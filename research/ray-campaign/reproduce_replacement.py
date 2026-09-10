"""Real Ray actor/subscriber replacement diagnostic, with no simulated Ray APIs."""
import argparse
import asyncio
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import time
import uuid

os.environ.setdefault('RAY_USAGE_STATS_ENABLED', '0')
import ray
import ray.serve._private.long_poll as long_poll


@ray.remote(num_cpus=0)
class Host:
    def __init__(self, epoch):
        self.host = long_poll.LongPollHost(listen_for_change_request_timeout_s=(0.2, 0.3))
        self.host.notify_changed({'route': epoch})
        # A deliberate version collision is legal: each host initializes independently.
        self.host.snapshot_ids['route'] = 7

    async def listen_for_change(self, ids):
        return await self.host.listen_for_change(ids)

    def identity(self):
        return ray.get_runtime_context().get_actor_id()


async def run(args):
    namespace = 'empirical-ray-' + uuid.uuid4().hex
    name = 'controller'
    old = Host.options(name=name, namespace=namespace).remote('epoch-A')
    old_id = await old.identity.remote()
    callbacks = []
    kwargs = {}
    if args.reconnect:
        kwargs['host_actor_resolver'] = lambda: ray.get_actor(name, namespace=namespace)
    client = long_poll.LongPollClient(old, {'route': callbacks.append},
        call_in_event_loop=asyncio.get_running_loop(), client_id='replacement-diagnostic', **kwargs)
    started = time.monotonic()
    while callbacks != ['epoch-A'] and time.monotonic() - started < 10:
        await asyncio.sleep(0.01)
    assert callbacks == ['epoch-A'], callbacks
    ray.kill(old, no_restart=True)
    await asyncio.sleep(1)
    new = Host.options(name=name, namespace=namespace).remote('epoch-B')
    new_id = await new.identity.remote()
    assert new_id != old_id
    started = time.monotonic()
    while callbacks[-1] != 'epoch-B' and time.monotonic() - started < args.timeout:
        await asyncio.sleep(0.02)
    observed = callbacks[-1] == 'epoch-B'
    result = {
        'python': platform.python_version(), 'platform': platform.platform(),
        'ray_version': ray.__version__, 'ray_native_commit': ray.__commit__,
        'long_poll_sha256': hashlib.sha256(Path(long_poll.__file__).read_bytes()).hexdigest(),
        'resolver_enabled': args.reconnect, 'host_ids_differ': new_id != old_id,
        'old_actor_id': old_id, 'new_actor_id': new_id,
        'host_snapshot_ids': [7, 7], 'observed_payloads': callbacks,
        'received_replacement': observed, 'client_running_before_stop': client.is_running,
        'elapsed_after_replacement_s': time.monotonic() - started,
        'limit': 'Real actor and LongPollClient path; this is not a HAProxy HTTP integration.',
    }
    client.stop()
    ray.kill(new, no_restart=True)
    await asyncio.sleep(0.1)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=5)
    parser.add_argument('--reconnect', action='store_true')
    args = parser.parse_args()
    ray.init(num_cpus=2, include_dashboard=False, _temp_dir=str(args.output.parent.resolve() / 'ray-tmp'))
    try:
        result = asyncio.run(run(args))
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
    finally:
        ray.shutdown()
