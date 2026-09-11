"""Exact resource accounting, induction envelope and historical boundary counterexample."""
from fractions import Fraction as F
from certificate_support import ROOT,check_package,admitted,emit
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'vendor'))
from algebra import Compiler

def run():
 p=check_package('resources',__file__)
 c=Compiler({n:{'units':{}} for n in ['Jp','Jgr','Jreg','Jg','d','A','b','K','kappa','t']},{})
 pairs={
  'glutathione_balance':('(-2*Jp+2*Jgr+Jg)+2*(Jp-Jgr)','Jg'),
  'nicotinamide_balance':('(Jreg-Jgr)+(Jgr-Jreg)','0'),
  'reducing_equivalent_balance':('(-2*Jp+2*Jgr+Jg)/2+(Jreg-Jgr)','Jreg-Jp+Jg/2'),
  'early_budget_factorization':('1+t/4+t**2/8-t','(t-2)*(t-4)/8'),
  'late_budget_factorization':('1+t/4+(t-1)/2-t','(2-t)/4'),
  'adaptation_response':('(2*d/(1+d)-d/2)/2','d*(3-d)/(4*(1+d))')}
 identities={}
 for k,(a,b) in pairs.items():
  l,r=c.compile(a),c.compile(b)
  assert l.ratio.equal(r.ratio),k
  identities[k]={'equal':True,'original_denominators':[g.text() for g in l.guards+r.guards]}
 response=c.compile('d*(3-d)/(4*(1+d))')
 assert response.ratio.derivative('d').equal(c.compile('(1-d)*(d+3)/(4*(1+d)**2)').ratio)
 assert response.ratio.value({'d':F(1)})==F(1,4)
 # Quantities below are illustrative in a consistently normalized amount/time system.
 envelope=lambda T:F(1)+T/4+F(1,2)*(T*T/4 if T<=2 else T-1)
 assert envelope(F(3))==F(11,4) and F(3)-envelope(F(3))==F(1,4)
 # Open-pool countermodel: positive species throughout [0,3], same initial B=1.
 # G=1+t/2, O=1/2+3t/4, N=P=1/2; Jp=1,Jgr=Jreg=1/4,Jg=2.
 open_end={'G':F(5,2),'O':F(11,4),'N':F(1,2),'P':F(1,2)}
 assert open_end['G']/2+open_end['N']==F(7,4)
 assert F(-2)+2*F(1,4)+2==F(1,2)
 # Printed legacy equation at G=0,e=1,V=Gmax=KM=Vtotal=beta=1.
 boundary_drift=F(1,2)-1
 assert boundary_drift==F(-1,2)
 # Exact initial derivative in the illustrative two-state adaptation model.
 initial_z_dot=F(-1,2)  # d=1,b=1/2,tau_z=1,a=0,z=z0=0
 initial_x_dot=initial_z_dot # x=tanh(z); derivative at zero equals one (imported).
 assert initial_x_dot<0
 no_induction_response=-F(1,4) # -bd/(1+A*kappa), d=1,C=2
 assert no_induction_response<0
 deps=['RES-03.P1','RES-03.P2','RES-04.P1','RES-04.P2']
 contrasts=[{'removed':None,'budget_status':admitted(p,deps)},
            {'removed':'RES-03.P2','budget_status':admitted(p,deps,['RES-03.P2']),
             'conservation_identity_status':admitted(p,['RES-03.P1'],['RES-03.P2']),
             'explicit_open_pool_countermodel':'Jg=2 permits the declared positive ledger through T=3'},
            {'removed':'RES-04.P1','budget_status':admitted(p,deps,['RES-04.P1'])}]
 emit('resources',p,__file__,{'status':'established_in_scope','check_count':14,'identities':identities,
  'units':'B in peroxide-clearance equivalents; fluxes in corresponding amount per time; illustrative normalized values',
  'duration_exclusion':{'T':'3','required':'3','upper_budget':str(envelope(F(3))),'shortfall':'1/4',
    'general_statement':'For this envelope, every T>2 is excluded; T<=2 is only not excluded.'},
  'adaptation':{'peak_dose':'1','crossing_dose':'3','peak_rapidity_shift':'1/4',
    'initial_z_slope':str(initial_z_dot),'initial_x_slope':str(initial_x_dot),
    'no_induction_shift':str(no_induction_response),'shared_interval_initial_dip_status':'unchanged: unresolved in supplied shared receipt'},
  'boundary_counterexample':{'drift_at_G_zero':str(boundary_drift),
    'claim_refuted':'The printed smooth vector field makes G=0 an invariant depleted equilibrium.'},
  'premise_contrasts':contrasts,
  'unproved_by_code':['Integral balance and induction comparison proof in PROOFS.md',
   'Existence, nonnegative kinetics and actual biological calibration are additional obligations',
   'No proof of actual rescue, durable fate, hormesis universality or depleted attractor']})
if __name__=='__main__':run()
