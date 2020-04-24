[![Latest Release](https://img.shields.io/github/release/anodot/anodot-python.svg)](https://github.com/anodot/anodot-python/releases/latest)
[![Python versions](https://img.shields.io/pypi/pyversions/python-anodot)](https://pypi.org/project/python-anodot/)


# Anodot API python package

Install:
```
pip install python-anodot
```

### Posting metrics

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
    events.append(metric.Metric(what='packets_in',
                                value=event['packets_in'],
                                target_type=metric.TargetType.GAUGE,
                                timestamp=timestamp,
                                dimensions={'host': event['host'], 'region': event['region']},
                                tags={'tag_name': ['tag_value']},
                                version=VERSION))    
    events.append(metric.Metric(what='packets_out',
                                value=event['packets_out'],
                                target_type=metric.TargetType.GAUGE,
                                timestamp=timestamp,
                                dimensions={'host': event['host'], 'region': event['region']},
                                tags={'tag_name': ['tag_value']},
                                version=VERSION))       

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

metric.send(events, token='datacollectiontoken', logger=logger, base_url='https://app.anodot.com')
```

