"""Authored COMP-02 certificate; not a general inquiry engine. Python 3.12, stdlib.
Run from this directory: python certify_composition.py
"""
from pathlib import Path
import hashlib, json, sys
from certificate_support import check_package
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent / 'vendor'))
from algebra import Compiler, domain_report

ROOT = Path(__file__).resolve().parent
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    package = check_package('composition',__file__)
    symbols = {n:{'units':{}} for n in ['x','u','v','a','b','c','d','p','q']}
    compiler = Compiler(symbols, {'T':{'arguments':['x','u'],'expression':'(x+u)/(1+x*u)'},
                                  'h':{'arguments':['x'],'expression':'x/(1-x**2)'}})
    pairs = {
        'composition':('T(T(x,u),v)','T(x,T(u,v))'),
        'identity':('T(x,0)','x'),
        'inverse':('T(T(x,u),-u)','x'),
        'interior_defect':('1-T(x,u)**2','(1-x**2)*(1-u**2)/(1+x*u)**2'),
        'projective_difference':('(a*p+b)/(c*p+d)-(a*q+b)/(c*q+d)',
                                 '(a*d-b*c)*(p-q)/((c*p+d)*(c*q+d))')}
    checks={}
    for name,(left,right) in pairs.items():
        lhs,rhs=compiler.compile(left),compiler.compile(right)
        assert lhs.ratio.equal(rhs.ratio), name
        checks[name]={'exact_polynomial_identity':True,'domain_obligations':[g.text()+' != 0' for g in lhs.guards+rhs.guards],
                      'global_domain_proof':'PROOFS.md#composition'}
    derivative=compiler.compile('h(x)').ratio.derivative('x')
    assert derivative.equal(compiler.compile('(1+x**2)/(1-x**2)**2').ratio)
    T=lambda x,u:(x+u)/(1+x*u)
    example=T(T(F(1,4),F(1,3)),F(1,2))
    assert example==F(9,11)
    w=T(F(1,3),F(1,2)); assert w==F(5,7)
    h=lambda x:x/(1-x*x)
    mismatch=h(T(F(1,2),F(1,2)))-2*h(F(1,2))
    assert mismatch==F(8,9)
    # Scale-blind lift preserves cross ratio; a strictly monotone bounded map need not.
    cr=lambda a,b,c,d:(a-c)*(b-d)/((a-d)*(b-c))
    points=list(map(F,['1','2','3','4']))
    M=lambda q:(2*q+1)/(q+2)
    assert cr(*points)==cr(*map(M,points))==F(4,3)
    bounded=list(map(F,['1/5','2/5','3/5','4/5']))
    squared=[x*x for x in bounded]
    assert cr(*bounded)==F(4,3) and cr(*squared)==F(32,25)
    # Specific package dependencies are explicit; this is not a generic provenance validator.
    outcomes=[]
    for removed in [None,'COMP-02.P2','COMP-02.P3']:
        outcomes.append({'removed_premise':removed,'composition_status':'established_in_scope' if removed is None else 'unresolved',
                         'bounded_group_counterexample_status':'established_in_scope'})
    result={'certificate_version':'0.1.0','result_kind':'formal_under_premises','status':'established_in_scope',
            'claim_scope':'authored fixed-fixture calculation; use admission_adapter for application to a submitted inquiry',
            'checks':checks,'inputs':{'x':'1/4','u':'1/3','v':'1/2'},'combined_parameter':str(w),'final_state':str(example),
            'bounded_alternative':{'generator':'h(x)=x/(1-x^2)','h(UHL(1/2,1/2))-2*h(1/2)':str(mismatch),
                                   'conclusion':'The h-induced bounded group is not UHL in the declared x coordinate.'},
            'cross_ratio':{'before':'4/3','projective_after':'4/3','square_map_after':'32/25'},
            'premise_contrasts':outcomes,'unproved_by_code':['Global real-domain arguments and monotone bijection proof supplied in PROOFS.md',
                'artanh translation requires the stated real-logarithm theorem','No empirical or physical branch selection is checked'],
            'code_sha256':digest(__file__),'algebra_sha256':digest(ROOT/'vendor/algebra.py'),
            'package_sha256':digest(ROOT/'packages/composition.json'),'python':sys.version}
    (ROOT/'receipts/composition.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'certificate':'composition','status':'passed','exact_identities':len(checks),'final_state':str(example),'counterexample_gap':str(mismatch)}))
if __name__=='__main__': run()
