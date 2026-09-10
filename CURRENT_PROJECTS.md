# Current projects

**[Open the live project board →](https://empirical-observatory.madmanmuzza.chatgpt.site/projects)** · [Enter the Observatory](https://empirical-observatory.madmanmuzza.chatgpt.site)

| Project | Current status | Start here |
| --- | --- | --- |
| Ray Serve / controller recovery | Validated scoped candidate; 60/60 correct HTTP probes after replacement; 30 Linux tests pass; not submitted | [Results and patch](https://github.com/thantiklermcirony/empirical-architecture/blob/main/research/ray-campaign/Ray_Contribution_Report.md), [live feature](https://empirical-observatory.madmanmuzza.chatgpt.site/projects#ray) |
| NeuroGym / observable decisions | Cue correction submitted; 132 full-suite tests pass on one Windows/Python runtime; 240-trial preservation check; awaiting review | [PR #295](https://github.com/neurogym/neurogym/pull/295), [results](https://github.com/thantiklermcirony/empirical-observatory/blob/main/public/research/NeuroGym_Contribution_Report.md), [live feature](https://empirical-observatory.madmanmuzza.chatgpt.site/projects#neurogym) |
| Pertpy / biological prediction evaluation | First API submitted; 84 evaluator cases on two Python versions and a 4,553-cell demonstration; awaiting review | [PR #1098](https://github.com/scverse/pertpy/pull/1098), [results and reproduction](https://github.com/thantiklermcirony/empirical-observatory/blob/main/public/research/Pertpy_Evaluation_Report.md), [live feature](https://empirical-observatory.madmanmuzza.chatgpt.site/projects#pertpy) |
| Graphiti memory correctness | Two tested fixes submitted; awaiting maintainer review | [History PR #1867](https://github.com/getzep/graphiti/pull/1867), [timestamp PR #1866](https://github.com/getzep/graphiti/pull/1866), [evidence](https://github.com/thantiklermcirony/empirical-observatory/blob/main/public/research/Graphiti.md) |
| TAO / adaptive control | Playable synthetic experiment; PI leads the published tracking comparison | [Enter the chamber](https://empirical-observatory.madmanmuzza.chatgpt.site/#tao), [methods](https://github.com/thantiklermcirony/empirical-observatory/blob/main/research/Methods.md) |
| Quantum measurement | Playable simulation using established quantum mechanics | [Enter the lab](https://empirical-observatory.madmanmuzza.chatgpt.site/#quantum) |
| Earth / AI / Genome | Real Oslo feed, executed memory diagnostic, locally configured Atlas adapter | [Explore expeditions](https://empirical-observatory.madmanmuzza.chatgpt.site/#expeditions) |
| IDA / StateAtlas | Developing experimental instrument and research prototype | [Source and research](https://github.com/thantiklermcirony/ida-stateatlas) |

The browser experiments can run without an API key. Hardware and AlphaGenome require their own local setup/access. None of these demonstrations establishes biological universality, consciousness measurement or general AI superiority.

## The NeuroGym contribution

The same observation-driven policy responds prematurely four times on the original task and zero times after correction in each of four controlled rollouts. Both versions still award reward 1: this fixes the missing signal, not the existing early-action reward rules. Twenty of the 32 new cases fail on the original; all pass with the patch. No trained-model advantage is claimed. Maintainers will decide the observation compatibility policy.

## Next three investigations

The [new focused scan](https://github.com/thantiklermcirony/empirical-observatory/blob/main/public/research/Next_Big_Three.md) checks current ownership, existing attempts, resources, independent tests and public demonstrations. Ray now has a tested recovery candidate. Dask and F Prime remain follow-on investigations with their existing contribution gates. We prioritize a useful upstream contribution over duplicating someone else's open patch.

## The Pertpy contribution

The evaluator aligns genes, separates training and held-out cells, compares predictions with training-only control and additive baselines, and keeps missing or undefined results visible. In eight held-out Norman gene combinations, the additive baseline had lower mean squared error in seven; one apparently good correlation still hid 3.06 times the no-change baseline’s error.

These are conventional baseline results in one K562 dataset. IDA has not yet been implemented or scored. This first API does not close all of Pertpy issue #1035: nearest-neighbour baselines, log-fold-change scoring and DEG discovery remain outside the submitted scope. [Evidence and limitations](https://github.com/thantiklermcirony/empirical-observatory/blob/main/public/research/Pertpy_Evaluation_Report.md).

The code is committed and [PR #1098](https://github.com/scverse/pertpy/pull/1098) is public. Acceptance depends on upstream review. The next scientific step is to specify an IDA predictor and a fresh held-out comparison before using this evaluator to claim an advantage.

## The Graphiti contribution

The original code could reuse an expired fact when the same fact became true again. A separate read/resave defect could change answers at exact time boundaries. The two patches address these distinct correctness failures.

There are 48 new regression cases. Each published branch passed a separate unit gate; those larger totals include existing Graphiti tests. The real-database evidence and unfinished cases are linked above. Our original investigation does not establish that release-event issue #1841 is resolved.

Status recorded 10 September 2026. Use the upstream pull requests for current checks, reviews and acceptance. A CLA acknowledgment is not maintainer approval.

## A useful next contribution

Reproduce a failure, challenge an assumption, improve a baseline, or help close a documented integration gap. [Contribution guide](CONTRIBUTING.md) · [Audited opportunity scan](https://github.com/thantiklermcirony/empirical-observatory/tree/main/research/contribution-scan)
