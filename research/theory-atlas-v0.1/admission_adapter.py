"""Domain adapter for four frozen authored fixtures; not a generic dependency engine.

The caller owns trusted contract selection, scheduling and receipt production. This
module checks whether this particular fixture answers a submitted inquiry. A passing
source hash establishes local integrity, not publisher authentication or truth.
"""
from pathlib import Path
import json,os
from certificate_support import ROOT,sha,object_sha

MODEL_FIELDS=('identity','question','system','observer','quantities','operations','constraints','mechanism')
def model_hash(package):return object_sha({k:package[k] for k in MODEL_FIELDS})
def receipt_hash(receipt):return object_sha({k:v for k,v in receipt.items() if k!='python'})

def assess(case,submitted,receipt,trusted,parent=None,source_root=None):
 spec=trusted['cases'][case]
 facts_ok=receipt_hash(receipt)==spec['receipt_semantic_sha256']
 findings=[]
 if not facts_ok:findings.append('fixture_receipt_mismatch')
 # These expected IDs/statements come from the frozen trusted contract, not the witness.
 declared=submitted.get('premises',[])
 ids=[x.get('id') for x in declared]
 malformed=len(ids)!=len(set(ids)) or any(x.get('status') not in {'assumed','observed','derived','missing','rejected'} for x in declared)
 premises={x.get('id'):x for x in declared}
 if malformed:findings.append('invalid_premise_record')
 mismatch=model_hash(submitted)!=spec['model_sha256']
 if mismatch:findings.append('submitted_model_differs_from_fixed_fixture')
 sources={s['id']:s for s in submitted.get('provenance',{}).get('sources',[])}
 source_errors=[]
 for sid,expected in spec['sources'].items():
  source=sources.get(sid)
  if not source or source.get('sha256')!=expected['sha256']:
   source_errors.append(sid+':binding');continue
  path=Path(source['path'])
  sr=source_root or os.environ.get('ATLAS_SOURCE_ROOT')
  if sr:path=Path(sr)/path.name
  try:actual=sha(path)
  except OSError:actual=None
  if actual!=expected['sha256']:source_errors.append(sid+':content')
 if source_errors:findings.append('source_integrity_failure')
 supplied_proofs={x['id']:x for x in submitted.get('execution',{}).get('proof_obligations',[])}
 conclusions={}
 for cid,definition in spec['conclusions'].items():
  missing=[];changed=[]
  for pid in definition['required_premises']:
   pr=premises.get(pid)
   if not pr or pr.get('status') in ('missing','rejected'):missing.append(pid)
   elif pr.get('status')!='assumed':changed.append(pid+':evidence_status_not_supported_by_this_fixture')
   if pr and pr.get('statement')!=spec['premise_statements'][pid]:changed.append(pid+':statement_changed')
  for pid in definition['required_proofs']:
   pr=supplied_proofs.get(pid);expected=spec['proofs'][pid]
   if not pr or pr.get('status')!='supplied_argument':missing.append(pid)
   elif pr.get('sha256')!=expected['sha256'] or pr.get('artifact')!=expected['artifact'] or sha(ROOT/expected['artifact'])!=expected['sha256']:
    changed.append(pid+':proof_binding')
  parent_problem=None
  if definition.get('parent'):
   required=definition['parent']
   if parent is None or parent.get('case')!=required['case'] or parent.get('submitted_package_sha256')!=required['package_object_sha256']:
    parent_problem='missing_or_changed_parent_package'
   elif parent.get('conclusions',{}).get(required['conclusion'],{}).get('status')!='established_in_scope':
    parent_problem='parent_conclusion_not_admitted'
  status='established_in_scope'
  if missing or changed or parent_problem or source_errors:status='unresolved'
  if mismatch and definition.get('requires_model_match',True):status='out_of_scope'
  if malformed or not facts_ok:status='execution_error'
  conclusions[cid]={'status':status,'result_kind':'formal_under_premises','missing':missing,
    'changed':changed,'parent_problem':parent_problem,'required_premises':definition['required_premises'],
    'proof_status':'supplied_argument_not_machine_verified' if definition['required_proofs'] else 'fixed_instance_arithmetic',
    'value_reference':definition['value_reference'] if status=='established_in_scope' else None}
 return {'case':case,'submitted_package_sha256':object_sha(submitted),
  'fixture_facts_status':'established_in_scope' if facts_ok else 'execution_error',
  'fixture_facts_scope':'Fixed authored mathematics; does not assert applicability to the submitted inquiry',
  'findings':findings,'source_errors':source_errors,'conclusions':conclusions,
  'trusted_contract_sha256':object_sha(spec),'adapter_sha256':sha(__file__),
  'boundary':'Four fixture contracts only. Required dependencies are trusted inputs; their scientific completeness and supplied proofs require review.'}

def load_trusted():return json.loads((ROOT/'trusted_contracts.json').read_text(encoding='utf-8'))
