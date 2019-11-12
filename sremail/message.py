from __future__ import annotations  # to allow Message to return itself in methods...

import datetime
import email.message
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from os import path
from typing import List

from marshmallow import Schema, fields, validates_schema, ValidationError, INCLUDE

from .address import Address, AddressField


class MessageHeadersSchema(Schema):
    # TODO: add more as they are supported
    date = fields.DateTime(format="iso", required=True, data_key="Date")
    from_addresses = fields.List(AddressField(),
                                 required=True,
                                 data_key="From")
    sender = AddressField(data_key="Sender")
    reply_to = fields.List(AddressField(), data_key="Reply-To")
    to = fields.List(AddressField(), data_key="To")
    cc = fields.List(AddressField(), data_key="Cc")
    bcc = fields.List(AddressField(), data_key="Bcc")

    @validates_schema
    def validate_mandatory_fields(self, data, **kwargs):
        print("validating")
        if not data.get("to") and not data.get("bcc"):
            raise ValidationError("One of 'to', or 'bcc' must be supplied")


MESSAGE_HEADERS_SCHEMA = MessageHeadersSchema(unknown=INCLUDE)


class Message:
    attachments: List[MIMEApplication] = []

    def __init__(self, **headers) -> None:
        # make sure the headers are valid
        validation_result = MESSAGE_HEADERS_SCHEMA.validate(
            MESSAGE_HEADERS_SCHEMA.dump(headers))
        if len(validation_result) > 0:
            raise ValueError(validation_result)

        dumped_headers = MESSAGE_HEADERS_SCHEMA.dump(headers)
        self.headers = dumped_headers

    def attach(self, file_path: str) -> Message:
        with open(file_path, "rb") as attachment_file:
            ext = file_path.split(".")[-1:][0]
            mime_attachment = MIMEApplication(attachment_file.read(),
                                              _subtype=ext)
            mime_attachment.add_header("content-disposition",
                                       "attachment",
                                       filename=path.basename(file_path))
            self.attachments.append(mime_attachment)
        return self  # for chaining

    def as_mime(self) -> email.message.Message:
        mime_message = email.message.Message()
        mime_message.add_header("Content-Type", "multipart/mixed")
        mime_message.add_header("MIME-Version", "1.0")
        for key, val in self.headers.items():
            # make sure lists are joined up with commas
            if isinstance(val, list):
                joined_list = ", ".join(val)
                val = joined_list
            mime_message[key] = val

        for attachment in self.attachments:
            mime_message.attach(attachment)
        return mime_message

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.headers == other.headers and sorted(
                self.attachments) == sorted(other.attachments)
        return False
