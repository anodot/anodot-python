import json
import logging
import requests
import sys
import urllib.parse

from enum import Enum
from typing import Iterable

BATCH_SIZE = 1000


def replace_illegal_chars(user_string: str):
    return user_string.replace(' ', '_').replace('.', '_')


def process_dimensions(dimensions: dict):
    if type(dimensions) is not dict:
        raise ValueError('dimensions should be dict')
    return {replace_illegal_chars(name): replace_illegal_chars(str(val)) for name, val in dimensions.items()}


def process_tags(tags: dict):
    if type(tags) is not dict:
        raise ValueError('tags should be dict')

    tags_result = {}
    for name, vals in tags.items():
        if type(vals) is not list:
            raise ValueError('Wrong tags format')
        tags_result[replace_illegal_chars(name)] = [replace_illegal_chars(str(val)) for val in vals]


class TargetType(Enum):
    GAUGE = 'gauge'
    COUNTER = 'counter'


class Metric:
    def __init__(self, what: str,
                 value,
                 target_type: TargetType,
                 timestamp: int,
                 dimensions: dict = None,
                 tags: dict = None,
                 version: int = 1):

        try:
            self.what = replace_illegal_chars(str(what))
            self.value = float(value)
            self.target_type = TargetType(target_type).value
            self.timestamp = int(timestamp)
            self.ver = int(version)
            self.dimensions = process_dimensions(dimensions)
            self.tags = process_tags(tags)
        except ValueError as e:
            raise EventConstructException(e)

    def to_dict(self):
        event = {
            'value': self.value,
            'timestamp': self.timestamp,
            'properties': {
                'what': self.what,
                'ver': self.ver,
                'target_type': self.target_type,
                **self.dimensions
            }
        }
        if self.tags:
            event['tags'] = self.tags
        return event


class EventConstructException(Exception):
    pass


def send_request(batch: list, logger: logging.Logger, token: str, base_url: str = 'https://app.anodot.com'):
    if len(batch) == 0:
        logger.info('Received empty batch')
        return

    try:
        logger.debug(f'Sending batch: {str(batch)}')
        response = requests.post(urllib.parse.urljoin(base_url, '/api/v1/metrics'),
                                 params={'token': token, 'protocol': 'anodot20'},
                                 json=batch)
        logger.info(f'Sent {len(batch)} records')
        response_data = response.json()
        for item in response_data['errors']:
            msg = f'{item["error"]} - {item["description"]}'
            if 'index' in item:
                msg += ' - Failed sample: ' + json.dumps(batch[item['index']])
            logger.error(msg)
    except requests.HTTPError as e:
        logger.exception(e)


def get_default_logger(level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


default_logger = get_default_logger()


def send(data: Iterable[Metric], token: str, logger: logging.Logger = None, base_url: str = 'https://app.anodot.com'):
    if not logger:
        logger = default_logger

    batch = []
    for item in data:
        batch.append(item.to_dict())
        if len(batch) == BATCH_SIZE:
            send_request(batch, logger, token, base_url)
            batch = []

    send_request(batch, logger, token, base_url)
