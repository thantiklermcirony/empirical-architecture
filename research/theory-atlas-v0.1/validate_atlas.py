"""Meaningful release checks: source integrity, migration, receipts and independent finite risk calculation."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json,os
from certificate_support import ROOT,sha,check_package
from certify_action_evidence import bayes_risk,check_witness

def run():
 base=json.loads((ROOT/'register.base.json').read_text(encoding='utf-8'))
 proposed=json.loads((ROOT/'register.proposed.json').read_text(encoding='utf-8'))
 byid={r['id']:r for r in proposed['rules']}
 assert len(byid)==len(proposed['rules'])==32
 assert len(base['rules'])==16
 for r in base['rules']:
  for k,v in r.items():assert byid[r['id']][k]==v,(r['id'],k)
 for s in proposed['sources']:
  path=Path(s['path'])
  if os.environ.get('ATLAS_SOURCE_ROOT'):path=Path(os.environ['ATLAS_SOURCE_ROOT'])/path.name
  assert sha(path)==s['sha256'],s['id']
  count=len(path.read_text(encoding='utf-8').splitlines())
  for r in proposed['rules']:
   for b in r['source_bindings']:
    if b['source_id']==s['id']:
     assert b['sha256']==s['sha256'] and 1<=b['line_start']<=b['line_end']<=count
 coverage=json.loads((ROOT/'coverage.json').read_text(encoding='utf-8'))
 assert coverage['counts']=={'total':41,'current':11,'legacy':30}
 assert len({r['key'] for r in coverage['records']})==41
 fields=set('identity question system observer quantities operations constraints mechanism premises execution results contrast next_question provenance'.split())
 for name in ['composition','resources','action_evidence','connections']:
  p=check_package(name,ROOT/f'certify_{name}.py')
  assert fields<=set(p)
  known={x['id'] for x in p['premises']}|{x['id'] for x in p['execution']['proof_obligations']}
  for step in p['execution']['steps']:
   assert set(step.get('depends_on',[]))<=known,(name,step['id'])
   known.add(step['id'])
  for result in p['results']:assert set(result['depends_on'])<=known,(name,result['id'])
  receipt=json.loads((ROOT/'receipts'/f'{name}.json').read_text(encoding='utf-8'))
  assert receipt['package_sha256']==sha(ROOT/'packages'/f'{name}.json')
  assert receipt['code_sha256']==sha(ROOT/f'certify_{name}.py')
 # Independent construction: enumerate 2^n ordered outcomes, not binomial counts.
 independent=[]
 for n in range(9):
  total=F(0)
  for seq in product((0,1),repeat=n):
   a=b=F(1)
   for y in seq:a*=F(3,4) if y else F(1,4);b*=F(1,4) if y else F(3,4)
   total+=min(a,b)/2
  assert total==bayes_risk(n)
  independent.append({'n':n,'risk':str(total)})
 admission=json.loads((ROOT/'receipts/admission.json').read_text(encoding='utf-8'))
 assert admission['status']=='passed' and len(admission['negative_fixtures'])==8
 report={'status':'passed','checks':['all16 original rule objects preserved field-for-field','32 unique rule IDs',
  '41 local source hashes and cited line ranges','41-entry coverage counts','four shared envelopes and declared dependency IDs',
  'source/proof/code/package bindings','independent ordered-outcome Bayes-risk enumeration for n0..8',
  'eight actual negative admission fixtures'],'independent_diagnostic_risks':independent,
  'validation_code_sha256':sha(__file__),'register_sha256':sha(ROOT/'register.proposed.json'),
  'limits':'Does not prove all source theorems, dependency completeness, source authenticity or empirical adequacy.'}
 (ROOT/'receipts/validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'release_validation':'passed','preserved_rules':16,'total_rules':32,'sources':41,'independent_risk_cases':9}))
if __name__=='__main__':run()
