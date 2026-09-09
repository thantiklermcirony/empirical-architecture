# Evidence and state for AI

The programme investigates whether intelligence is better engineered by separating the generation of candidates from the evidence, state and authority needed to use them.

## The architectural claim

The proposer generates explanations, plans and candidate assertions. Evidence and explicit inference determine what is supported. Persistent state retains distinctions future tasks need. The experimental model can discover that its representation is inadequate. The action layer accounts for feasibility, time and authorization.

The existing epistemic-type-safety paper offers two engineering hypotheses: useful certification within a manageable trusted core, and earlier proposer-size saturation for a declared evidence-supported workload. It does not derive a numerical minimum parameter count or prove that larger models cease to help. [Paper](https://ssrn.com/abstract=7426838).

The larger programme adds state revision and scientific discovery. The system should propose a new state when an old summary loses predictive information, choose a test that distinguishes explanations, and track which conclusions remain applicable after the model changes.

## The first benchmark

Use a versioned factual/experimental task family with explicit entities, units, observations, unknowns and admissible operations. Freeze the evaluation set. Give every system equivalent evidence and tool access.

Compare a conventional retrieval/tool system, the same system with structured output and abstention, the proposed architecture, and its state/evidence/renderer ablations. Cross those systems with several proposer tiers. Include an inexpensive baseline; compare strong architectures, not an artificially weak model asked to memorize what another is allowed to retrieve.

Tasks should include source-version changes, entity ambiguity, conflicting observations, invalid composition assumptions, missing history, and a hypothesis that requires an additional experiment. Independent grading must assess external correctness and usefulness as well as source fidelity.

Report useful coverage, conditional correctness, unsupported assertions, state-dependent task failures, discovery performance, billed tokens, tool costs, latency, rejected attempts and human correction effort. Publish raw task outcomes and the rules that define a successful completion.

## The economic question

Current inexpensive proposers create considerable price headroom. Capturing it requires the proposed architecture to preserve sufficient quality on a useful task class. The relevant metric is total cost per useful correct result, including all attempts, retrieval, checks and maintenance. Model price, parameter count and market value are different quantities.

A separate reproducible economic analysis in the project redesign package quantifies price-based scenarios. Those are planning calculations; the reference code in this repository does not establish equivalent performance or realized savings.

## What this repository implements

The offline reference example accepts a tiny structured source-relative assertion when its fields match a bound query and evidence record. It rejects unsupported values, stale versions, changed record identity and unsupported extra interpretation. It does not run a generative model, solve source truth, perform general semantic binding or guarantee safety in a browser/agent environment.

The next software result is a real proposer adapter and a comparative evaluation, followed by a state-revising experimental loop. An integration should expose structured candidates to the checking layer rather than silently allowing generated prose to bypass the interface.
