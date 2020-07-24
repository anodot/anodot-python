import requests
import urllib.parse


class ApiClient:

    def __init__(self, access_key: str, proxies: dict, base_url='https://app.anodot.com'):
        self.access_key = access_key
        self.base_url = base_url
        self.proxies = proxies
        self.session = requests.Session()
        self.get_auth_token()

    def get_auth_token(self):
        auth_token = self.session.post(self.build_url('access-token'),
                                       json={'refreshToken': self.access_key},
                                       proxies=self.proxies)
        auth_token.raise_for_status()
        self.session.headers.update({'Authorization': 'Bearer ' + auth_token.text.replace('"', '')})

    def build_url(self, *args):
        return urllib.parse.urljoin(self.base_url, '/'.join(['/api/v2', *args]))

    def create_schema(self, schema):
        return self.session.post(self.build_url('stream-schemas'), json=schema, proxies=self.proxies)

    def delete_schema(self, schema_id):
        return self.session.delete(self.build_url('stream-schemas', schema_id), proxies=self.proxies)

    def send_topology_data(self, data_type, data):
        return self.session.post(self.build_url('topology', 'data'),
                                 proxies=self.proxies,
                                 data=data,
                                 params={'type': data_type})
