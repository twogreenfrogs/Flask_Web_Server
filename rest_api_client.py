import requests
import re
import os
import sys
import time
from collections import defaultdict
import json
from pprint import pprint

class RESTClient(object):
    # customize http headers
    default_headers = {
    'User-Agent': 'Firefox',
    'Content-Type': 'application/json'
    }
    # convert Json Dict to Class Attributes
    class _ToAttrs(dict):
        #http://stackoverflow.com/questions/10026797/using-json-keys-as-python-attributes-in-nested-json
        def __getattr__(self, name):
            return self[name]

        def __setattr__(self, name, value):
            self[name] = value

        def __delattr__(self, name):
            del self[name]

    # todo: select interface
    def __init__(self, base_url=None, headers = None, auth=None, username=None, password=None, ssl_verify=False, ssl_cert=(None, None)):
        self.base_url = base_url
        self.auth = auth
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.ssl_cert = ssl_cert
        self.session = requests.Session()
        self.headers = RESTClient.default_headers
        if auth:
            if auth == 'digest':
                self.session.auth = requests.auth.HTTPDigestAuth(username, password)
            elif auth == 'basic':
                self.session.auth = requests.auth.HTTPBasicAuth(username, password)
            else:
                print 'Unknown auth method'
                return None

    def __enter__(self):
        return self

    def __exit__(self, etype, einst, etcb):
        #self.disconnect()
        if etype is not None:
            print etype
            print einst
            print etcb

    def get(self, uri, headers=None):
        headers = self.headers
        uri = self.base_url + uri
        if self.ssl_verify:
            resp = self.session.get(uri, headers=headers, verify=self.ssl_verify, cert=self.ssl_cert)
        else:
            resp = self.session.get(uri, headers=headers)

        return json.loads(resp.text, object_hook=self._ToAttrs)

    def post(self, uri, json_data, headers=None):
        headers = self.headers
        uri = self.base_url + uri
        if self.ssl_verify:
            resp = self.session.post(uri, json.dumps(json_data), headers=headers, verify=self.ssl_verify, cert=self.ssl_cert)
        else:
            resp = self.session.post(uri, json.dumps(json_data), headers=headers)
 
        return json.loads(resp.text, object_hook=self._ToAttrs)

    def delete(self, uri, headers=None):
        headers = self.headers
        uri = self.base_url + uri
        if self.ssl_verify:
            resp = self.session.delete(uri, headers=headers, verify=self.ssl_verify, cert=self.ssl_cert)
        else:
            resp = self.session.delete(uri, headers=headers)

        return json.loads(resp.text, object_hook=self._ToAttrs)

    def put(self, uri, json_data, headers=None):
        headers = self.headers
        uri = self.base_url + uri
        if self.ssl_verify:
            resp = self.session.put(uri, json.dumps(json_data), headers=headers, verify=self.ssl_verify, cert=self.ssl_cert)
        else:
            resp = self.session.put(uri, json.dumps(json_data), headers=headers)

        return json.loads(resp.text, object_hook=self._ToAttrs)
    


if __name__ == '__main__':
    # RESTClient Example(lsof -i :5000)
    REST_SERVER = 'http://162.243.249.178'
    REST_USERNAME = 'admin'
    REST_PASSWORD = 'tch123'
    
    with RESTClient(base_url=REST_SERVER, auth='basic', username=REST_USERNAME, password=REST_PASSWORD) as client:

    
        # Test1: get all events
        print '----- Test1: get all events -----'
        try:
            pprint(client.get('/api/events/'))
        except requests.exceptions.ConnectionError:
            print 'Cannot connect to {}'.format(REST_SERVER)
        print
        
        # Test2: get only 1 event
        print '----- Test2: get one event -----'
        try:
            pprint(client.get('/api/events/3G_OVERAGE/'))
        except requests.exceptions.ConnectionError:
            print 'Cannot connect to {}'.format(REST_SERVER)
        print
        
        # Test 3: create new event  
        print '----- Test3: create new event -----'
        json_data = {
            "event_name": "ANOTHER_EVENT",
            'emails': [u'inzoolee@hotmail.com'],
            'sms_nums': [u'+14041111111'],                        
            'twitters': False,
        }          
        pprint(client.post('/api/events/', json_data))
        print

        # Test 4: try to create same event  
        print '----- Test4: try to overwrite existing event -----'
        json_data = {
            "event_name": "ANOTHER_EVENT",
            'emails': [u'inzoolee@hotmail.com'],
            'sms_nums': [u'+14041111112'],                        
            'twitters': False,
        }          
        pprint(client.post('/api/events/', json_data))
        print

        # Test 5: update existing event  
        print '----- Test5: update existing event -----'
        json_data = {
            "event_name": "3G_OVERAGE",
            'emails': [u'inzoolee@hotmail.com', u'test@test.com', u'test@test.com'],
            'sms_nums': [u'+14041112222', u'+14101112345'],                        
            'twitters': True,
        }          
        pprint(client.put('/api/events/3G_OVERAGE/', json_data))
        print

        # Test 6: update non-existing event  
        print '----- Test6: update non-existing event -----'
        json_data = {
            "event_name": "NON_EXISTING",
            'emails': [u'inzoolee@hotmail.com', u'test@test.com', u'test@test.com'],
            'sms_nums': [u'+14041112222', u'+14101112345'],                        
            'twitters': True,
        }          
        pprint(client.put('/api/events/3G_OVERAGE/', json_data))
        print
                                        
#         # Test 7: trigger notification for specific event 
        print '----- Test7: trigger notification for event -----' 
        json_data = {
            "event_name": "3G_OVERAGE",
            'targets': ['email', 'sms', 'twitters' ],
        }          
        pprint(client.post('/api/events/trigger/3G_OVERAGE', json_data))
        print

        # Test 8: delete existing event  
        print '----- Test8: delete existing event -----'        
        pprint(client.delete('/api/events/ANOTHER_EVENT/'))
        print
        
        # Test 9: delete non-existing event  
        print '----- Test9: delete non-existing event -----'        
        pprint(client.delete('/api/events/NON_EXISTING_EVENT/'))
        print