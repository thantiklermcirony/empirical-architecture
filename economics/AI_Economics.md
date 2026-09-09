# The AI economics: what the numbers permit

9 September 2026. This is a reproducible price-and-workload analysis. Prices are observed; token budgets, attempts, overhead and performance are explicit scenarios. It does not measure the proposed architecture’s quality or predict company valuations.

**Result:** there is substantial economic room to investigate. In the central scenario, costs are about 4.8× lower than Sonnet 5, 9.6× lower than GPT-5.6 Sol and 23.9× lower than GPT-6 Astra at equal useful performance. The architecture has not yet demonstrated that equality. Existing inexpensive models are already cheaper than this proposed pipeline. Its breakthrough would have to be enabling sufficiently strong performance, reliability or discovery with those inexpensive proposers.

## Published prices

| Model | Input / million | Cached input / million | Output / million |
|---|---:|---:|---:|
| [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) | $10 | $1 | $50 |
| [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) | $4 | $0.4 | $20 |
| [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) | $2 | $0.2 | $12 |
| [GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) | $0.2 | $0.02 | $1.2 |
| [Claude Opus 5](https://claude.com/pricing) | $5 | $0.5 | $25 |
| [Claude Sonnet 5](https://claude.com/pricing) | $2 | $0.2 | $10 |
| [Claude Haiku 4.5](https://claude.com/pricing) | $1 | $0.1 | $5 |
| [Gemini 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/pricing) | $0.25 | $0.025 | $1.5 |

Standard paid text rates, USD, short contexts. Output budgets include billed reasoning/thinking tokens. Tool fees, taxes, regional uplifts, cache writes/storage and contracted discounts are not included in these rates. Sol pricing is listed as promotional at the check date. Tokenizers differ, so an actual cross-provider benchmark must use observed billed usage for the same tasks.

## One explicit workload

Assume each model attempt consumes 6,000 input tokens and 1,000 billed output tokens. Both systems receive the same evidence. The baseline makes one attempt. The central candidate uses Luna pricing, averages 1.5 attempts including rejected proposals, and adds $0.001 per incoming request for incremental retrieval, verification and orchestration. That overhead is an assumption for sensitivity analysis, not an observed measurement. A 1.5-attempt mean does not imply independent errors or guarantee eventual success.

`model cost = (input tokens × input price + billed output tokens × output price) / 1,000,000`

`candidate cost = mean attempts × proposer cost + operational overhead`

For Luna: one attempt is $0.0024; the central pipeline is 1.5 × $0.0024 + $0.001 = **$0.0046 per request**, or **$4,600 per million requests**, before fixed engineering and maintenance.

| Comparator | Token cost / million requests | Candidate / million | Raw reduction | Ratio |
|---|---:|---:|---:|---:|
| GPT-6 Astra | $110,000 | $4,600 | 95.8% | 23.91× |
| GPT-5.6 Sol | $44,000 | $4,600 | 89.5% | 9.57× |
| GPT-5.6 Terra | $24,000 | $4,600 | 80.8% | 5.22× |
| GPT-5.6 Luna | $2,400 | $4,600 | -91.7% | 0.52× |
| Claude Opus 5 | $55,000 | $4,600 | 91.6% | 11.96× |
| Claude Sonnet 5 | $22,000 | $4,600 | 79.1% | 4.78× |
| Claude Haiku 4.5 | $11,000 | $4,600 | 58.2% | 2.39× |
| Gemini 3.1 Flash-Lite | $3,000 | $4,600 | -53.3% | 0.65× |

Negative reduction means the proposed pipeline costs more. These are price-only comparisons under a fixed workload; they are not demonstrated replacements or claims of equal model capability.

## Useful correct results are the denominator

Let q be the fraction of incoming tasks that end in a useful, independently correct completion. It includes abstentions and all failed attempts; equivalently, coverage × conditional correctness. Let C include the mean cost of every attempt and operation. Then cost per useful correct completion is C/q. A certificate that faithfully reports a false source is not an independently correct result.

`quality-adjusted cost ratio = (baseline cost / baseline q) / (candidate cost / candidate q)`

If baseline q = 0.95 and candidate q = 0.90, the central ratios become approximately **4.53× versus Sonnet, 9.06× versus Sol and 22.65× versus Astra**. Those q values are illustrative, not measured model scores. A product must also meet a prespecified minimum quality, coverage and latency; a low cost per success does not make a poor service acceptable.

The purely financial break-even condition is `candidate q > baseline q × candidate cost / baseline cost`. The benchmark must separately enforce practical quality and coverage requirements. Publishing only this financial threshold would hide whether the system is usable.

## What can remove the advantage

| Candidate scenario | Cost / request | Ratio vs Sonnet | Ratio vs Sol | Ratio vs Astra |
|---|---:|---:|---:|---:|
| One proposal; inexpensive local evidence | $0.0026 | 8.46× | 16.92× | 42.31× |
| 1.5 proposals; $0.001 operational overhead | $0.0046 | 4.78× | 9.57× | 23.91× |
| Three proposals; $0.010 operational overhead | $0.0172 | 1.28× | 2.56× | 6.40× |

One paid web search at Anthropic’s published $10 per 1,000 searches is already $0.01 before the model tokens needed to process it. This makes local/versioned evidence and reusable calculations economically significant. The exact search cost belongs in both systems when both need it. [Anthropic tool pricing](https://claude.com/pricing).

Using one additional full-size comparator-model call to verify every request makes the central pipeline more expensive than that single comparator call. Shorter or selectively escalated verification can change the arithmetic; it must be measured. The architectural thesis requires reliable inexpensive verification where claimed, not an uncounted second frontier model.

With a steady-state 90% input-cache hit rate for both systems, the central ratios are about 3.91× versus Sonnet, 7.82× versus Sol and 19.54× versus Astra. This calculation excludes cache write/storage costs and assumes both evidence layouts permit those hits. The JSON contains the full sensitivity table. Batch pricing and ordinary model routing are additional competitors, not programme-specific innovations.

Fixed costs matter. If a new pipeline saves Δ dollars per request but adds M dollars in monthly maintenance, it needs more than M/Δ requests per month before that maintenance is covered. For the central Sol comparison, Δ = $0.0394. An illustrative extra $2,000/month therefore requires about 50,762 requests/month just to cover maintenance; a separate development cost still needs repayment. No such maintenance or development budget has been estimated for this project.

## Why cheap-model savings alone do not establish the thesis

Luna and Flash-Lite already exist at low prices. Conventional retrieval, constrained output, tool use, routing and caching are available to competitors. The decisive comparison is whether the proposed separation of proposal, evidence, state and action makes useful high-quality tasks attainable at lower total cost than strong systems using those same ingredients. It must also beat or improve a plain inexpensive model where that model already suffices.

A fair factorial benchmark crosses architecture (ordinary tool/RAG system versus the proposed system), proposer price/capability tier and workload difficulty. It separately removes state memory, evidence checks and controlled rendering. Freeze unknowns, conflicting sources, version changes and model-selection data before evaluating. Report useful coverage, independent correctness, semantic binding, latency, total spend and human correction effort. An output constrained to a narrower task must be compared with a baseline asked to perform that same task.

## What could happen to the wider market

The possible disruption is architectural: capable generators become more substitutable while value moves into evidence, state, tools, integration and experimentally reliable decisions. That could affect expensive inference workloads even if frontier training and difficult reasoning remain valuable. Existing providers can also adopt this architecture, and lower costs can expand demand.

For a defined spend pool at fixed task volume, let f be the share of spending eligible for the architecture, a the fraction of that share that adopts it, and s the savings on migrated work. The direct spend reduction is f × a × s. The following are sensitivity scenarios, not estimates of those market quantities.

| Eligible spending | Adoption within eligible | Saving on migrated work | Whole-pool spend reduction | Demand multiplier restoring original spend |
|---:|---:|---:|---:|---:|
| 10% | 25% | 80% | 2.0% | 1.02× |
| 30% | 50% | 90% | 13.5% | 1.16× |
| 60% | 75% | 90% | 40.5% | 1.68× |

This is why a 90% saving on one workload does not imply a 90% reduction in the AI market. Revenue, profit, capital investment and company valuation require further assumptions. The present evidence supplies no defensible numerical forecast for them.

**Research judgment:** a reproducible 5–10× reduction on a useful task class at genuinely comparable quality would be a strong launch result. A 20× or larger result against an expensive tier could be important, but must survive comparison with already-cheap alternatives. These are targets made plausible by price differences, not achieved results. The next experiment is to establish the quality, useful coverage and operational cost that determine which part of this room can actually be captured.

Reproduce with `python ai_economics.py`. All prices, scenarios, comparisons and sensitivity calculations are in `AI_Economics.json`. No paid API calls were made for this analysis.
