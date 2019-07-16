# -*- coding: utf-8 -*-

"""Test for pyops."""

import logging
import sys
import unittest

sys.path.append('../')

import pyops

class OpsTest(unittest.TestCase):

    def test_class_parameters(self):
        # logging.basicConfig(level=logging.DEBUG)

        with self.assertRaises(ValueError):
            client = pyops.Client()
    
    def test_search_without_parameters(self):
        # logging.basicConfig(level=logging.DEBUG)

        client = pyops.Client(search_endpoint='https://catalog.terradue.com/sentinel1/search', type='results')
        self.assertIsInstance(client, pyops.Client)
        
        raw_results = client.search()
        self.assertIsInstance(raw_results, list)
        self.assertTrue(len(raw_results) > 0)

    def test_search_with_parameters(self):
        # logging.basicConfig(level=logging.DEBUG)

        # Search with params
        client = pyops.Client(search_endpoint='https://catalog.terradue.com/sentinel1/search', type='results')
        self.assertIsInstance(client, pyops.Client)
        
        raw_results = client.search(params={"{eop:instrument?}": {"value": "SAR"}})
        self.assertIsInstance(raw_results, list)
        self.assertTrue(len(raw_results) > 0)

        fields = client.get_available_fields()
        self.assertIsInstance(fields, list)
        self.assertTrue(len(fields) > 0)

        filtered_results = client.filter_entries([{
            "tag": "{http://www.w3.org/2005/Atom}id",
            "name": "id"
        }, {
            "tag": "{http://www.w3.org/2005/Atom}title",
            "name": "title"
        }, {
            "tag": "{http://www.w3.org/2005/Atom}summary",
            "name": "summary"
        }, {
            "tag": "{http://www.w3.org/2005/Atom}published",
            "name": "published"
        }, {
            "tag": "{http://www.w3.org/2005/Atom}updated",
            "name": "updated"
        }, {
            "tag": "{http://www.w3.org/2005/Atom}link",
            "name": "link",
            "rel": "enclosure"
        }])
        self.assertIsInstance(filtered_results, list)
        self.assertTrue(len(filtered_results) > 0)
    
    def test_fedeo_collection_search(self):
        client = pyops.Client(description_xml_url='http://fedeo.esa.int/opensearch/description.xml')
        self.assertIsInstance(client, pyops.Client)

        raw_results = client.search(force_HTTPS=False)
        self.assertIsInstance(raw_results, list)
        self.assertTrue(len(raw_results) > 0)

    def test_fedeo_results_search(self):
        client = pyops.Client(description_xml_url='http://fedeo.esa.int/opensearch/description.xml?parentIdentifier=ENVISAT.ASA.APS_1P', type='results')
        self.assertIsInstance(client, pyops.Client)

        raw_results = client.search(force_HTTPS=False)
        self.assertIsInstance(raw_results, list)
        self.assertTrue(len(raw_results) > 0)

    #def test_authentication(self):
    #    client = pyops.Client(description_xml_url="")
    #    raw_results = client.search(auth=('', ''))
    #    self.assertIsInstance(raw_results, list)
    #    self.assertTrue(len(raw_results) > 0)


if __name__ == "__main__":
    # unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(OpsTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
