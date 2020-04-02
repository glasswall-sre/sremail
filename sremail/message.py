from __future__ import annotations  # to allow Message to return itself in methods...

import datetime
import email.message
from email.message import EmailMessage, MIMEPart
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import IOBase
import mimetypes
from os import path
from typing import List, Union

from marshmallow import Schema, fields, validates_schema, post_dump, pre_dump,\
    ValidationError, INCLUDE

from .address import Address, AddressField
from .email_date_field import EmailDate


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
    date = EmailDate(required=True)
    sender = AddressField()
    reply_to = fields.List(AddressField())
    to = fields.List(AddressField())
    cc = fields.List(AddressField())
    bcc = fields.List(AddressField())

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cached_unknown_fields = {}

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
        unknown = INCLUDE

    def on_bind_field(self, field_name, field_obj):
        """Convert data keys from snake_case to Mime-Header format."""
        field_obj.data_key = mime_headerize(field_obj.data_key or field_name)

    @validates_schema
    def validate_mandatory_fields(self, data, **kwargs):
        """Used for validating fields against each other."""
        if not data.get("to") and not data.get("bcc"):
            raise ValidationError("One of 'to', or 'bcc' must be supplied")

    @pre_dump()
    def cache_unknown_fields(self, data, **kwargs):
        """Cache any fields that were unknown, so we can dump them later on."""
        field_names = [
            field.attribute or field.name for field in self.fields.values()
        ]
        self.cached_unknown_fields.clear()
        for k, v in data.items():
            if k not in field_names:
                self.cached_unknown_fields[k] = v
        return data

    @post_dump()
    def dump_unknown_fields(self, data, **kwargs):
        """Add the unknown fields to the dumped output."""
        for k, v in self.cached_unknown_fields.items():
            new_key = mime_headerize(k)
            data[new_key] = v
        return data


MESSAGE_HEADERS_SCHEMA = MessageHeadersSchema(unknown=INCLUDE)
"""Schema instance for validating message headers."""


class Message:
    """A MIME message.

    Attributes:
        headers (dict): The headers of the MIME message.
        attachments (List[email.message.Message]): MIME objects attached to the message.
    """
    def __init__(self, body: str = "", **headers) -> None:
        """Create a message, specifying headers as kwargs.

        MUST use headers ('to' OR 'bcc') AND 'date' AND 'from_addresses'.

        For example::
            Message(to=["a@b.com"], date=datetime.now(), from_addresses=["c@d.com"])

        Headers kwarg names will be 'MIMEified', for example, 'reply_to' will be
        converted to 'Reply-To'.

        Args:
            body: The plaintext body of the email.
            kwargs: The headers.
        """
        # make sure the headers are valid
        validation_result = MESSAGE_HEADERS_SCHEMA.validate(
            MESSAGE_HEADERS_SCHEMA.dump(headers))
        if len(validation_result) > 0:
            raise ValueError(validation_result)

        self.headers = headers
        self.body = body
        self.attachments = []

    @classmethod
    def with_headers(cls, headers: dict, body: str = "") -> Message:
        """Create a new MIME message with given headers. This allows you to
        create a message using raw headers.

        MUST use headers ('To' OR 'Bcc') AND 'Date' AND 'From'.

        Example::
            msg = Message.with_headers({
                "To": ["sgibson@glasswallsolutions.com"],
                "Date": datetime.now(),
                "From": ["sgibson@glasswallsolutions.com"]
            })

        This exists because when creating a message with a constructor it's
        expecting the headers as kwargs, i.e. Message(to=[...], date="") etc.
        
        This comes into the constructor as a dict with keys "to", "date" and so on,
        and is converted (MIMEified) into MIME headers with keys "To" and "Date"
        inside the MessageHeadersSchema. Keys here will be expecting Python-native
        types, for example "date" will be expecting a datetime.

        The limitations of this approach come when you want to let users specify
        headers in a config file (for example), whereby you are unable to supply 
        Python-native types, and must do some level of conversion beforehand to 
        get the user specified header values to play nice with the constructor.

        Instead of doing the conversion, you could just trust the user to put
        headers in the correct format, supply the raw headers to 
        Message.with_headers() and be done with it.

        Args:
            headers (dict): The raw headers to put on the Message.
            body (str): The body of the Message.

        Returns:
            Message: The created Message object.
        """
        self = cls.__new__(cls)
        self.headers = headers
        self.body = body
        self.attachments = []
        return self

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
            return self.attach_stream(attachment_file, file_path)

    def attach_stream(self, stream: IOBase, file_name: str) -> Message:
        """Read a stream into an attachment and attach to this message.

        This method returns the object, so
        you can chain it like::
            msg.attach(file_handle, "test.txt").attach(byte_stream, "test.bin")

        Args:
            stream (IOBase): The stream to read from.
            file_name (str): The name of the file, used for MIME type identification.

        Returns:
            Message: this Message, for chaining.
        """
        mime_type = mimetypes.guess_type(file_name)[0]
        main_type, sub_type = mime_type.split("/")
        attachment = MIMEPart()

        # we need special handling for set_content with datatype of str, as
        # for some reason this method doesn't like 'maintype'
        # see: https://docs.python.org/3/library/email.contentmanager.html#email.contentmanager.set_content
        content_args = {"subtype": sub_type}
        if main_type != "text":
            content_args["maintype"] = main_type
        file_name = path.basename(file_name)
        attachment.set_content(stream.read(),
                               filename=file_name,
                               disposition="attachment",
                               **content_args)
        self.attachments.append(attachment)
        return self

    def as_mime(self) -> email.message.Message:
        """Get this message as a Python standard library Message object.

        Returns:
            email.message.Message
        """
        mime_message = email.message.Message()
        mime_message.add_header("Content-Type", "multipart/mixed")
        mime_message.add_header("MIME-Version", "1.0")
        dumped_headers = MESSAGE_HEADERS_SCHEMA.dump(self.headers)
        for key, val in dumped_headers.items():
            # make sure lists are joined up with commas
            if isinstance(val, list):
                joined_list = ", ".join(val)
                val = joined_list
            mime_message[key] = val

        # add the body if it exists
        if self.body:
            mime_message.attach(MIMEText(self.body))

        # now the attachments
        for attachment in self.attachments:
            mime_message.attach(attachment)

        return mime_message

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.body == other.body and \
                self.headers == other.headers and sorted(
                self.attachments) == sorted(other.attachments)
        return False
