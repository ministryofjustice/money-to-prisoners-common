"""
This module is used to look up prisoners in HMPPS Prisoner Search.

Prisoner Search holds a copy of each prisoner's current details, so it can answer "where is this prisoner now?"
without calling Prison API (i.e. NOMIS). It uses the same HMPPS Auth client credentials as `mtp_common.nomis`,
but the client needs a Prisoner Search role (e.g. ROLE_PRISONER_SEARCH) to be granted in HMPPS Auth.
"""

from urllib.parse import quote_plus

from django.conf import settings

from mtp_common.nomis import Connector

# Prisoner Search uses these pseudo-prison codes for prisoners who are not currently in an establishment
RELEASED_PRISON_ID = 'OUT'
IN_TRANSFER_PRISON_ID = 'TRN'


class PrisonerSearchConnector(Connector):
    """
    Connector for HMPPS Prisoner Search (using HMPPS Auth).
    Shares the cached HMPPS Auth token with `mtp_common.nomis.Connector` since the same client credentials are used.
    """

    @property
    def base_url(self):
        return settings.HMPPS_OFFENDER_SEARCH_BASE_URL

    def can_access_prisoner_search(self):
        """
        :return: True if this connector has all keys in place to connect to Prisoner Search.
        """
        return all(
            getattr(settings, key, None)
            for key in (
                'HMPPS_CLIENT_ID',
                'HMPPS_CLIENT_SECRET',
                'HMPPS_AUTH_BASE_URL',
                'HMPPS_OFFENDER_SEARCH_BASE_URL',
            )
        )


connector = PrisonerSearchConnector()


def can_access_prisoner_search():
    return connector.can_access_prisoner_search()


def get_prisoner(prisoner_number, retries=2, session=None):
    """
    :return: the Prisoner Search record for this prisoner.
    :raises requests.HTTPError: e.g. with status 404 if Prisoner Search does not know the prisoner.
    """
    return connector.get(
        '/prisoner/{prisoner_number}'.format(
            prisoner_number=quote_plus(prisoner_number)
        ),
        retries=retries,
        session=session,
    )


def get_location(prisoner_number, retries=2, session=None):
    """
    Replaces `mtp_common.nomis.get_location`, returning the prisoner's current establishment.

    :return: dict with `nomis_id` and `name` of the prison, plus `cell_location` (e.g. 'A-1-002') when known,
        or None if Prisoner Search has no prison for this prisoner.
        Released prisoners have nomis_id `RELEASED_PRISON_ID` ('OUT'),
        those being transferred have nomis_id `IN_TRANSFER_PRISON_ID` ('TRN').
    :raises requests.RequestException: e.g. requests.HTTPError with status 404 if the prisoner is not known.
    """
    result = get_prisoner(prisoner_number, retries=retries, session=session)
    prison_id = result.get('prisonId')
    if not prison_id:
        return None
    location = {
        'nomis_id': prison_id,
        'name': result.get('prisonName') or prison_id,
    }
    if result.get('cellLocation'):
        location['cell_location'] = result['cellLocation']
    return location
