def replace_illegal_chars(user_string: str):
    return user_string.replace(' ', '_').replace('.', '_')


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


def process_dimensions(dimensions: dict):
    if not dimensions:
        return {}

    if type(dimensions) is not dict:
        raise ValueError('dimensions should be dict')
    return {replace_illegal_chars(name): replace_illegal_chars(str(val)) for name, val in dimensions.items()}


def process_measurements(measurements: dict):
    if not measurements:
        return {}

    if type(measurements) is not dict:
        raise ValueError('measurements should be dict')
    return {replace_illegal_chars(name): float(val) for name, val in measurements.items()}
