from datetime import timedelta

from govuk_bank_holidays import bank_holidays


class WorkdayChecker:

    def __init__(self):
        self.holiday_checker = bank_holidays.BankHolidays()

    def is_workday(self, date):
        return (
            date.weekday() < 5 and
            not self.holiday_checker.is_holiday(date, division='england-and-wales')
        )

    def get_next_workday(self, date):
        next_day = date + timedelta(days=1)
        while not self.is_workday(next_day):
            next_day += timedelta(days=1)
        return next_day

    def get_previous_workday(self, date):
        previous_day = date - timedelta(days=1)
        while not self.is_workday(previous_day):
            previous_day -= timedelta(days=1)
        return previous_day
