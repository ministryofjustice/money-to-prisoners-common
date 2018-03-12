from django.test import SimpleTestCase

from mtp_common.bank_accounts import (
    is_correspondence_account, roll_number_required, roll_number_valid_for_account
)


class CorrespondenceAccountTestCase(SimpleTestCase):

    def test_is_correspondence_account_any_account_number(self):
        self.assertTrue(
            is_correspondence_account('203253', '11112222')
        )
        self.assertTrue(
            is_correspondence_account('203253', '99999999')
        )

    def test_is_correspondence_account_with_account_number(self):
        self.assertTrue(
            is_correspondence_account('200353', '73152596')
        )

    def test_not_correspondence_account_different_account_number(self):
        self.assertFalse(
            is_correspondence_account('200353', '12341234')
        )


class RollNumberRequiredTestCase(SimpleTestCase):

    def test_roll_number_required_with_account_number(self):
        self.assertTrue(
            roll_number_required('403214', '10572780')
        )

    def test_roll_number_not_required_different_account_number(self):
        self.assertFalse(
            roll_number_required('403214', '12341234')
        )

    def test_roll_number_required_any_account_number(self):
        self.assertTrue(
            roll_number_required('134012', '12341234')
        )
        self.assertTrue(
            roll_number_required('134012', '11118888')
        )
        self.assertTrue(
            roll_number_required('134012', '00000000')
        )

    def test_roll_number_required_blank_account_number(self):
        self.assertTrue(
            roll_number_required('571327', '00000000')
        )


class RollNumberValidTestCase(SimpleTestCase):

    def test_roll_number_valid_with_account_number(self):
        self.assertTrue(
            roll_number_valid_for_account('403214', '10572780', 'AAA1234567BBB')
        )

    def test_roll_number_valid_any_account_number(self):
        self.assertTrue(
            roll_number_valid_for_account('134016', '12341234', '12345678901234')
        )

    def test_roll_number_invalid_with_account_number(self):
        self.assertFalse(
            roll_number_valid_for_account('403214', '10572780', 'notvalid')
        )

    def test_roll_number_invalid_any_account_number(self):
        self.assertFalse(
            roll_number_valid_for_account('134016', '12341234', 'notvalid')
        )
