from contextlib import nullcontext as does_not_raise

import pytest

from sremail.address import Address


def create_address(email: str, name: str) -> Address:
    addr = Address.__new__(Address)
    addr.email = email
    addr.name = name
    return addr


@pytest.mark.parametrize("addr,expected,raises", [
    ("Sam Gibson <sgibson@glasswallsolutions.com>",
     create_address("sgibson@glasswallsolutions.com",
                    "Sam Gibson"), does_not_raise()),
    ("sgibson@glasswallsolutions.com",
     create_address("sgibson@glasswallsolutions.com", ""), does_not_raise()),
    ("Sam Gibson", None, pytest.raises(ValueError)),
    ("", None, pytest.raises(ValueError)),
    ("<>", None, pytest.raises(ValueError)),
],
                         ids=[
                             "Name and email", "Only email", "No email",
                             "Bad address", "Bad email"
                         ])
def test_address_create(addr, expected, raises):
    with raises:
        result = Address(addr)
        assert result == expected


@pytest.mark.parametrize(
    "addr_a, addr_b, expected",
    [(Address("Sam Gibson <sgibson@glasswallsolutions.com>"),
      Address("Sam Gibson <sgibson@glasswallsolutions.com>"), True),
     (Address("Sam Gibson <sgibson@glasswallsolutions.com>"),
      Address("sgibson@glasswallsolutions.com"), True),
     (Address("Sam Gibson <sgibson@glasswallsolutions.com>"),
      Address("different_email@email.com"), False)])
def test_address_eq(addr_a, addr_b, expected):
    assert (addr_a == addr_b) == expected


def test_address_str():
    address = "Sam Gibson <sgibson@glasswallsolutions.com>"
    result = str(Address(address))
    assert result == address


def test_address_repr():
    address = "Sam Gibson <sgibson@glasswallsolutions.com>"
    result = Address(address).__repr__()
    assert result == f"address.Address(\"{address}\")"