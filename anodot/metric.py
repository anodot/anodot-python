from datetime import datetime
from enum import Enum
from .tools import replace_illegal_chars, process_tags, process_dimensions, process_measurements
from typing import Iterable


class TargetType(Enum):
    GAUGE = 'gauge'
    COUNTER = 'counter'


class Metric:
    def to_dict(self) -> dict:
        pass


class Metric20(Metric):
    def __init__(
            self,
            what: str,
            value: float,
            target_type: TargetType,
            timestamp: datetime,
            dimensions: dict = None,
            tags: dict = None,
            version: int = 1,
    ):
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
        self.timestamp = int(timestamp.timestamp())
        self.ver = int(version)
        self.dimensions = process_dimensions(dimensions)
        self.tags = process_tags(tags)

    def __repr__(self):
        return str(self.__dict__)

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


class Aggregation(Enum):
    AVERAGE = 'average'
    SUM = 'sum'


class MissingDimPolicyAction(Enum):
    FILL = 'fill'
    FAIL = 'fail'
    IGNORE = 'ignore'


class MissingDimPolicy:
    def __init__(self, action: MissingDimPolicyAction, fill: str = None):
        self.action = action
        self.fill = fill

    def to_dict(self):
        val = {'action': self.action.value}
        if self.action == MissingDimPolicyAction.FILL:
            val['fill'] = self.fill

        return val

    @staticmethod
    def from_dict(data: dict) -> 'MissingDimPolicy':
        return MissingDimPolicy(
            MissingDimPolicyAction(data['action']),
            data.get('fill'),
        )

    def __eq__(self, other: 'MissingDimPolicy') -> bool:
        return self.action == other.action and self.fill == other.fill


class Measurement:
    def __init__(self, name: str, aggregation: Aggregation, units: str = None):
        self.name = name
        self.aggregation = aggregation
        self.units = units

    def to_dict(self):
        val = {'aggregation': self.aggregation.value, 'countBy': 'none'}
        if self.units:
            val['units'] = self.units

        return val

    def __eq__(self, other: 'Measurement') -> bool:
        return (
            self.name == other.name
            and self.aggregation == other.aggregation
            and self.units == other.units
        )


class Schema:
    def __init__(
            self,
            name: str,
            dimensions: Iterable[str],
            measurements: Iterable[Measurement],
            missing_dim_policy: MissingDimPolicy,
            version: int = 1,
            id_: str = None,
    ):
        self.id = id_
        self.name = name
        self.dimensions = dimensions
        self.measurements = measurements
        self.missing_dim_policy = missing_dim_policy
        self.version = version

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'name': self.name,
            'dimensions': [replace_illegal_chars(d) for d in self.dimensions],
            'measurements': {replace_illegal_chars(s.name): s.to_dict() for s in self.measurements},
            'missingDimPolicy': self.missing_dim_policy.to_dict(),
        }

    @staticmethod
    def from_dict(data: dict) -> 'Schema':
        return Schema(
            name=data['name'],
            dimensions=data['dimensions'],
            measurements=[
                Measurement(name, Aggregation(measurement['aggregation']))
                for name, measurement in data['measurements'].items()
            ],
            missing_dim_policy=MissingDimPolicy.from_dict(data['missingDimPolicy']),
            version=data.get('version', 1),
            id_=data.get('id'),
        )

    def __eq__(self, other: 'Schema') -> bool:
        return (
            self.name == other.name
            and self.dimensions == other.dimensions
            and self.measurements == other.measurements
            and self.missing_dim_policy == other.missing_dim_policy
        )


class Metric30(Metric):
    def __init__(
            self, schema_id: str,
            timestamp: datetime,
            measurements: dict,
            dimensions: dict = None,
            tags: dict = None,
    ):
        self.schema_id = schema_id
        self.timestamp = int(timestamp.timestamp())
        self.measurements = process_measurements(measurements)
        self.dimensions = process_dimensions(dimensions)
        self.tags = process_tags(tags)

    def __repr__(self):
        return str(self.__dict__)

    def to_dict(self):
        event = {
            'schemaId': self.schema_id,
            'timestamp': self.timestamp,
            'dimensions': self.dimensions,
            'measurements': self.measurements
        }

        if self.tags:
            event['tags'] = self.tags

        return event


class Watermark:
    def __init__(self, schema_id: str, timestamp: datetime):
        self.schema_id = schema_id
        self.timestamp = int(timestamp.timestamp())

    def to_dict(self):
        return {
            'schemaId': self.schema_id,
            'watermark': self.timestamp
        }
