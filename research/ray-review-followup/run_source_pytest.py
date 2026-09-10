"""Verify actually imported source/native identities before Linux pytest."""

import argparse
from pathlib import Path
import sys

from validation_support import BASE, HP, LP, manifest, sha, write_json

WHEEL_SHA = "59d62dcfdf70053b47875c4e354e04bcbfaab107e8f8365b03d1e8644f7f7a41"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--identity-output", required=True)
    parser.add_argument("--implementation", choices=["submitted", "candidate"], required=True)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    source = Path(args.source_root).resolve()
    output = Path(args.identity_output).resolve()
    value = manifest(Path(__file__).resolve().parent)
    wheel_record = (output.parent / "wheel.sha256").read_text(encoding="utf-8").split()
    assert wheel_record[0] == WHEEL_SHA, "Missing or incorrect verified wheel provenance"
    # Match the prior validated `python -c` launch from the checkout root. This
    # adds the repository root, never its unbuilt python/ray package directory.
    sys.path.insert(0, str(source))
    # Import native ray first, before pytest traverses the checkout's parents.
    import ray
    import ray._raylet
    import ray.serve._private.haproxy as haproxy
    import ray.serve._private.long_poll as long_poll
    import pytest

    record = {"native_commit": ray.__commit__, "verified_native_wheel_sha256": WHEEL_SHA,
              "native_extension_path": str(Path(ray._raylet.__file__).resolve()),
              "implementation": args.implementation, "imported_sources": {}}
    assert ray.__commit__ == BASE
    assert not ray.is_initialized(), "Tests must start disconnected from any Ray runtime"
    for relative, module in [(LP, long_poll), (HP, haproxy)]:
        actual = Path(module.__file__).resolve()
        expected = (source / relative).resolve()
        assert actual == expected, (str(actual), str(expected))
        actual_hash = sha(actual)
        phase = args.implementation if relative == LP else "candidate"
        assert actual_hash == value["files"][relative][f"{phase}_sha256"]
        record["imported_sources"][relative] = {"path": str(actual), "sha256": actual_hash}
    assert haproxy.LongPollClient is long_poll.LongPollClient
    write_json(output, record)
    options = args.pytest_args
    if options and options[0] == "--":
        options = options[1:]
    record["pytest_arguments"] = options
    try:
        code = int(pytest.main(options))
        record["pytest_exit_code"] = code
    finally:
        ray.shutdown()
        record["ray_initialized_after_shutdown"] = ray.is_initialized()
        write_json(output, record)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
