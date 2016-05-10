from django.utils.crypto import get_random_string


def generate_tokens(**kwargs):
    """
    Returns a dict with random access_token and refresh_token.
    Whatever is passed via kwargs will be added or replace
    dict values.
    """
    defaults = {
        'access_token': get_random_string(length=30),
        'refresh_token': get_random_string(length=30)
    }
    defaults.update(kwargs)
    return defaults
