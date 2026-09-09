"""Offline reference examples for The Empirical Architecture.

Synthetic and mathematical examples only. No model calls, clinical claims,
learned performance, or claims of novel mathematics. Python 3.10+, stdlib only.
"""
import argparse
import copy
from fractions import Fraction
import hashlib
import json


def state_example():
    observed = Fraction(1, 2)
    def response(capacity):
        return capacity * (1-observed)/(Fraction(1, 2)+1-observed)-1
    return {'kind':'synthetic dynamical example','observed_state':[float(observed)]*2,
            'omitted_capacity':[2,4],'future_initial_derivative':[float(response(2)),float(response(4))],
            'lesson':'The identical observation omits a variable that changes the future in this model.'}


def transformation_example():
    x=Fraction(1,5)
    def A(z): return (z+Fraction(1,5))/(1+z*Fraction(1,5))
    def B(z): return z/2
    ab=B(A(x)); ba=A(B(x))
    return {'kind':'exact bounded scalar model','start':float(x),'A_then_B':float(ab),'B_then_A':float(ba),
            'exact_A_then_B':str(ab),'exact_B_then_A':str(ba),
            'lesson':'A sufficient scalar state can have noncommuting actions; order dependence alone does not prove hidden state or hyperbolic curvature.'}


def ecology_example():
    # Finite Markov analogue of the stationary density/current distinction.
    def kernel(clockwise, counterclockwise):
        return [[Fraction(1,2) if i==j else clockwise if j==(i+1)%3 else counterclockwise
                 for j in range(3)] for i in range(3)]
    reversible=kernel(Fraction(1,4),Fraction(1,4))
    circulating=kernel(Fraction(2,5),Fraction(1,10))
    pi=[Fraction(1,3)]*3
    def stationary_error(P):
        return max(abs(sum(pi[i]*P[i][j] for i in range(3))-pi[j]) for j in range(3))
    def currents(P):
        return [pi[i]*P[i][(i+1)%3]-pi[(i+1)%3]*P[(i+1)%3][i] for i in range(3)]
    return {'kind':'exact finite Markov illustration; not an ecological dataset',
            'stationary_distribution':[float(x) for x in pi],
            'reversible_stationarity_error':float(stationary_error(reversible)),
            'circulating_stationarity_error':float(stationary_error(circulating)),
            'reversible_clockwise_currents':[float(x) for x in currents(reversible)],
            'circulating_clockwise_currents':[float(x) for x in currents(circulating)],
            'lesson':'The same stationary distribution can hide different directed transition currents; this toy example does not identify a biological niche mechanism.'}


RECORD={'entity':'synthetic-sample-A','property':'mass','value':'12','unit':'mg',
        'version':'v2','evidence_class':'synthetic-fixture'}
QUERY={'entity':'synthetic-sample-A','property':'mass','unit':'mg','version':'v2'}


def digest(record):
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def admit(proposal, query, record):
    """Tiny exact lookup interface, not a general factuality/semantic verifier."""
    keys={'entity','property','value','unit','version','evidence_digest'}
    if not isinstance(proposal,dict) or set(proposal)!=keys:
        return {'status':'reject','reason':'unsupported proposition shape'}
    if not all(type(v) is str for v in proposal.values()):
        return {'status':'reject','reason':'fields must be exact strings'}
    if proposal['evidence_digest']!=digest(record):
        return {'status':'reject','reason':'evidence record changed'}
    if any(proposal[k]!=query[k] for k in ('entity','property','unit','version')):
        return {'status':'reject','reason':'proposal does not answer the bound query'}
    if any(proposal[k]!=record[k] for k in ('entity','property','value','unit','version')):
        return {'status':'reject','reason':'proposal differs from the evidence record'}
    return {'status':'accept-source-relative',
            'text':f"The {record['version']} synthetic record lists {record['entity']} {record['property']} as {record['value']} {record['unit']}.",
            'scope':'Agreement with the bound synthetic record, not independent truth about the world.'}


def evidence_example():
    good={k:RECORD[k] for k in ('entity','property','value','unit','version')}
    good['evidence_digest']=digest(RECORD)
    stale=copy.deepcopy(good); stale['version']='v1'
    wrong=copy.deepcopy(good); wrong['value']='120'
    embellished=copy.deepcopy(good); embellished['interpretation']='definitely healthy'
    changed=copy.deepcopy(RECORD); changed['value']='13'
    return {'kind':'deterministic synthetic assertion checks; no generative model',
            'supported':admit(good,QUERY,RECORD),'wrong_version':admit(stale,QUERY,RECORD),
            'wrong_value':admit(wrong,QUERY,RECORD),'unsupported_interpretation':admit(embellished,QUERY,RECORD),
            'changed_evidence':admit(good,QUERY,changed),
            'lesson':'Meaning, evidence identity and query version are explicit. General evidence admission, language binding and model quality remain research/engineering work.'}


def run():
    return {'state':state_example(),'transformation':transformation_example(),
            'ecology':ecology_example(),'evidence':evidence_example()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true',help='Emit the full machine-readable examples')
    args=parser.parse_args()
    result=run()
    if args.json:
        print(json.dumps(result,indent=2))
    else:
        print('THE EMPIRICAL ARCHITECTURE | four offline reference examples')
        print('Synthetic/mathematical demonstrations; no empirical or AI benchmark claims.\n')
        for label,entry in result.items():
            print(label.upper())
            for k,v in entry.items():
                if k not in ('lesson','kind'): print(f'  {k}: {v}')
            print(' ',entry['lesson'],'\n')
