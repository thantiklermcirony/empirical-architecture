"""Execute baseline admission and bounded negative fixtures, or assess one submitted JSON.

python run_admission.py --case composition --package changed.json --out report.json
The fixed fixture receipts must have been freshly produced or integrity-validated by
the caller. This script does not execute arbitrary submitted operations.
"""
from pathlib import Path
from copy import deepcopy
import argparse,json,tempfile,shutil,os
from certificate_support import ROOT,sha
from admission_adapter import assess,load_trusted

def run():
 cli=argparse.ArgumentParser()
 cli.add_argument('--case',choices=['composition','resources','action_evidence','connections'])
 cli.add_argument('--package',type=Path)
 cli.add_argument('--out',type=Path)
 args=cli.parse_args()
 trusted=load_trusted()
 packages={c:json.loads((ROOT/'packages'/f'{c}.json').read_text(encoding='utf-8')) for c in trusted['cases']}
 receipts={c:json.loads((ROOT/'receipts'/f'{c}.json').read_text(encoding='utf-8')) for c in packages}
 baseline={}
 for case in ['composition','resources','action_evidence','connections']:
  baseline[case]=assess(case,packages[case],receipts[case],trusted,parent=baseline.get('resources'))
 if args.package:
  if not args.case or not args.out:cli.error('--package needs --case and --out')
  result=assess(args.case,json.loads(args.package.read_text(encoding='utf-8')),receipts[args.case],trusted,parent=baseline['resources'])
  args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));return
 assert all(x['status']=='established_in_scope' for b in baseline.values() for x in b['conclusions'].values())
 fixtures=[]
 def mutate(case,pid,status='missing'):
  p=deepcopy(packages[case]);next(x for x in p['premises'] if x['id']==pid)['status']=status;return p
 for case,pid,target,survivor in [
  ('composition','COMP-02.P2','combined_operation','bounded_countermodel'),
  ('resources','RES-03.P2','duration_exclusion','balance'),
  ('connections','REC-03.P1','variance_interpretation','projective_order')]:
  r=assess(case,mutate(case,pid),receipts[case],trusted)
  assert r['conclusions'][target]['status']=='unresolved'
  assert r['conclusions'][survivor]['status']=='established_in_scope'
  assert r['fixture_facts_status']=='established_in_scope'
  fixtures.append({'name':'missing_'+pid,'report':r})
 changed=deepcopy(packages['composition']);changed['operations'][0]['formula']='(x+u)/2'
 next(x for x in changed['premises'] if x['id']=='COMP-02.P2')['statement']='The action is (x+u)/2.'
 r=assess('composition',changed,receipts['composition'],trusted)
 assert r['conclusions']['combined_operation']['status']=='out_of_scope' and r['conclusions']['bounded_countermodel']['status']=='established_in_scope'
 fixtures.append({'name':'changed_operation_not_executed_as_UHL','report':r})
 bad=mutate('composition','COMP-02.P2','magically_verified')
 r=assess('composition',bad,receipts['composition'],trusted)
 assert r['conclusions']['combined_operation']['status']=='execution_error'
 fixtures.append({'name':'unknown_status_rejected','report':r})
 missing_proof=deepcopy(packages['composition'])
 next(x for x in missing_proof['execution']['proof_obligations'] if x['id']=='ATLAS-PROOF-H-BIJECTION')['status']='missing'
 r=assess('composition',missing_proof,receipts['composition'],trusted)
 assert r['conclusions']['bounded_countermodel']['status']=='unresolved' and r['conclusions']['combined_operation']['status']=='established_in_scope'
 fixtures.append({'name':'missing_named_proof','report':r})
 parent=assess('resources',mutate('resources','RES-03.P2'),receipts['resources'],trusted)
 r=assess('action_evidence',packages['action_evidence'],receipts['action_evidence'],trusted,parent=parent)
 assert r['conclusions']['deadline_exclusion']['status']=='unresolved' and r['conclusions']['action_cover']['status']=='established_in_scope'
 fixtures.append({'name':'changed_parent_blocks_deadline','report':r})
 # Tamper only a temporary private copy, leaving all source manuscripts intact.
 with tempfile.TemporaryDirectory(prefix='atlas_source_test_') as td:
  for s in packages['composition']['provenance']['sources']:
   source=Path(s['path'])
   if os.environ.get('ATLAS_SOURCE_ROOT'):source=Path(os.environ['ATLAS_SOURCE_ROOT'])/source.name
   shutil.copyfile(source,Path(td)/source.name)
  one=Path(td)/Path(packages['composition']['provenance']['sources'][0]['path']).name
  with one.open('ab') as f:f.write(b'\nchanged test copy\n')
  r=assess('composition',packages['composition'],receipts['composition'],trusted,source_root=td)
  assert r['conclusions']['combined_operation']['status']=='unresolved' and r['source_errors']
  fixtures.append({'name':'changed_source_content','report':r})
 result={'version':'0.1.0','adapter_sha256':sha(ROOT/'admission_adapter.py'),
  'trusted_contracts_sha256':sha(ROOT/'trusted_contracts.json'),'baseline':baseline,'negative_fixtures':fixtures,
  'status':'passed','scope':'Actual four-fixture admission execution; no arbitrary-expression execution or generic DAG inference'}
 (ROOT/'receipts/admission.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'admission':'passed','baseline_cases':len(baseline),'negative_fixtures':len(fixtures)}))
if __name__=='__main__':run()
