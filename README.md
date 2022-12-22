[![Latest Release](https://img.shields.io/github/release/anodot/anodot-python.svg)](https://github.com/anodot/anodot-python/releases/latest)
[![Python versions](https://img.shields.io/pypi/pyversions/python-anodot)](https://pypi.org/project/python-anodot/)


# Anodot API python package

Install:
```
pip install python-anodot
```


### Posting metrics

More about the flow and protocols you can read here [Posting metrics with Anodot API](https://docs.anodot.com/#post-metrics)

#### Note:
- All dots and spaces in measurement names and in dimensions are replaced with an underscore `_`
- When you pass more than 1000 events to the `anodot.send` function they are splitted into chuncks before sending
- Events should be sorted by timestamp in the ascending order


#### Protocol 2.0
```python
import anodot
import logging
import sys

from datetime import datetime

data = [
    {"time": "2020-01-01 00:00:00", "packets_in": 100, "packets_out": 120, "host": "host134", "region": "region1"},
    {"time": "2020-01-01 00:01:00", "packets_in": 163, "packets_out": 130, "host": "host126", "region": "region1"},
    {"time": "2020-01-01 00:02:00", "packets_in": 215, "packets_out": 140, "host": "host101", "region": "region2"}
]

VERSION = 1

events = []
for event in data:
    timestamp = datetime.strptime(event['time'], '%Y-%m-%d %H:%M:%S')
    events.append(
        anodot.Metric20(
            what='packets_in',
            value=event['packets_in'],
            target_type=anodot.TargetType.GAUGE,
            timestamp=timestamp,
            dimensions={'host': event['host'], 'region': event['region']},
            tags={'tag_name': ['tag_value']},
            version=VERSION,
        )
    )
    events.append(
        anodot.Metric20(
            what='packets_out',
            value=event['packets_out'],
            target_type=anodot.TargetType.GAUGE,
            timestamp=timestamp,
            dimensions={'host': event['host'], 'region': event['region']},
            tags={'tag_name': ['tag_value']},
            version=VERSION,
        )
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

anodot.send(events, token='datacollectiontoken', logger=logger, base_url='https://app.anodot.com')
```

#### Protocol 3.0
```python
import anodot
import logging
import sys

from datetime import datetime

data = [
    {"time": "2020-01-01 00:00:00", "packets_in": 100, "packets_out": 120, "host": "host134", "region": "region1"},
    {"time": "2020-01-01 00:01:00", "packets_in": 163, "packets_out": 130, "host": "host126", "region": "region1"},
    {"time": "2020-01-01 00:02:00", "packets_in": 215, "packets_out": 140, "host": "host101", "region": "region2"}
]

VERSION = 1

api_client = anodot.ApiClient('accesskeyhere', base_url='https://app.anodot.com')
schema = api_client.create_schema(
    anodot.Schema(
        name='new_schema',
        dimensions=['host', 'region'],
        measurements=[
            anodot.Measurement('packets_in', anodot.Aggregation.AVERAGE),
            anodot.Measurement('packets_out', anodot.Aggregation.AVERAGE),
        ],
        missing_dim_policy=anodot.MissingDimPolicy(action=anodot.MissingDimPolicyAction.FAIL),
        version=VERSION,
    )
)

events = []
for event in data:
    timestamp = datetime.strptime(event['time'], '%Y-%m-%d %H:%M:%S')
    events.append(
        anodot.Metric30(
            schema_id=schema['schema']['id'],
            measurements={"packets_in": event['packets_in'], "packets_out": event['packets_out']},
            timestamp=timestamp,
            dimensions={'host': event['host'], 'region': event['region']},
            tags={'tag_name': ['tag_value']},
        )
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

anodot.send(
    events,
    token='datacollectiontoken',
    logger=logger,
    base_url='https://app.anodot.com',
    protocol=anodot.Protocol.ANODOT30,
)

anodot.send_watermark(
    anodot.Watermark(
        schema_id=schema['schema']['id'],
        timestamp=datetime.strptime('2020-01-01 00:03:00', '%Y-%m-%d %H:%M:%S'),
    ),
    token='datacollectiontoken',
    logger=logger,
    base_url='https://app.anodot.com',
)
```

### Posting metrics (for package version <2.0)

Example

```python
import logging
import sys

from anodot import metric
from datetime import datetime

data = [
    {"time": "2020-01-01 00:00:00", "packets_in": 100, "packets_out": 120, "host": "host134", "region": "region1"},
    {"time": "2020-01-01 00:01:00", "packets_in": 163, "packets_out": 130, "host": "host126", "region": "region1"},
    {"time": "2020-01-01 00:02:00", "packets_in": 215, "packets_out": 140, "host": "host101", "region": "region2"}
]

VERSION = 1

events = []
for event in data:
    timestamp = datetime.strptime(event['time'], '%Y-%m-%d %H:%M:%S')
    events.append(
        metric.Metric(
            what='packets_in',
            value=event['packets_in'],
            target_type=metric.TargetType.GAUGE,
            timestamp=timestamp,
            dimensions={'host': event['host'], 'region': event['region']},
            tags={'tag_name': ['tag_value']},
            version=VERSION
        )
    )
    events.append(
        metric.Metric(
            what='packets_out',
            value=event['packets_out'],
            target_type=metric.TargetType.GAUGE,
            timestamp=timestamp,
            dimensions={'host': event['host'], 'region': event['region']},
            tags={'tag_name': ['tag_value']},
            version=VERSION
        )
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

metric.send(events, token='datacollectiontoken', logger=logger, base_url='https://app.anodot.com')
```

