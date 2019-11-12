from typing import Optional

from marshmallow import fields, validate, ValidationError

from email.utils import parseaddr, formataddr


class Address:
    """Class to store an email address, as in a MIME file.

    Attributes:
        name (str): The real name of the email address. Can be empty.
        email (str): The email address.
    """
    def __init__(self, addr_str: str) -> None:
        self.name, self.email = parseaddr(addr_str)

        if not self.name and not self.email:
            raise ValueError("Bad address given")

        if "@" not in self.email:
            raise ValueError("Email was not an email address")

    def __str__(self):
        return formataddr((self.name, self.email))

    def __repr__(self):
        return f"address.Address(\"{str(self)}\")"


class AddressField(fields.String):
    default_error_messages = {"invalid_address": "Not a valid address."}

    def _validated(self, value) -> Optional[Address]:
        if value is None:
            return None
        if isinstance(value, Address):
            return value
        try:
            return Address(value)
        except ValueError as err:
            raise self.make_error("invalid_address") from err

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:
        val = str(value) if value is not None else None
        return super()._serialize(val, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs) -> Optional[Address]:
        return self._validated(value)