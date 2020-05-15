import json
import logging
import requests
import sys
import time
import urllib.parse

from datetime import datetime
from enum import Enum
from typing import Iterable

BATCH_SIZE = 1000
MAX_BATCH_DEBUG_OUTPUT = 10


def replace_illegal_chars(user_string: str):
    return user_string.replace(' ', '_').replace('.', '_')


def process_dimensions(dimensions: dict):
    if not dimensions:
        return {}

    if type(dimensions) is not dict:
        raise ValueError('dimensions should be dict')
    return {replace_illegal_chars(name): replace_illegal_chars(str(val)) for name, val in dimensions.items()}


def process_tags(tags: dict):
    if not tags:
        return {}

    if type(tags) is not dict:
        raise ValueError('tags should be dict')

    tags_result = {}
    for name, vals in tags.items():
        if type(vals) is not list:
            raise ValueError('Wrong tags format')
        tags_result[replace_illegal_chars(name)] = [replace_illegal_chars(str(val)) for val in vals]
    return tags_result


class TargetType(Enum):
    GAUGE = 'gauge'
    COUNTER = 'counter'


class Metric:
    def __init__(self, what: str,
                 value: float,
                 target_type: TargetType,
                 timestamp: datetime,
                 dimensions: dict = None,
                 tags: dict = None,
                 version: int = 1):
        """

        :param what: Name of your measurement
        :param value: Measurement value
        :param target_type: gauge (average aggregation) or counter (sum aggregation).
        :param timestamp: datetime object
        :param dimensions:
        :param tags:
        :param version: Metric version. (Change in case you want to create new metric)
        """

        self.what = replace_illegal_chars(str(what))
        self.value = float(value)
        self.target_type = TargetType(target_type).value
        self.timestamp = timestamp.timestamp()
        self.ver = int(version)
        self.dimensions = process_dimensions(dimensions)
        self.tags = process_tags(tags)

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


class AnodotAPIResponseException(Exception):
    pass


def send_request(batch: list,
                 logger: logging.Logger,
                 token: str,
                 base_url: str = 'https://app.anodot.com',
                 dry_run: bool = False):
    if len(batch) == 0:
        logger.info('Received empty batch')
        return

    logger.debug(f'Sending batch example: {str(batch[:MAX_BATCH_DEBUG_OUTPUT])}')
    if not dry_run:
        response = requests.post(urllib.parse.urljoin(base_url, '/api/v1/metrics'),
                                 params={'token': token, 'protocol': 'anodot20'},
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


def get_default_logger(level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


default_logger = get_default_logger()


def send(data: Iterable[Metric],
         token: str,
         logger: logging.Logger = None,
         base_url: str = 'https://app.anodot.com',
         dry_run: bool = False):
    """

    :param data: List of Metric objects
    :param token: Data collection token (https://support.anodot.com/hc/en-us/articles/360002631114#DataCollectionKey)
    :param logger: Logger object, if empty default_logger is used
    :param base_url: Base url for Anodot api
    :param dry_run:
    :return:
    """
    if not logger:
        logger = default_logger

    with requests.Session() as s:
        batch = []
        for item in data:
            batch.append(item.to_dict())
            if len(batch) == BATCH_SIZE:
                send_request(batch, logger, token, base_url, dry_run)
                batch = []

        send_request(batch, logger, token, base_url, dry_run)
