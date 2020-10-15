"""Address Class, AddressField

Store an email address, as in a MIME file
A marshmallow field for de/serialisation of Address objects

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""
from typing import Optional
from email.utils import parseaddr, formataddr
from marshmallow import fields


class Address:
    """Class to store an email address, as in a MIME file.

    Attributes:
        name (str): The real name of the email address. Can be empty.
        email (str): The email address.
    """
    def __init__(self, addr_str: str) -> None:
        """Create a new address from a string.

        Args:
            addr_str (str): The address. Can be "email@test.com",
            or "Firstname Lastname <email@test.com>"

        Raises:
            ValueError: If addr_str was in an incorrect format.
        """
        self.name, self.email = parseaddr(addr_str)

        if not self.name and not self.email:
            raise ValueError("Bad address given")

        if "@" not in self.email:
            raise ValueError("Email was not an email address")

    def __str__(self):
        return formataddr((self.name, self.email))

    def __repr__(self):
        return f"address.Address(\"{str(self)}\")"

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.email == other.email
        return False


class AddressField(fields.String):
    """A marshmallow field for de/serialisation of Address objects."""
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
