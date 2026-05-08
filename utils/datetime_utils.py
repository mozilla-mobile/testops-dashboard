import pytz

from datetime import datetime, timedelta


format_date = "%Y-%m-%d"
format_datetime = '%Y-%m-%dT%H:%M:%S.%fZ'


class DatetimeUtils:

    def convert_datetime_to_epoch(str_date):
        str_to_dt = datetime.strptime(str_date, format_date)
        t = str_to_dt.timestamp()
        return int(t)

    def convert_epoch_to_datetime(int_epoch_date):
        ts = datetime.fromtimestamp(int_epoch_date)
        return ts.strftime(format_date)

    def convert_to_utc(datetime_str):
        """Convert datetime string with timezone offset to UTC."""
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        return dt.astimezone(pytz.UTC)

    def start_date(num_days, end_date=''):
        """ given num_days, calculate a start_date
        given an end_date (default: now), calculate a start date num_days
        number of days in the past.
        If num_days is empty, return a blank start date."""

        if num_days:
            n = int(num_days)
        else:
            return ''

        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, format_date)

        d = end_date - timedelta(days=n)
        return d.strftime(format_date)

    def parse_iso_timestamp(ts):
        if ts:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return None

    def delta_days(n):
        return timedelta(days=n)

    def delta_hours(n):
        return timedelta(hours=n)

    def delta_seconds(n):
        return timedelta(seconds=n)

    def create_date(year, month, day):
        return datetime(year, month, day)

    def parse_date(date_str: str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def resolve_date_range(start_date=None, end_date=None, num_days=None):
        """
        Resolve effective start/end dates using precedence:

        1. explicit start_date/end_date
        2. num_days rolling window
        3. default = Jan 1 current year -> today
        """

        today = datetime.now().date()

        # explicit range
        if start_date:
            if not end_date:
                end_date = today

            return (
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

        # rolling window
        if num_days:
            end = today
            start = end - timedelta(days=int(num_days))

            return (
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d")
            )

        # default: year-to-date
        start = datetime(today.year, 1, 1).date()

        return (
            start.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )