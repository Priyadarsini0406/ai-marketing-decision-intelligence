"""Integration tests using a real HTTP server and an isolated SQLite database.
Run with the project Python environment: python -m unittest test_admin -v
"""
import json
import io
import zipfile
import os
from pathlib import Path
import socket
import tempfile
import time
import unittest
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class AdminIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.previous_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = "sqlite:///" + str(Path(cls.temp.name) / "test.db")
        from database.connection import Base, engine, SessionLocal
        from api.auth import NewUser, create_user
        import uvicorn
        cls.engine = engine
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            create_user(NewUser(name='Admin', email='admin@example.com', password='TestPassword123!', role='admin'), db)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        cls.server = uvicorn.Server(uvicorn.Config('main:app', host='127.0.0.1', port=port, log_level='error'))
        cls.thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.thread.start()
        for _ in range(100):
            try:
                urlopen(cls.base, timeout=1).close()
                return
            except OSError:
                time.sleep(.1)
        cls.server.should_exit = True
        raise RuntimeError('Test server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=10)
        cls.engine.dispose()
        cls.temp.cleanup()
        if cls.previous_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_url

    def request(self, method, path, data=None, token=None, raw=None, filename='campaign.csv'):
        headers = {}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        if raw is not None:
            body = (f'--BOUNDARY\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
                    + (raw.encode() if isinstance(raw, str) else raw) + b'\r\n--BOUNDARY--\r\n')
            headers['Content-Type'] = 'multipart/form-data; boundary=BOUNDARY'
        try:
            response = urlopen(Request(self.base + path, data=body, headers=headers, method=method), timeout=10)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def login(self, email='admin@example.com', password='TestPassword123!'):
        status, data = self.request('POST', '/auth/login', {'email': email, 'password': password})
        self.assertEqual(status, 200, data)
        return data['token']

    def test_admin_workflows_and_access_control(self):
        for path in ['/admin/users', '/admin/datasets', '/admin/configuration', '/admin/reports', '/leads/']:
            self.assertEqual(self.request('GET', path)[0], 401)
        self.assertEqual(self.request('POST', '/auth/login', {'email':'admin@example.com','password':'wrong'})[0], 401)
        admin = self.login()
        user_data = {'name':'Marketer','email':'marketer@example.com','password':'StrongPassword123!','role':'marketer'}
        self.assertEqual(self.request('POST','/auth/register', {**user_data,'role':'admin'})[0], 403)
        status, user = self.request('POST','/admin/users', user_data, admin)
        self.assertEqual(status, 201)
        self.assertNotIn('password_hash', user)
        self.assertEqual(self.request('POST','/admin/users', user_data, admin)[0], 409)
        regular = self.login(user_data['email'], user_data['password'])
        for path in ['/workspace/overview', '/workspace/segments', '/workspace/settings']:
            self.assertEqual(self.request('GET',path)[0],401)
        self.assertEqual(self.request('POST','/workspace/simulate',{'budget':100,'mode':'equal'})[0],401)
        self.assertEqual(self.request('PUT','/workspace/settings',{'currency':'INR','compact':True},regular)[0],200)
        self.assertEqual(self.request('GET','/workspace/settings',token=regular)[1],{'currency':'INR','compact':True})
        self.assertEqual(self.request('GET','/workspace/settings',token=admin)[1]['currency'],'USD')
        self.assertEqual(self.request('PUT','/workspace/settings',{'currency':'BAD'},regular)[0],422)
        lead_data = {'customer_id':'WORKSPACE-1','age':30,'gender':'Female','income':1000,
                     'campaign_channel':'Email','campaign_type':'Awareness','ad_spend':100,
                     'click_through_rate':.1,'conversion_rate':.1,'website_visits':2,
                     'pages_per_visit':2,'time_on_site':3,'social_shares':0,'email_opens':2,
                     'email_clicks':1,'previous_purchases':0,'loyalty_points':0,'conversion':True}
        self.assertEqual(self.request('POST','/leads',lead_data)[0],401)
        status, created_lead = self.request('POST','/leads',lead_data,regular)
        self.assertEqual(status,201,created_lead)
        self.assertEqual(self.request('POST','/leads',lead_data,regular)[0],409)
        self.assertEqual(self.request('PUT','/leads/'+created_lead['id'],{**lead_data,'ad_spend':200},regular)[0],200)
        self.assertEqual(self.request('GET','/leads?search=WORKSPACE-1',token=regular)[1][0]['ad_spend'],200)
        status, scenario = self.request('POST','/workspace/simulate',{'budget':1000,'mode':'equal'},regular)
        self.assertEqual(status,200,scenario)
        self.assertEqual(scenario['predicted_conversions'],5)
        self.assertEqual(self.request('POST','/workspace/simulate',{'budget':1000,'mode':'custom','allocations':{'Email':20}},regular)[0],422)
        overview = self.request('GET','/workspace/overview',token=regular)[1]
        self.assertEqual(overview['summary']['leads'],1)
        self.assertEqual(overview['funnel'][-1]['count'],1)
        self.assertEqual(self.request('GET','/workspace/segments',token=regular)[1][0]['leads'],1)
        def zipped(entries):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, value in entries.items():
                    archive.writestr(name, value)
            return output.getvalue()
        for endpoint, token in [('/datasets', regular), ('/admin/datasets', admin)]:
            status, item = self.request('POST', endpoint, token=token, filename='campaign.zip',
                raw=zipped({'folder/campaign.csv':'channel,spend\nSEO,100', 'README.txt':'Campaign data'}))
            self.assertEqual(status, 201, item)
            self.assertEqual(item['row_count'], 1)
            self.assertEqual(self.request('DELETE','/admin/datasets/'+item['id'],token=admin)[0],200)
        for contents in [b'broken zip', zipped({'readme.txt':'no CSV'}),
                         zipped({'a.csv':'a\n1', 'b.csv':'b\n2'}), zipped({'a.csv':'a,a\n1,2'})]:
            self.assertEqual(self.request('POST','/datasets',token=regular,filename='bad.zip',raw=contents)[0],400)
        self.assertEqual(self.request('POST','/datasets',token=regular,filename='big.zip',
            raw=zipped({'a.csv':'a\n' + 'x' * (5 * 1024 * 1024)}))[0],413)
        self.assertEqual(self.request('POST','/datasets',raw='channel,spend\nSEO,100')[0],401)
        self.assertEqual(self.request('POST','/datasets',token=regular,raw='a,a\n1,2')[0],400)
        status, uploaded = self.request('POST','/datasets',token=regular,raw='channel,spend\nSEO,100')
        self.assertEqual(status,201,uploaded)
        self.assertEqual(uploaded['row_count'],1)
        upload_path = '/admin/datasets/' + uploaded['id']
        self.assertEqual(self.request('POST','/admin/datasets',token=regular,raw='a\n1')[0],403)
        self.assertEqual(self.request('PUT',upload_path,{'name':'Changed'},regular)[0],403)
        self.assertEqual(self.request('DELETE',upload_path,token=regular)[0],403)
        self.assertEqual(self.request('GET',upload_path,token=admin)[1]['rows'][0]['channel'],'SEO')
        self.assertEqual(self.request('DELETE',upload_path,token=admin)[0],200)
        for path in ['/admin/users','/admin/datasets','/admin/configuration','/admin/reports']:
            self.assertEqual(self.request('GET',path,token=regular)[0],403)
        self.assertEqual(self.request('POST','/admin/users',user_data,regular)[0],403)
        status, admin_user = self.request('GET','/auth/me',token=admin)
        self.assertEqual(self.request('PUT','/admin/users/'+admin_user['id'],{'name':'Admin','role':'marketer','active':True},admin)[0],400)
        update = {'name':'Updated','role':'admin','active':True,'password':'ChangedPassword123!'}
        self.assertEqual(self.request('PUT','/admin/users/'+user['id'],update,admin)[0],200)
        self.assertEqual(self.request('GET','/auth/me',token=regular)[0],401)
        promoted = self.login(user_data['email'], update['password'])
        self.assertEqual(self.request('GET','/admin/reports',token=promoted)[0],200)
        self.assertEqual(self.request('PUT','/admin/users/'+user['id'],{**update,'active':False},admin)[0],200)
        self.assertEqual(self.request('GET','/admin/reports',token=promoted)[0],401)
        self.assertEqual(self.request('POST','/auth/login',{'email':user_data['email'],'password':update['password']})[0],401)
        self.assertEqual(self.request('POST','/admin/datasets',token=admin,raw='a,a\n1,2')[0],400)
        self.assertEqual(self.request('POST','/admin/datasets',token=admin,raw='a,b\n1')[0],400)
        status, dataset = self.request('POST','/admin/datasets',token=admin,raw='channel,spend\nSEO,100\nEmail,200')
        self.assertEqual(status,201,dataset)
        self.assertEqual(dataset['row_count'],2)
        path = '/admin/datasets/'+dataset['id']
        self.assertEqual(self.request('GET',path,token=admin)[1]['rows'][0]['channel'],'SEO')
        self.assertEqual(self.request('PUT',path,{'name':'Campaign data'},admin)[1]['name'],'Campaign data')
        config = self.request('GET','/admin/configuration',token=admin)[1]
        self.assertEqual(self.request('PUT','/admin/configuration',{**config,'conversion_threshold':2},admin)[0],422)
        config.update(currency='INR',conversion_threshold=.8)
        self.assertEqual(self.request('PUT','/admin/configuration',config,admin)[0],200)
        report = self.request('GET','/admin/reports',token=admin)[1]
        self.assertEqual(report['configuration']['currency'],'INR')
        self.assertEqual(report['summary']['dataset_rows'],2)
        self.assertEqual(self.request('DELETE',path,token=admin)[0],200)
        self.assertEqual(self.request('GET',path,token=admin)[0],404)
        self.assertEqual(self.request('POST','/auth/logout',token=admin)[0],200)
        self.assertEqual(self.request('GET','/admin/users',token=admin)[0],401)

if __name__ == '__main__':
    unittest.main()
