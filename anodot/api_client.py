import json
import logging
import requests
import sys
import urllib.parse

from enum import Enum
from typing import Iterable, List, Optional
from .metric import Metric, Watermark, Schema, MissingDimPolicy, MissingDimPolicyAction, Measurement, Aggregation

BATCH_SIZE = 1000
MAX_BATCH_DEBUG_OUTPUT = 10


def _get_default_logger(level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


_default_logger = _get_default_logger()


class ApiClient:
    def __init__(self, access_key: str, proxies: dict = None, base_url='https://app.anodot.com'):
        self.access_key = access_key
        self.base_url = base_url
        self.proxies = proxies or {}
        self.session = requests.Session()
        self.authenticate_session()

    def authenticate_session(self):
        auth_token = self.session.post(
            self.build_url('access-token'),
            json={'refreshToken': self.access_key},
            proxies=self.proxies,
        )
        auth_token.raise_for_status()
        self.session.headers.update({'Authorization': 'Bearer ' + auth_token.text.replace('"', '')})

    def build_url(self, *args):
        return urllib.parse.urljoin(self.base_url, '/'.join(['/api/v2', *args]))

    def get_all_schemas(self) -> List[Schema]:
        res = self.session.get(
            self.build_url('stream-schemas', 'schemas'),
            params={'excludeCubes': True},
            proxies=self.proxies,
        )
        res.raise_for_status()

        schemas = []
        for schema in res.json():
            s = schema['streamSchemaWrapper']['schema']
            missing_dim_policy = MissingDimPolicy(
                MissingDimPolicyAction(s['missingDimPolicy']['action']),
                s['missingDimPolicy'].get('fill'),
            )
            schemas.append(Schema(
                name=s['name'],
                dimensions=s['dimensions'],
                measurements=[
                    Measurement(name, Aggregation(measurement['aggregation']))
                    for name, measurement in s['measurements'].items()
                ],
                missing_dim_policy=missing_dim_policy,
                version=s.get('version', 1),
                id_=s['id'],
            ))

        return schemas

    def find_by_name(self, schema_name: str) -> Optional[Schema]:
        return next(
            (
                schema
                for schema in self.get_all_schemas()
                if schema.name == schema_name
            ),
            None,
        )

    def create_schema(self, schema: Schema) -> dict:
        res = self.session.post(self.build_url('stream-schemas'), json=schema.to_dict(), proxies=self.proxies)
        res.raise_for_status()
        return res.json()

    def delete_schema(self, schema_id: str):
        res = self.session.delete(self.build_url('stream-schemas', schema_id), proxies=self.proxies)
        res.raise_for_status()
        return res.json()

    def send_topology_data(self, data_type, data):
        res = self.session.post(self.build_url('topology', 'data'),
                                proxies=self.proxies,
                                data=data,
                                params={'type': data_type})

        res.raise_for_status()
        return res.json()


class AnodotAPIResponseException(Exception):
    pass


class Protocol(Enum):
    ANODOT20 = 'anodot20'
    ANODOT30 = 'anodot30'


def send(data: Iterable[Metric],
         token: str,
         logger: logging.Logger = None,
         base_url: str = 'https://app.anodot.com',
         dry_run: bool = False,
         protocol: Protocol = Protocol.ANODOT20):
    """

    :param data: List of Metric objects
    :param token: Data collection token (https://support.anodot.com/hc/en-us/articles/360002631114#DataCollectionKey)
    :param logger: Logger object, if empty default_logger is used
    :param base_url: Base url for Anodot api
    :param dry_run:
    :param protocol: metrics protocol
    :return:
    """
    if not logger:
        logger = _default_logger

    batch = []
    for item in data:
        batch.append(item.to_dict())
        if len(batch) == BATCH_SIZE:
            _send_request(batch, logger, token, base_url, dry_run, protocol)
            batch = []

    _send_request(batch, logger, token, base_url, dry_run, protocol)


def send_watermark(watermark: Watermark,
                   token: str,
                   logger: logging.Logger = None,
                   base_url: str = 'https://app.anodot.com',
                   dry_run: bool = False):
    """

    :param watermark:
    :param token: Data collection token (https://support.anodot.com/hc/en-us/articles/360002631114#DataCollectionKey)
    :param logger: Logger object, if empty default_logger is used
    :param base_url: Base url for Anodot api
    :param dry_run:
    :return:
    """
    if not logger:
        logger = _default_logger

    logger.info('Sending watermark: ' + str(watermark.to_dict()))
    if not dry_run:
        response = requests.post(urllib.parse.urljoin(base_url, '/api/v1/metrics/watermark'),
                                 params={'token': token, 'protocol': Protocol.ANODOT30.value},
                                 json=watermark.to_dict())
        response.raise_for_status()
        response_data = response.json()
        logger.info('Response: ' + str(response_data))


def _send_request(batch: list,
                  logger: logging.Logger,
                  token: str,
                  base_url: str = 'https://app.anodot.com',
                  dry_run: bool = False,
                  protocol: Protocol = Protocol.ANODOT20):
    if len(batch) == 0:
        logger.info('Received empty batch')
        return

    logger.debug(f'Sending batch example: {str(batch[:MAX_BATCH_DEBUG_OUTPUT])}')
    if not dry_run:
        response = requests.post(urllib.parse.urljoin(base_url, '/api/v1/metrics'),
                                 params={'token': token, 'protocol': protocol.value},
                                 json=batch)
        response.raise_for_status()
        response_data = response.json()
        messages = []
        for item in response_data['errors']:
            msg = f'{item["error"]} - {item["description"]}'
            if 'index' in item:
                msg += ' - Failed sample: ' + json.dumps(batch[int(item['index'])])
            messages.append(msg)
        if messages:
            raise AnodotAPIResponseException('\n'.join(messages))

    logger.info(f'Sent {len(batch)} records')
