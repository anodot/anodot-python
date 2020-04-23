import pytest
import requests

from anodot import metric
from datetime import datetime


@pytest.mark.parametrize('what,value,target_type,timestamp,dimensions,tags,version,dict_result', [
    ('test', 0, 'gauge', datetime.strptime('2020-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'), {'te. st': 'test. 1'},
     {'ta. g': ['ta. g1', 'tag2']}, 1, {
         'value': 0.0,
         'timestamp': 1577836800.0,
         'properties': {
             'what': 'test',
             'ver': 1,
             'target_type': 'gauge',
             'te__st': 'test__1'
         },
         'tags': {'ta__g': ['ta__g1', 'tag2']}
     }),
    ('test', '0.01', 'counter', datetime.strptime('2020-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'), None, None, '2', {
        'value': 0.01,
        'timestamp': 1577836800.0,
        'properties': {
            'what': 'test',
            'ver': 2,
            'target_type': 'counter'
        }
    })
])
def test_metric_to_dict(what, value, target_type, timestamp, dimensions, tags, version, dict_result):
    assert metric.Metric(what, value, metric.TargetType(target_type), timestamp, dimensions, tags,
                         version).to_dict() == dict_result


class MockResponse:
    @staticmethod
    def json():
        return {
            'errors': [
                {
                    'index': '1',
                    'error': '2028',
                    'description': 'Metric name length exceeded the maximum allowed: {xxx}'
                },
                {
                    'error': '2003',
                    'description': 'Metrics per seconds limit reached'
                }
            ]
        }


def test_send_request(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, 'post', mock_post)
    metric.send_request([{}, {}], metric.default_logger, 'token1234', 'https://app.anodot.com')
