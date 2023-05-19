import calendar

import pendulum


def parse_month(month: str) -> tuple[str, str]:

    if month is None:
        start_date = pendulum.today().start_of("month")
        end_date = start_date.end_of("month")
    else:
        month = month.capitalize()
        today = pendulum.today()

        # Get the month number
        month_number = {v: k for k, v in enumerate(calendar.month_name)}[month]

        # Check if the input month is in the future and adjust the year accordingly
        year = today.year - 1 if today.month < month_number else today.year

        start_date = pendulum.date(year, month_number, 1).start_of("month")
        end_date = start_date.end_of("month")

    return start_date.to_date_string(), end_date.to_date_string()
