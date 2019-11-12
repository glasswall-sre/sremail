import datetime
from email.message import EmailMessage
from typing import List

from marshmallow import Schema, fields, validates_schema, ValidationError, INCLUDE

from .address import Address, AddressField


class MessageHeadersSchema(Schema):
    # TODO: add more as they are supported
    Date = fields.DateTime(format="iso", required=True, data_key="Date")
    From = fields.List(AddressField(), required=True, data_key="From")
    Sender = AddressField(data_key="Sender")
    ReplyTo = fields.List(AddressField(), data_key="Reply-To")
    to_addresses = fields.List(AddressField(), data_key="To")
    cc_addresses = fields.List(AddressField(), data_key="Cc")
    bcc_addresses = fields.List(AddressField(), data_key="Bcc")

    @validates_schema
    def validate_mandatory_fields(self, data, **kwargs):
        if not data.get("to_addresses") and not data.get("bcc_addresses"):
            raise ValidationError("One of 'To', or 'Bcc' must be supplied")


MESSAGE_HEADERS_SCHEMA = MessageHeadersSchema(unknown=INCLUDE)


class Message:
    def __init__(self, **headers) -> None:
        # make sure the headers are valid
        header_validation_result = MESSAGE_HEADERS_SCHEMA.validate(headers)
        if len(header_validation_result) > 0:
            raise ValueError(header_validation_result)
        self.headers = headers
