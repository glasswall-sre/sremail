import builtins
import contextlib
from contextlib import nullcontext as does_not_raise
from datetime import datetime
import email
import io
from typing import Dict, List

import pytest

from sremail.message import Message, MIMEApplication


@pytest.fixture
def mock_open(monkeypatch):
    """Fixture used to mock open() to make sure tests don't write to the
    host filesystem."""
    files = {}

    @contextlib.contextmanager
    def mocked_open(filename, *args, **kwargs):
        file = io.StringIO(files.get(filename, ""))
        try:
            yield file
        finally:
            files[filename] = file.getvalue()
            file.close()

    monkeypatch.setattr(builtins, "open", mocked_open)


def create_message(headers: Dict[str, object],
                   attachments: List[MIMEApplication]) -> Message:
    msg = Message.__new__(Message)
    msg.headers = headers
    msg.attachments = attachments
    return msg


@pytest.mark.parametrize(
    "headers,expected,raises",
    [({
        "to": ["test@email.com"],
        "from_addresses": ["person@place.com"],
        "date":
        datetime.strptime("2019-11-12T15:24:28+00:00", "%Y-%m-%dT%H:%M:%S%z")
    },
      create_message(
          {
              "To": ["test@email.com"],
              "From": ["person@place.com"],
              "Date": "2019-11-12T15:24:28+00:00"
          }, []), does_not_raise()),
     ({
         "from_addresses": ["person@place.com"],
         "date":
         datetime.strptime("2019-11-12T15:24:28+00:00", "%Y-%m-%dT%H:%M:%S%z")
     }, None, pytest.raises(ValueError))],
    ids=["Success", "SchemaInvalidation"])
def test_create_message(headers, expected, raises):
    with raises:
        result = Message(**headers)
        print(result.__dict__)
        assert result == expected


def test_message_attach(mock_open):
    # write a test file to try to attach
    with open("attachment.txt", "w") as test_attachment:
        test_attachment.write("TEXT")

    msg = Message(to=["test@email.com"],
                  from_addresses=["test@email.com"],
                  date=datetime.now())

    msg.attach("attachment.txt")

    expected = MIMEApplication("TEXT", _subtype="txt")
    expected.add_header("content-disposition",
                        "attachment",
                        filename="attachment.txt")

    result = msg.attachments[0]

    assert result.get_content_type() == expected.get_content_type()
    assert result.get_content_disposition(
    ) == expected.get_content_disposition()
    assert result.get_payload() == expected.get_payload()


def test_as_mime(mock_open):
    # write a test file to try to attach
    with open("attachment.txt", "w") as test_attachment:
        test_attachment.write("TEXT")

    msg = Message(to=["test@email.com"],
                  from_addresses=["test@email.com"],
                  date=datetime.strptime("2019-11-12T16:48:25.773537",
                                         "%Y-%m-%dT%H:%M:%S.%f"))
    msg.attach("attachment.txt")

    # we need to set a boundary for the MIME message as it's not
    # very deterministic
    boundary = "===============8171060537750829823=="
    expected_str = f"""Content-Type: multipart/mixed; boundary="{boundary}"
MIME-Version: 1.0
Date: 2019-11-12T16:48:25.773537
To: test@email.com
From: test@email.com

--{boundary}
Content-Type: application/txt
MIME-Version: 1.0
Content-Transfer-Encoding: base64
content-disposition: attachment; filename="attachment.txt"

VEVYVA==

--{boundary}--
"""
    result = msg.as_mime()
    result.set_boundary(boundary)

    print(result)

    expected = email.message_from_string(expected_str)

    assert dict(result) == dict(expected)