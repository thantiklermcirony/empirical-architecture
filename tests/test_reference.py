import copy
import unittest
from reference_demo import QUERY, RECORD, admit, digest, run


class ReferenceExamples(unittest.TestCase):
    def test_equal_observation_distinct_future(self):
        r=run()['state']
        self.assertEqual(r['observed_state'][0],r['observed_state'][1])
        self.assertNotEqual(*r['future_initial_derivative'])

    def test_order_dependence_inside_bound(self):
        r=run()['transformation']
        self.assertNotEqual(r['exact_A_then_B'],r['exact_B_then_A'])
        for k in ['A_then_B','B_then_A']: self.assertTrue(-1<r[k]<1)

    def test_stationarity_does_not_identify_current(self):
        r=run()['ecology']
        self.assertEqual(r['reversible_stationarity_error'],0)
        self.assertEqual(r['circulating_stationarity_error'],0)
        self.assertEqual(r['reversible_clockwise_currents'],[0,0,0])
        self.assertEqual(r['circulating_clockwise_currents'],[.1,.1,.1])

    def test_bound_evidence_only(self):
        r=run()['evidence']
        self.assertEqual(r['supported']['status'],'accept-source-relative')
        for k in ['wrong_version','wrong_value','unsupported_interpretation','changed_evidence']:
            self.assertEqual(r[k]['status'],'reject')

    def test_malformed_or_extended_proposals_rejected(self):
        good={k:RECORD[k] for k in ['entity','property','value','unit','version']}
        good['evidence_digest']=digest(RECORD)
        for malformed in [None,[],{},dict(good,value=12),dict(good,value=True),dict(good,extra='claim')]:
            self.assertEqual(admit(malformed,QUERY,RECORD)['status'],'reject')

    def test_record_identity_is_not_external_truth(self):
        altered=copy.deepcopy(RECORD); altered['value']='999'
        p={k:altered[k] for k in ['entity','property','value','unit','version']}
        p['evidence_digest']=digest(altered)
        r=admit(p,QUERY,altered)
        self.assertEqual(r['status'],'accept-source-relative')
        self.assertIn('not independent truth',r['scope'])


if __name__=='__main__': unittest.main()
