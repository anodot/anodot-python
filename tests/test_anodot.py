import pytest

from anodot.metric import Metric, TargetType
from datetime import datetime


@pytest.mark.parametrize('what,value,target_type,timestamp,dimensions,tags,version,dict_result', [
    ('test', 0, 'gauge', datetime.strptime('2020-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'), {'te. st': 'test. 1'},
     {'ta. g': ['ta. g1', 'tag2']}, 1, {
        'value': 0.0,
        'timestamp': 1577829600.0,
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
        'timestamp': 1577829600.0,
        'properties': {
            'what': 'test',
            'ver': 2,
            'target_type': 'counter'
        }
    })
])
def test_metric_create_object(what, value, target_type, timestamp, dimensions, tags, version, dict_result):
    assert Metric(what, value, TargetType(target_type), timestamp, dimensions, tags, version).to_dict() == dict_result
