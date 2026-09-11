"""Run the four isolated certificates. Python >=3.10, standard library only."""
from pathlib import Path
import argparse,subprocess,sys,os
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--source-root',help='Directory containing the original hash-matching current/legacy text snapshots')
args=p.parse_args()
env=os.environ.copy()
env['PYTHONDONTWRITEBYTECODE']='1'
if args.source_root:env['ATLAS_SOURCE_ROOT']=str(Path(args.source_root).resolve())
for name in ['composition','resources','action_evidence','connections']:
 subprocess.run([sys.executable,'-B',str(root/f'certify_{name}.py')],check=True,cwd=root,env=env)
subprocess.run([sys.executable,'-B',str(root/'run_admission.py')],check=True,cwd=root,env=env)
