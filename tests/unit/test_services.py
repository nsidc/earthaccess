import json
import unittest

import earthaccess
from vcr.unittest import VCRTestCase  # type: ignore[import-untyped]


class TestServices(VCRTestCase):
    
    def _get_vcr(self, **kwargs):
        myvcr = super(TestServices, self)._get_vcr(**kwargs)
        myvcr.cassette_library_dir = "tests/unit/fixtures/vcr_cassettes"
        return myvcr
    
    def test_services(self):
        """Test DataService get function return of service metadata results."""

        query = earthaccess.services.DataService().parameters(
            concept_id="S2004184019-POCLOUD"
        )
        actual = query.get(query.hits())
        actual = json.loads(actual[0])
        with open("tests/unit/fixtures/S2004184019-POCLOUD.json") as jf:
            expected = json.load(jf)
        self.assertTrue(actual["items"] == expected[0]["items"])

if __name__ == '__main__':
    unittest.main()