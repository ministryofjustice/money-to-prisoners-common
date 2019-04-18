from django.utils.translation import gettext


def and_join(values):
    if not isinstance(values, list):
        values = list(values)
    if len(values) > 1:
        values = values[:-2] + [gettext('%s and %s') % (values[-2], values[-1])]
    return ', '.join(map(str, values))
