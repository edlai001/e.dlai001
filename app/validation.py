"""Input checks that mirror the limits in sql/schema.sql.

Oracle rejects values that break these limits with an error (e.g. ORA-12899),
which would reach the user as a 500 crash page. Checking first lets us return
a clear 400 message instead.
"""
import re
from datetime import datetime

from flask import jsonify

# Column sizes from sql/schema.sql (VARCHAR2(n)).
MAX_LEN = {
    'display_name': 100,
    'major': 100,
    'bio': 1000,
    'language': 50,
    'subject_name': 100,
    'level': 20,
    'goal': 50,
    'group_name': 100,
    'description': 500,
    'location_or_link': 300,
}

HH_MM = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
DATETIME_FORMAT = '%Y-%m-%d %H:%M'


def bad_request(message):
    return jsonify({'error': message}), 400


def check_lengths(values):
    """values: {field_name: value}. Returns a 400 response for the first value that
    is too long for its database column, or None when everything fits."""
    for field, value in values.items():
        if value is not None and len(str(value)) > MAX_LEN[field]:
            return bad_request(f'{field} must be at most {MAX_LEN[field]} characters')
    return None


def parse_datetime(value):
    """Parse 'YYYY-MM-DD HH:MM'. Returns a datetime, or None if the format is wrong."""
    try:
        return datetime.strptime(str(value), DATETIME_FORMAT)
    except ValueError:
        return None
