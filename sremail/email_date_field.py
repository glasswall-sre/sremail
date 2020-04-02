"""email_date_field

Defines a Marshmallow field for an email date.

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime

from marshmallow.fields import Field


class EmailDate(Field):
    """A formatted email date (RFC2822).

    Example: Mon, 25 Nov 2019 14:59:32 UTC +0000

    Args:
        kwargs: The same kwargs that Field receives.

    See:
        https://tools.ietf.org/html/rfc2822.html#section-3.3
    """

    default_error_messages = {
        "invalid": "Not a valid {obj_type}",
        "format": "'{input}' cannot be formatted as a {obj_type}"
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def _serialize(self, value: datetime, attr, obj, **kwargs) -> str:
        if value is None:
            return None
        return format_datetime(value)

    def _deserialize(self, value: str, attr, data, **kwargs) -> datetime:
        return parsedate_to_datetime(value)