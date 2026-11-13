from unittest import mock

from django.core import signing
from django.test import SimpleTestCase

from mtp_common.private_estate_downloads import DEFAULT_RETENTION_SECONDS, PREFIX, SALT, issue_token, read_token


class PrivateEstateDownloadTokenTestCase(SimpleTestCase):
    path = PREFIX + '2026-11-13/PR1/random/payment.csv'
    key = 'a-test-signing-key'

    @mock.patch('mtp_common.private_estate_downloads.time.time', return_value=1000)
    def test_valid_token_identifies_the_file(self, clock):
        token = issue_token(self.path, self.key, 28 * 24 * 60 * 60)
        self.assertEqual(read_token(token, self.key), self.path)

    @mock.patch('mtp_common.private_estate_downloads.time.time', return_value=1000)
    def test_expiry_is_fixed_at_issue_time(self, clock):
        token = issue_token(self.path, self.key, 30)
        clock.return_value = 1029
        self.assertEqual(read_token(token, self.key), self.path)
        clock.return_value = 1030
        with self.assertRaises(signing.BadSignature):
            read_token(token, self.key)

    @mock.patch('mtp_common.private_estate_downloads.time.time', return_value=1000)
    def test_tampered_token_and_wrong_key_are_rejected(self, clock):
        token = issue_token(self.path, self.key, 30)
        with self.assertRaises(signing.BadSignature):
            read_token(token + 'x', self.key)
        with self.assertRaises(signing.BadSignature):
            read_token(token, 'another-key')

    def test_cannot_issue_unscoped_or_unlimited_token(self):
        for path, key, lifetime in (('emails/other/file', self.key, 60), (self.path, '', 60),
                                    (self.path, self.key, 0), (self.path, self.key, True),
                                    (self.path, self.key, DEFAULT_RETENTION_SECONDS + 1)):
            with self.subTest(path=path, key=key, lifetime=lifetime):
                with self.assertRaises(ValueError):
                    issue_token(path, key, lifetime)

    def test_lifetime_can_match_the_object_retention_period(self):
        token = issue_token(self.path, self.key, DEFAULT_RETENTION_SECONDS)
        self.assertEqual(read_token(token, self.key), self.path)

    def test_longer_configured_retention_allows_a_longer_link(self):
        lifetime = 90 * 86400
        token = issue_token(self.path, self.key, lifetime, retention_seconds=lifetime)
        self.assertEqual(read_token(token, self.key), self.path)

    def test_signed_tokens_with_invalid_payloads_are_rejected(self):
        for payload in ({'path': 'emails/other/file', 'expires': 9999999999},
                        {'path': self.path, 'expires': True}, {'path': self.path}, []):
            with self.subTest(payload=payload):
                token = signing.dumps(payload, key=self.key, salt=SALT)
                with self.assertRaises(signing.BadSignature):
                    read_token(token, self.key)
