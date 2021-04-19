import logging

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('mtp')

# rejection reason categories where the stored value is user-specified text
# NB: you cannot remove keys as they will have been persisted in the database,
#     instead remove fields from the form in noms-ops as necessary
CHECK_REJECTION_TEXT_CATEGORY_LABELS = {
    'fiu_investigation_id': _('Associated FIU investigation'),
    'intelligence_report_id': _('Associated intelligence report (IR)'),
    'other_reason': _('Other reason'),
}
# rejection reason categories where the stored value is simply `True`
# NB: you cannot remove keys as they will have been persisted in the database,
#     instead remove fields from the form in noms-ops as necessary
CHECK_REJECTION_BOOL_CATEGORY_LABELS = {
    'payment_source_paying_multiple_prisoners': _('Payment source is paying multiple prisoners'),
    'payment_source_multiple_cards': _('Payment source is using multiple cards'),
    'payment_source_linked_other_prisoners': _('Payment source is linked to other prisoner/s'),
    'payment_source_known_email': _('Payment source is using a known email'),
    'payment_source_unidentified': _('Payment source is unidentified'),
    'prisoner_multiple_payments_payment_sources': _('Prisoner has multiple payments or payment sources'),
}

# all known security check rejection reason categories
CHECK_REJECTION_CATEGORIES = (
    frozenset(CHECK_REJECTION_TEXT_CATEGORY_LABELS) | frozenset(CHECK_REJECTION_BOOL_CATEGORY_LABELS)
)


def human_readable_check_rejection_reasons(rejection_reasons: dict) -> list:
    """
    Turns the DB representation of a security check's rejection reasons into a list of human-readable descriptions
    """
    descriptions = []
    if not rejection_reasons:
        # in case None is persisted in older records
        return descriptions
    for key, value in rejection_reasons.items():
        if key in CHECK_REJECTION_TEXT_CATEGORY_LABELS:
            descriptions.append(f'{CHECK_REJECTION_TEXT_CATEGORY_LABELS[key]}: {value}')
        elif key in CHECK_REJECTION_BOOL_CATEGORY_LABELS:
            if value:
                descriptions.append(f'{CHECK_REJECTION_BOOL_CATEGORY_LABELS[key]}')
            if value is not True:
                logger.error('Security check rejection bool category is not True')
        else:
            logger.error('Security check has unknown rejection category')
            descriptions.append(f'{key}: {value}')
    return descriptions
