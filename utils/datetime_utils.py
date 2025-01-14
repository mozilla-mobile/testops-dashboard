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
