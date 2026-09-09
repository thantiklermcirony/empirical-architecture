"""Price-based scenarios, NOT measured model quality or an AI market forecast.

Python standard library only. Run beside the output documents.
Prices checked against official provider pages on 2026-09-09.
All output tokens include billed reasoning/thinking, where applicable.
"""
from pathlib import Path
import json

PRICES = [
 {'id':'astra','model':'GPT-6 Astra','input':10.0,'cached_input':1.0,'output':50.0,'url':'https://developers.openai.com/api/docs/models/gpt-6-astra'},
 {'id':'sol','model':'GPT-5.6 Sol','input':4.0,'cached_input':0.4,'output':20.0,'url':'https://developers.openai.com/api/docs/models/gpt-5.6-sol'},
 {'id':'terra','model':'GPT-5.6 Terra','input':2.0,'cached_input':0.2,'output':12.0,'url':'https://developers.openai.com/api/docs/models/gpt-5.6-terra'},
 {'id':'luna','model':'GPT-5.6 Luna','input':0.2,'cached_input':0.02,'output':1.2,'url':'https://developers.openai.com/api/docs/models/gpt-5.6-luna'},
 {'id':'opus','model':'Claude Opus 5','input':5.0,'cached_input':0.5,'output':25.0,'url':'https://claude.com/pricing'},
 {'id':'sonnet','model':'Claude Sonnet 5','input':2.0,'cached_input':0.2,'output':10.0,'url':'https://claude.com/pricing'},
 {'id':'haiku','model':'Claude Haiku 4.5','input':1.0,'cached_input':0.1,'output':5.0,'url':'https://claude.com/pricing'},
 {'id':'flashlite','model':'Gemini 3.1 Flash-Lite','input':0.25,'cached_input':0.025,'output':1.5,'url':'https://ai.google.dev/gemini-api/docs/pricing'},
]

def token_cost(price, input_tokens=6000, output_tokens=1000, cache_fraction=0, discount=1):
    assert 0 <= cache_fraction <= 1 and discount > 0
    inp = price['input']*(1-cache_fraction)+price['cached_input']*cache_fraction
    return discount*(input_tokens*inp+output_tokens*price['output'])/1_000_000

