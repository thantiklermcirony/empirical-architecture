"""Finite action cover, admissibility, diagnostic risk, query-bound result witness."""
from fractions import Fraction as F
from itertools import combinations
from math import comb
from copy import deepcopy
from certificate_support import check_package,object_sha,admitted,emit

# Trusted local rule definition: a witness may not choose or erase these obligations.
REQUIRED_WITNESS_PREMISES=frozenset({'sets_calibrated','library_complete'})

def minimal_cover(acceptable):
 universe=set(acceptable)
 actions=sorted(set().union(*acceptable.values()))
 for n in range(1,len(actions)+1):
  for chosen in combinations(actions,n):
   if all(acceptable[s]&set(chosen) for s in universe):return chosen
 return None

def bayes_risk(n,p=F(3,4),q=F(1,4)):
 # Binomial count is sufficient for the declared iid Bernoulli hypotheses.
 # 1/2 sum_k min(P0(k),P1(k)) includes optimal random tie handling.
 return sum((min(F(comb(n,k))*p**k*(1-p)**(n-k),
                  F(comb(n,k))*q**k*(1-q)**(n-k)) for k in range(n+1)),F(0))/2

def finite_descent(partition,operation):
 for cell in partition:
  domain=[s in operation for s in cell]
  if len(set(domain))>1:return False,'domain_not_saturated'
  if all(domain):
   labels=[next(i for i,C in enumerate(partition) if operation[s] in C) for s in cell]
   if len(set(labels))>1:return False,'value_not_constant_on_fibre'
 return True,'descends'

def check_witness(query,source,witness,expected_source_hash,expected_model_hash,premises):
 # This example authenticates no external publisher: expected hashes are trusted inputs.
 if object_sha(source)!=expected_source_hash:return False,'source'
 if witness['query_sha256']!=object_sha(query):return False,'query'
 if witness['source_sha256']!=expected_source_hash:return False,'binding'
 if witness['model_sha256']!=expected_model_hash:return False,'model'
 supplied=witness.get('depends_on')
 if not isinstance(supplied,list) or set(supplied)!=REQUIRED_WITNESS_PREMISES:return False,'required_dependencies'
 if len(supplied)!=len(REQUIRED_WITNESS_PREMISES):return False,'required_dependencies'
 if not all(premises.get(x) is True for x in REQUIRED_WITNESS_PREMISES):return False,'premise'
 if query['operation']!='minimum_action_cover' or query['units']!='code_cells':return False,'type'
 value=len(minimal_cover({s:set(v) for s,v in source.items()}))
 if value!=witness['value']:return False,'recomputation'
 return True,'admitted'

def run():
 p=check_package('action_evidence',__file__)
 sets={'s1':{'a','b'},'s2':{'b','c'},'s3':{'a','c'}}
 pairwise={f'{i}/{j}':sorted(sets[i]&sets[j]) for i,j in combinations(sets,2)}
 assert all(pairwise.values()) and not set.intersection(*sets.values())
 cover=minimal_cover(sets); assert len(cover)==2
 assert len(minimal_cover({s:A|{'abstain'} for s,A in sets.items()}))==1
 domain_case=finite_descent([{'h0','h1'},{'h2'}],{'h0':'h2'})
 assert domain_case==(False,'domain_not_saturated')
 assert finite_descent([{'h0','h1'},{'h2'}],{'h0':'h2','h1':'h2'})[0]
 risks={str(n):str(bayes_risk(n)) for n in range(9)}
 assert all(bayes_risk(n)>F(1,10) for n in range(7))
 assert bayes_risk(7)<=F(1,10)
 assert bayes_risk(4)==F(5,32) and bayes_risk(6)==F(53,512)
 assert bayes_risk(7)==F(289,4096)
 # Times start after the first sample interval: no free sample at t=0.
 duration=F(7,2); fast_duration=F(7,4)
 assert duration>2 and fast_duration<2
 query={'operation':'minimum_action_cover','units':'code_cells','scope':'three declared states and deterministic library'}
 source={s:sorted(v) for s,v in sets.items()}
 model={'threshold':'already reflected in declared action sets','randomized_actions':False}
 witness={'query_sha256':object_sha(query),'source_sha256':object_sha(source),
          'model_sha256':object_sha(model),'depends_on':['sets_calibrated','library_complete'],'value':2}
 premises={'sets_calibrated':True,'library_complete':True}
 checker=lambda q,s,w,pr:check_witness(q,s,w,object_sha(source),object_sha(model),pr)
 assert checker(query,source,witness,premises)[0]
 mutations={}
 q=deepcopy(query);q['units']='patients'; mutations['query_units']=checker(q,source,witness,premises)
 s=deepcopy(source);s['s1']=['c'];mutations['source_data']=checker(query,s,witness,premises)
 w=deepcopy(witness);w['value']=1;mutations['claimed_result']=checker(query,source,w,premises)
 w=deepcopy(witness);w['model_sha256']='0'*64;mutations['model_binding']=checker(query,source,w,premises)
 pr=deepcopy(premises);pr['sets_calibrated']=False;mutations['missing_premise']=checker(query,source,witness,pr)
 w=deepcopy(witness);w['depends_on']=[]
 mutations['erased_required_dependencies']=checker(query,source,w,{'sets_calibrated':False,'library_complete':False})
 w=deepcopy(witness);w['depends_on']=['sets_calibrated']
 mutations['omitted_library_dependency']=checker(query,source,w,premises)
 mutations['absent_trusted_premise']=checker(query,source,witness,{'sets_calibrated':True})
 assert all(not ok for ok,why in mutations.values())
 deps=['ACT-02.P1','ACT-02.P2','ACT-02.P3','ACT-02.P4','ACT-03.P1','ACT-03.P2','ACT-03.P3']
 emit('action_evidence',p,__file__,{'status':'established_in_scope','check_count':21,
  'cover':{'sets':source,'pairwise_intersections':pairwise,'triple_intersection':[],
    'minimum_cells':2,'cover_actions':list(cover),'adding_common_abstain_cells':1},
  'partial_action':{'value':domain_case[0],'reason':domain_case[1]},
  'diagnosis':{'risk_by_sample_count':risks,'target_error':'1/10','first_sufficient_n':7,
    'sample_interval':'1/2','duration':str(duration),'resource_horizon_upper_bound':'2',
    'conclusion':'No fixed sample-count member meets both constraints; even four samples have minimum error 5/32.',
    'fast_sample_interval':'1/4','fast_duration':str(fast_duration),
    'fast_status':'not excluded by resource bound; feasible diagnostic and rescue not established'},
  'evidence':{'positive_witness':witness,'rejected_mutations':mutations,
    'authentication':'Trusted local expected hashes only; replacing both trusted inputs and artifacts is outside this check'},
  'premise_contrasts':[{'removed':None,'exclusion':admitted(p,deps)}]+[
    {'removed':k,'exclusion':admitted(p,deps,[k]),'finite_cover':'established_in_scope'} for k in deps],
  'unproved_by_code':['Physical validity of the diagnostic likelihood, experimental unit and nondisturbance',
   'Resource duration upper bound imports resources package and supplied comparison proof',
   'No result for arbitrary sequential stopping rules, alternative diagnostics, or actual biological failure probability']})
if __name__=='__main__':run()
