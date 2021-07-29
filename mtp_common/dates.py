from govuk_bank_holidays import bank_holidays


class WorkdayChecker:
    def __init__(self):
        self.holidays = bank_holidays.BankHolidays()

    def is_workday(self, date):
        return self.holidays.is_work_day(date, division=bank_holidays.BankHolidays.ENGLAND_AND_WALES)

    def get_next_workday(self, date):
        return self.holidays.get_next_work_day(date=date, division=bank_holidays.BankHolidays.ENGLAND_AND_WALES)

    def get_previous_workday(self, date):
        return self.holidays.get_prev_work_day(date=date, division=bank_holidays.BankHolidays.ENGLAND_AND_WALES)
