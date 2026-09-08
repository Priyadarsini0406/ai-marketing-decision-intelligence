"""Integration tests using a real HTTP server and an isolated SQLite database.
Run with the project Python environment: python -m unittest test_admin -v
"""
import json
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

    def request(self, method, path, data=None, token=None, raw=None):
        headers = {}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        if raw is not None:
            body = ('--BOUNDARY\r\nContent-Disposition: form-data; name="file"; filename="campaign.csv"\r\nContent-Type: text/csv\r\n\r\n' + raw + '\r\n--BOUNDARY--\r\n').encode()
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
