"""Exact examples for invariant/temporal/metric-transfer distinctions."""
from fractions import Fraction as F
from certificate_support import check_package,emit

def cr(q):
 a,b,c,d=q
 return (a-c)*(b-d)/((a-d)*(b-c))

def run():
 p=check_package('connections',__file__)
 q=list(map(F,[1,2,3,4]))
 A=lambda x:2*x
 B=lambda x:x+1
 AB=[B(A(x)) for x in q] # Apply A then B, chronological names.
 BA=[A(B(x)) for x in q]
 assert cr(q)==cr(AB)==cr(BA)==F(4,3)
 assert all(y-x==1 for x,y in zip(AB,BA))
 contrast=lambda x:(x-1)/(x+1)
 assert all(-1<contrast(x)<1 for x in q+AB+BA)
 assert cr([contrast(x) for x in AB])==F(4,3)
 # Positive two-mode recovery, rates chosen by their exact unit-time attenuation.
 weights=[F(1,2),F(1,2)]; rates=[F(1,2),F(1,4)]
 moment=lambda t:sum((w*r**t for w,r in zip(weights,rates)),F(0))
 m1,m2=moment(1),moment(2)
 variance=sum((w*(r-m1)**2 for w,r in zip(weights,rates)),F(0))
 assert m1==F(3,8) and m2==F(5,32) and m2-m1*m1==variance==F(1,64)
 assert F(1,2)**2-F(1,2)**2==0
 # IDA energy-order counterexample, positive integration weights 1/2 and 1.
 leak=[F(1,2),F(1)]
 measures=lambda v:(sum((w*x for w,x in zip(leak,v)),F(0)),
                    sum((w*x*x for w,x in zip(leak,v)),F(0)))
 ra,qa=measures([F(4,5),F(4,5)]);rb,qb=measures([F(2),F(0)])
 assert rb<ra and qb>qa
 same_a=measures([F(0),F(1)]);same_b=measures([F(2),F(0)])
 assert same_a[0]==same_b[0] and same_a[1]!=same_b[1]
 # Rotated disk section B_a(i*z), evaluated with rational real/imaginary parts.
 a,z=F(1,3),F(1,2)
 real=a*(1+z*z)/(1+a*a*z*z);imag=z*(1-a*a)/(1+a*a*z*z)
 pure=(a+z)/(1+a*z)
 assert (real,imag,pure)==(F(15,37),F(16,37),F(5,7))
 assert real*real+imag*imag<1
 # Full quantum-like diagonal filter on probabilities: retain postselection mass.
 p0,a0,b0=F(1,3),F(3,4),F(1,4)
 success=a0*p0+b0*(1-p0)
 posterior=a0*p0/success
 x,u=2*p0-1,(a0-b0)/(a0+b0)
 assert success==F(5,12) and 2*posterior-1==(x+u)/(1+x*u)==F(1,5)
 emit('connections',p,__file__,{'status':'established_in_scope','check_count':13,
  'noncommuting_projective':{'q':list(map(str,q)),'A_then_B':list(map(str,AB)),
    'B_then_A':list(map(str,BA)),'all_cross_ratios':'4/3','order_difference':'1',
    'inference':'Order dependence is compatible with closed scalar projective state; endpoint-fixing UHL is an additional restriction.'},
  'recovery':{'m1':str(m1),'m2':str(m2),'semigroup_defect':str(variance),
    'interpretation':'Positive variance of mode attenuation rejects one exponential on these gaps under fixed positive weights.'},
  'ida_counterexample':{'linear_A':str(ra),'quadratic_A':str(qa),'linear_B':str(rb),'quadratic_B':str(qb),
    'same_linear_different_quadratic':[list(map(str,same_a)),list(map(str,same_b))]},
  'boost_section_counterexample':{'rotated_real':str(real),'rotated_imag':str(imag),'pure':str(pure),
    'scope':'Lemma2.1 listed premises only; full A1-A6 theorem not refuted by this example'},
  'diagonal_filter':{'success_mass':str(success),'posterior_population':str(posterior),'posterior_contrast':'1/5',
    'scope':'Conditional classical probability sector only; no phase deletion or full quantum theorem'},
  'unproved_by_code':['General cross-ratio, mixture-variance and section arguments in PROOFS.md',
    'No empirical mechanism or priority claim; no general complex ODE or classification proved']})
if __name__=='__main__':run()
