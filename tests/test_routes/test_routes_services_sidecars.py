import json
from hedweb.constants import base_constants
from tests.test_routes.test_routes_base import TestRouteBase


class Test(TestRouteBase):
    def test_submit_service_sidecar_route(self):
        with self.app.app_context():
            json_data = {base_constants.SIDECAR_STRING: self._get_file_string("bids_events.json"),
                         base_constants.CHECK_FOR_WARNINGS: 'on',
                         base_constants.SCHEMA_VERSION: '8.2.0', base_constants.SERVICE: 'sidecar_validate'}

            response = self.app.test.post('/services_submit', content_type='application/json', data=json.dumps(json_data))
            json_data2 = json.loads(response.data)
            results = json_data2['results']
            self.assertEqual('success', results['msg_category'],
                             "sidecar_validation services has success on bids_events.json")
            self.assertEqual(json.dumps('8.2.0'), results[base_constants.SCHEMA_VERSION], 'Version 8.2.0 was used')

    def test_submit_service_sidecar_route2(self):
        json_data = {base_constants.SERVICE: 'sidecar_validate', base_constants.SCHEMA_VERSION: "8.2.0",
                     base_constants.COMMAND: 'validate', base_constants.COMMAND_TARGET: 'sidecar',
                     base_constants.SIDECAR_STRING: self._get_file_string("bids_events.json"),
                     }
        with self.app.app_context():
            response = self.app.test.post('/services_submit', "application/json", data=json.dumps(json_data))
            json_data2 = json.loads(response.data)
            results = json_data2['results']
            self.assertEqual('success', results['msg_category'],
                             "sidecar_validation services has success on bids_events.json")
            self.assertEqual(json.dumps('8.2.0'), results[base_constants.SCHEMA_VERSION], 'Version 8.2.0 was used')

        json_data[base_constants.SIDECAR_STRING] = self._get_file_string("bids_events_bad.json")
        with self.app.app_context():
            response = self.app.test.post('/services_submit', content_type='application/json',
                                          data=json.dumps(json_data))
            json_data2 = json.loads(response.data)
            results = json_data2['results']
            self.assertTrue(results['data'], 'sidecar_validation produces errors when file not valid')
            self.assertEqual('warning', results['msg_category'], "sidecar_validation did not valid with 8.2.0")
            self.assertEqual(json.dumps('8.2.0'), results['schema_version'], 'Version 8.2.0 was used')

