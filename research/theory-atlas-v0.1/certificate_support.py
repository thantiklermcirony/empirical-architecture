"""Utilities for these authored examples, not a universal proof checker."""
from pathlib import Path
import hashlib,json,os,sys
ROOT=Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def object_sha(value): return hashlib.sha256(canonical(value)).hexdigest()
def check_package(name,code):
    p=json.loads((ROOT/'packages'/f'{name}.json').read_text(encoding='utf-8'))
    for s in p['provenance']['sources']:
        path=Path(os.environ['ATLAS_SOURCE_ROOT'])/Path(s['path']).name if os.environ.get('ATLAS_SOURCE_ROOT') else Path(s['path'])
        if sha(path)!=s['sha256']: raise ValueError('Stale source: '+str(path))
    if sha(code)!=p['provenance']['code_sha256']: raise ValueError('Code differs from package')
    for item in p['provenance'].get('support_files',[]):
        if sha(ROOT/item['path'])!=item['sha256']: raise ValueError('Changed support: '+item['path'])
    return p
def admitted(p,depends,missing=()):
    known={x['id']:x['status'] for x in p['premises']}
    if any(s not in {'assumed','observed','derived','missing','rejected'} for s in known.values()):raise ValueError('Unknown premise status')
    if set(depends)-known.keys(): raise ValueError('Unknown premise dependency')
    if set(missing)-known.keys(): raise ValueError('Unknown removed premise')
    return 'unresolved' if any(x in missing or known[x] in ('missing','rejected') for x in depends) else 'established_in_scope'
def emit(name,p,code,result):
    result.update(certificate_version='0.1.0',result_kind='formal_under_premises',
      claim_scope='authored fixed-fixture calculation; use admission_adapter for application to a submitted inquiry',
      python=sys.version,code_sha256=sha(code),package_sha256=sha(ROOT/'packages'/f'{name}.json'),
      source_hashes={s['id']:s['sha256'] for s in p['provenance']['sources']})
    (ROOT/'receipts'/f'{name}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'certificate':name,'status':'passed','checks':result['check_count']}))
