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


def mime_headerize(s: str) -> str:
    """Convert a snake_cased string into a MIME header key.

    For example:
        reply_to -> Reply-To
    """
    parts = iter(s.split("_"))
    return "-".join(i.title() for i in parts)


class MessageHeadersSchema(Schema):
    """Marshmallow schema for validating MIME headers."""
    # TODO: add more as they are supported
    # field names here should be able to be converted to the correct MIME header
    # key using mime_headerize()
    date = fields.DateTime(format="iso", required=True)
    sender = AddressField()
    reply_to = fields.List(AddressField())
    to = fields.List(AddressField())
    cc = fields.List(AddressField())
    bcc = fields.List(AddressField())

    class Meta:
        # a bit of a hack... as 'from' is a python keyword, we need to declare
        # the from field here and alias it to attribute 'from_addresses'
        # meaning when creating a message you need to specify 'from' as
        # kwarg 'from_addresses'
        include = {
            "from":
            fields.List(AddressField(),
                        required=True,
                        attribute="from_addresses")
        }

    def on_bind_field(self, field_name, field_obj):
        """Convert data keys from snake_case to Mime-Header format."""
        field_obj.data_key = mime_headerize(field_obj.data_key or field_name)

    @validates_schema
    def validate_mandatory_fields(self, data, **kwargs):
        """Used for validating fields against each other."""
        if not data.get("to") and not data.get("bcc"):
            raise ValidationError("One of 'to', or 'bcc' must be supplied")


MESSAGE_HEADERS_SCHEMA = MessageHeadersSchema(unknown=INCLUDE)
"""Schema instance for validating message headers."""


class Message:
    """A MIME message.

    Attributes:
        headers (dict): The headers of the MIME message.
        attachments (List[email.message.Message]): MIME objects attached to the message.
    """
    def __init__(self, **headers) -> None:
        """Create a message, specifying headers as kwargs.

        For example::
            Message(to=["a@b.com"], date=datetime.now(), from_addresses=["c@d.com"])

        Headers kwarg names will be 'MIMEified', for example, 'reply_to' will be
        converted to 'Reply-To'.
        """
        # make sure the headers are valid
        validation_result = MESSAGE_HEADERS_SCHEMA.validate(
            MESSAGE_HEADERS_SCHEMA.dump(headers))
        if len(validation_result) > 0:
            raise ValueError(validation_result)

        dumped_headers = MESSAGE_HEADERS_SCHEMA.dump(headers)
        self.headers = dumped_headers
        self.attachments = []

    def attach(self, file_path: str) -> Message:
        """Attach a file to the message. 
        
        This method returns the object, so
        you can chain it like::
            msg.attach("file.pdf").attach("test.txt").attach("word.doc")

        Args:
            file_path (str): The path to the file to attach.

        Returns:
            Message: this Message, for chaining.
        """
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
        """Get this message as a Python standard library Message object.

        Returns:
            email.message.Message
        """
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
