import anodot
import pytest
import requests

from datetime import datetime


@pytest.mark.parametrize('what,value,target_type,timestamp,dimensions,tags,version,dict_result', [
    ('test', 0, 'gauge', datetime.strptime('2020-01-01 00:00:00 +0000', '%Y-%m-%d %H:%M:%S %z'), {'te. st': 'test. 1'},
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
    ('test', '0.01', 'counter', datetime.strptime('2020-01-01 00:00:00 +0000', '%Y-%m-%d %H:%M:%S %z'), None, None, '2',
     {
         'value': 0.01,
         'timestamp': 1577836800.0,
         'properties': {
             'what': 'test',
             'ver': 2,
             'target_type': 'counter'
         }
     })
])
def test_metric20_to_dict(what, value, target_type, timestamp, dimensions, tags, version, dict_result):
    assert anodot.Metric20(what=what,
                           value=value,
                           target_type=anodot.TargetType(target_type),
                           timestamp=timestamp,
                           dimensions=dimensions,
                           tags=tags,
                           version=version).to_dict() == dict_result


@pytest.mark.parametrize('name,dimensions,measurements,missing_dim_policy,version,dict_result', [
    ('test1',
     ['te. st', 'test1  '],
     [anodot.Measurement('m. 1', anodot.Aggregation.SUM)],
     anodot.MissingDimPolicy(action=anodot.MissingDimPolicyAction.FILL, fill='tttt'),
     3,
     {
         'version': 3,
         'name': 'test1',
         'dimensions': ['te__st', 'test1__'],
         'measurements': {'m__1': {'aggregation': 'sum', 'countBy': 'none'}},
         'missingDimPolicy': {'action': 'fill', 'fill': 'tttt'}
     })
])
def test_schema_to_dict(name, dimensions, measurements, missing_dim_policy, version, dict_result):
    assert anodot.Schema(name, dimensions, measurements, missing_dim_policy, version=version).to_dict() == dict_result


@pytest.mark.parametrize('schema_id,timestamp,measurements,dimensions,tags,dict_result', [
    ('test',
     datetime.strptime('2020-01-01 00:00:00 +0000', '%Y-%m-%d %H:%M:%S %z'),
     {'m. 1': 3},
     {'te. st': 'test. 1'},
     {'ta. g': ['ta. g1', 'tag2']},
     {
         'schemaId': 'test',
         'timestamp': 1577836800.0,
         'dimensions': {'te__st': 'test__1'},
         'measurements': {'m__1': 3.0},
         'tags': {'ta__g': ['ta__g1', 'tag2']}
     })
])
def test_metric30_to_dict(schema_id, timestamp, measurements, dimensions, tags, dict_result):
    assert anodot.Metric30(schema_id, timestamp, measurements, dimensions, tags).to_dict() == dict_result


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

    @staticmethod
    def raise_for_status():
        return True


def test_send(monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, 'post', mock_post)
    with pytest.raises(anodot.AnodotAPIResponseException):
        anodot.send([anodot.Metric20('test', 0, anodot.TargetType.GAUGE, datetime.now()),
                     anodot.Metric20('test', 0, anodot.TargetType.GAUGE, datetime.now())],
                    token='token1234', base_url='https://app.anodot.com')