def main():
    by_id={p['id']:p for p in PRICES}
    cheap=by_id['luna']
    scenarios=[
      {'id':'lean','name':'One proposal; inexpensive local evidence','attempts':1.0,'overhead':0.0002},
      {'id':'central','name':'1.5 proposals; $0.001 operational overhead','attempts':1.5,'overhead':0.001},
      {'id':'costly','name':'Three proposals; $0.010 operational overhead','attempts':3.0,'overhead':0.010},
    ]
    comparisons=[]
    for scenario in scenarios:
      candidate=scenario['attempts']*token_cost(cheap)+scenario['overhead']
      scenario['cost_per_request']=candidate
      for baseline in PRICES:
        base=token_cost(baseline)
        comparisons.append({'scenario':scenario['id'],'baseline':baseline['model'],
          'baseline_token_cost':base,'candidate_cost':candidate,'raw_cost_ratio':base/candidate,
          'raw_saving_fraction':1-candidate/base,'million_request_savings':1_000_000*(base-candidate),
          'quality_adjusted_ratio_if_baseline_q_095_candidate_q_090':(base/.95)/(candidate/.90),
          'quality_break_even_candidate_q_if_baseline_q_095':.95*candidate/base})
    central=scenarios[1]['cost_per_request']
    assert abs(central-.0046)<1e-12
    assert abs(token_cost(by_id['sol'])-.044)<1e-12
    assert abs(token_cost(by_id['sonnet'])-.022)<1e-12
    cache=[]
    for f in [0,.5,.9]:
      candidate=1.5*token_cost(cheap,cache_fraction=f)+.001
      for key in ['sol','sonnet','astra']:
        base=token_cost(by_id[key],cache_fraction=f)
        cache.append({'cache_fraction':f,'baseline':by_id[key]['model'],'baseline_cost':base,'candidate_cost':candidate,'raw_ratio':base/candidate})
    frontier_verifier=[]
    for key in ['sol','sonnet','astra']:
      base=token_cost(by_id[key])
      cost=central+base
      frontier_verifier.append({'baseline':by_id[key]['model'],'candidate_plus_one_equal_size_baseline_model_verification':cost,'raw_ratio':base/cost})
    adoption=[]
    for eligible,adopt,saving in [(0.1,.25,.8),(.3,.5,.9),(.6,.75,.9)]:
      reduction=eligible*adopt*saving
      adoption.append({'eligible_share':eligible,'adoption_within_eligible':adopt,'saving_on_adopted_work':saving,
                       'fixed_volume_spend_reduction':reduction,'demand_growth_factor_restoring_spend':1/(1-reduction)})
    result={'date':'2026-09-09','currency':'USD','price_unit':'per million tokens',
      'status':'Published prices plus assumed workload and performance; no generative benchmark run.',
      'workload':{'input_tokens_per_attempt':6000,'billed_output_tokens_per_attempt':1000,'baseline_attempts':1,
                  'same_data_access_required':True,'same_number_of_tokens_is_not_same_text_across_tokenizers':True,
                  'base_case_caching':False,'base_case_batching':False,'baseline_non_model_overhead':0,
                  'candidate_overhead_note':'Incremental operational cost assumption; not measured. Fixed development, maintenance and human review are separate.'},
      'prices':PRICES,'scenarios':scenarios,'comparisons':comparisons,'cache_sensitivity':cache,
      'large_model_verification':frontier_verifier,'market_arithmetic_scenarios':adoption}
    out=Path(__file__).resolve().parent
    (out/'AI_Economics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# The AI economics: what the numbers permit','',
      '9 September 2026. This is a reproducible price-and-workload analysis. Prices are observed; token budgets, attempts, overhead and performance are explicit scenarios. It does not measure the proposed architecture’s quality or predict company valuations.','',
      '**Result:** there is substantial economic room to investigate. In the central scenario, costs are about 4.8× lower than Sonnet 5, 9.6× lower than GPT-5.6 Sol and 23.9× lower than GPT-6 Astra at equal useful performance. The architecture has not yet demonstrated that equality. Existing inexpensive models are already cheaper than this proposed pipeline. Its breakthrough would have to be enabling sufficiently strong performance, reliability or discovery with those inexpensive proposers.','',
      '## Published prices','', '| Model | Input / million | Cached input / million | Output / million |', '|---|---:|---:|---:|']
    for p in PRICES: lines.append(f"| [{p['model']}]({p['url']}) | ${p['input']:g} | ${p['cached_input']:g} | ${p['output']:g} |")
    lines += ['', 'Standard paid text rates, USD, short contexts. Output budgets include billed reasoning/thinking tokens. Tool fees, taxes, regional uplifts, cache writes/storage and contracted discounts are not included in these rates. Sol pricing is listed as promotional at the check date. Tokenizers differ, so an actual cross-provider benchmark must use observed billed usage for the same tasks.', '',
      '## One explicit workload','',
      'Assume each model attempt consumes 6,000 input tokens and 1,000 billed output tokens. Both systems receive the same evidence. The baseline makes one attempt. The central candidate uses Luna pricing, averages 1.5 attempts including rejected proposals, and adds $0.001 per incoming request for incremental retrieval, verification and orchestration. That overhead is an assumption for sensitivity analysis, not an observed measurement. A 1.5-attempt mean does not imply independent errors or guarantee eventual success.', '',
      '`model cost = (input tokens × input price + billed output tokens × output price) / 1,000,000`', '',
      '`candidate cost = mean attempts × proposer cost + operational overhead`', '',
      'For Luna: one attempt is $0.0024; the central pipeline is 1.5 × $0.0024 + $0.001 = **$0.0046 per request**, or **$4,600 per million requests**, before fixed engineering and maintenance.','',
      '| Comparator | Token cost / million requests | Candidate / million | Raw reduction | Ratio |', '|---|---:|---:|---:|---:|']
    for c in [x for x in comparisons if x['scenario']=='central']:
      lines.append(f"| {c['baseline']} | ${c['baseline_token_cost']*1e6:,.0f} | ${c['candidate_cost']*1e6:,.0f} | {c['raw_saving_fraction']:.1%} | {c['raw_cost_ratio']:.2f}× |")
    lines += ['', 'Negative reduction means the proposed pipeline costs more. These are price-only comparisons under a fixed workload; they are not demonstrated replacements or claims of equal model capability.', '',
      '## Useful correct results are the denominator','',
      'Let q be the fraction of incoming tasks that end in a useful, independently correct completion. It includes abstentions and all failed attempts; equivalently, coverage × conditional correctness. Let C include the mean cost of every attempt and operation. Then cost per useful correct completion is C/q. A certificate that faithfully reports a false source is not an independently correct result.', '',
      '`quality-adjusted cost ratio = (baseline cost / baseline q) / (candidate cost / candidate q)`','',
      'If baseline q = 0.95 and candidate q = 0.90, the central ratios become approximately **4.53× versus Sonnet, 9.06× versus Sol and 22.65× versus Astra**. Those q values are illustrative, not measured model scores. A product must also meet a prespecified minimum quality, coverage and latency; a low cost per success does not make a poor service acceptable.', '',
      'The purely financial break-even condition is `candidate q > baseline q × candidate cost / baseline cost`. The benchmark must separately enforce practical quality and coverage requirements. Publishing only this financial threshold would hide whether the system is usable.', '',
      '## What can remove the advantage','',
      '| Candidate scenario | Cost / request | Ratio vs Sonnet | Ratio vs Sol | Ratio vs Astra |', '|---|---:|---:|---:|---:|']
    for s in scenarios:
      ratios=[token_cost(by_id[k])/s['cost_per_request'] for k in ['sonnet','sol','astra']]
      lines.append(f"| {s['name']} | ${s['cost_per_request']:.4f} | {ratios[0]:.2f}× | {ratios[1]:.2f}× | {ratios[2]:.2f}× |")
    lines += ['', 'One paid web search at Anthropic’s published $10 per 1,000 searches is already $0.01 before the model tokens needed to process it. This makes local/versioned evidence and reusable calculations economically significant. The exact search cost belongs in both systems when both need it. [Anthropic tool pricing](https://claude.com/pricing).','',
      'Using one additional full-size comparator-model call to verify every request makes the central pipeline more expensive than that single comparator call. Shorter or selectively escalated verification can change the arithmetic; it must be measured. The architectural thesis requires reliable inexpensive verification where claimed, not an uncounted second frontier model.', '',
      'With a steady-state 90% input-cache hit rate for both systems, the central ratios are about 3.91× versus Sonnet, 7.82× versus Sol and 19.54× versus Astra. This calculation excludes cache write/storage costs and assumes both evidence layouts permit those hits. The JSON contains the full sensitivity table. Batch pricing and ordinary model routing are additional competitors, not programme-specific innovations.', '',
      'Fixed costs matter. If a new pipeline saves Δ dollars per request but adds M dollars in monthly maintenance, it needs more than M/Δ requests per month before that maintenance is covered. For the central Sol comparison, Δ = $0.0394. An illustrative extra $2,000/month therefore requires about 50,762 requests/month just to cover maintenance; a separate development cost still needs repayment. No such maintenance or development budget has been estimated for this project.', '',
      '## Why cheap-model savings alone do not establish the thesis','',
      'Luna and Flash-Lite already exist at low prices. Conventional retrieval, constrained output, tool use, routing and caching are available to competitors. The decisive comparison is whether the proposed separation of proposal, evidence, state and action makes useful high-quality tasks attainable at lower total cost than strong systems using those same ingredients. It must also beat or improve a plain inexpensive model where that model already suffices.', '',
      'A fair factorial benchmark crosses architecture (ordinary tool/RAG system versus the proposed system), proposer price/capability tier and workload difficulty. It separately removes state memory, evidence checks and controlled rendering. Freeze unknowns, conflicting sources, version changes and model-selection data before evaluating. Report useful coverage, independent correctness, semantic binding, latency, total spend and human correction effort. An output constrained to a narrower task must be compared with a baseline asked to perform that same task.', '',
      '## What could happen to the wider market','',
      'The possible disruption is architectural: capable generators become more substitutable while value moves into evidence, state, tools, integration and experimentally reliable decisions. That could affect expensive inference workloads even if frontier training and difficult reasoning remain valuable. Existing providers can also adopt this architecture, and lower costs can expand demand.', '',
      'For a defined spend pool at fixed task volume, let f be the share of spending eligible for the architecture, a the fraction of that share that adopts it, and s the savings on migrated work. The direct spend reduction is f × a × s. The following are sensitivity scenarios, not estimates of those market quantities.','',
      '| Eligible spending | Adoption within eligible | Saving on migrated work | Whole-pool spend reduction | Demand multiplier restoring original spend |','|---:|---:|---:|---:|---:|']
    for x in adoption: lines.append(f"| {x['eligible_share']:.0%} | {x['adoption_within_eligible']:.0%} | {x['saving_on_adopted_work']:.0%} | {x['fixed_volume_spend_reduction']:.1%} | {x['demand_growth_factor_restoring_spend']:.2f}× |")
    lines += ['', 'This is why a 90% saving on one workload does not imply a 90% reduction in the AI market. Revenue, profit, capital investment and company valuation require further assumptions. The present evidence supplies no defensible numerical forecast for them.', '',
      '**Research judgment:** a reproducible 5–10× reduction on a useful task class at genuinely comparable quality would be a strong launch result. A 20× or larger result against an expensive tier could be important, but must survive comparison with already-cheap alternatives. These are targets made plausible by price differences, not achieved results. The next experiment is to establish the quality, useful coverage and operational cost that determine which part of this room can actually be captured.', '',
      'Reproduce with `python ai_economics.py`. All prices, scenarios, comparisons and sensitivity calculations are in `AI_Economics.json`. No paid API calls were made for this analysis.','']
    (out/'AI_Economics.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'central_cost':central,'selected_ratios':{k:token_cost(by_id[k])/central for k in ['sonnet','sol','astra']},'cache_90':[x for x in cache if x['cache_fraction']==.9]},indent=2))

if __name__=='__main__': main()
