import base64
from contextlib import nullcontext as does_not_raise
from datetime import datetime
import email
import io
from typing import Dict, List

import pytest

from sremail.message import Message, MIMEApplication, MIMEText


def create_message(body: str, headers: Dict[str, object],
                   attachments: List[MIMEApplication]) -> Message:
    msg = Message.__new__(Message)
    msg.body = body
    msg.headers = headers
    msg.attachments = attachments
    return msg


@pytest.mark.parametrize(
    "body,headers,expected,raises",
    [("", {
        "to": ["test@email.com"],
        "from_addresses": ["person@place.com"],
        "date":
        datetime.strptime("2019-11-12T15:24:28+00:00", "%Y-%m-%dT%H:%M:%S%z")
    },
      create_message(
          "", {
              "to": ["test@email.com"],
              "from_addresses": ["person@place.com"],
              "date":
              datetime.strptime("2019-11-12T15:24:28+00:00",
                                "%Y-%m-%dT%H:%M:%S%z")
          }, []), does_not_raise()),
     ("", {
         "from_addresses": ["person@place.com"],
         "date":
         datetime.strptime("2019-11-12T15:24:28+00:00", "%Y-%m-%dT%H:%M:%S%z")
     }, None, pytest.raises(ValueError)),
     ("Hello world", {
         "to": ["test@email.com"],
         "from_addresses": ["person@place.com"],
         "date":
         datetime.strptime("2019-11-12T15:24:28+00:00", "%Y-%m-%dT%H:%M:%S%z")
     },
      create_message(
          "Hello world", {
              "to": ["test@email.com"],
              "from_addresses": ["person@place.com"],
              "date":
              datetime.strptime("2019-11-12T15:24:28+00:00",
                                "%Y-%m-%dT%H:%M:%S%z")
          }, []), does_not_raise())],
    ids=["SuccessNoBody", "SchemaInvalidation", "SuccessWithBody"])
def test_create_message(body, headers, expected, raises):
    with raises:
        result = Message(body, **headers)
        print(result.headers)
        assert result == expected


def test_create_message_unknown_headers():
    result = Message(to=["test@email.com"],
                     from_addresses=["a@b.com"],
                     date=datetime.now(),
                     unknown_header="test")
    mime_result = result.as_mime()
    assert mime_result["Unknown-Header"] == "test"


def test_add_header():
    result = Message(to=["test@email.com"],
                     from_addresses=["a@b.com"],
                     date=datetime.now())
    result.headers["X-FileTrust-Tenant"] = "test"
    mime_result = result.as_mime()
    assert mime_result["X-FileTrust-Tenant"] == "test"


def test_with_headers():
    result = Message.with_headers({
        "To": ["sgibson@glasswallsolutions.com"],
        "Date": "Mon, 25 Nov 2019 14:59:32 UTC +0000",
        "From": ["sgibson@glasswallsolutions.com"]
    })
    assert result.headers == {
        "To": ["sgibson@glasswallsolutions.com"],
        "Date": "Mon, 25 Nov 2019 14:59:32 UTC +0000",
        "From": ["sgibson@glasswallsolutions.com"]
    }


def test_message_attach(mock_open):
    # write a test file to try to attach
    with open("attachment.txt", "w") as test_attachment:
        test_attachment.write("TEXT")

    msg = Message(to=["test@email.com"],
                  from_addresses=["test@email.com"],
                  date=datetime.now())

    msg.attach("attachment.txt")

    expected = MIMEText("TEXT\n")
    expected.add_header("content-disposition",
                        "attachment",
                        filename="attachment.txt")

    result = msg.attachments[0]

    assert result.get_content_type() == expected.get_content_type()
    assert result.get_content_disposition() == \
        expected.get_content_disposition()
    assert result.get_payload() == expected.get_payload()


def test_message_attach_stream():
    byte_stream = io.BytesIO(b"testing testing 123")

    msg = Message(to=["test@email.com"],
                  from_addresses=["test@email.com"],
                  date=datetime.now())
    msg.attach_stream(byte_stream, "test.bin")

    expected = MIMEApplication(b"testing testing 123")
    expected.add_header("content-disposition",
                        "attachment",
                        filename="test.bin")

    result = msg.attachments[0]

    assert result.get_content_type() == expected.get_content_type()
    assert result.get_content_disposition() == \
        expected.get_content_disposition()
    assert result.get_payload() == expected.get_payload()


def test_message_attach_stream_unknown_mime():
    byte_stream = io.BytesIO(b"testing testing 123")

    msg = Message(to=["test@email.com"],
                  from_addresses=["test@email.com"],
                  date=datetime.now())
    msg.attach_stream(byte_stream, "test.coff")

    expected = MIMEApplication(b"testing testing 123")
    expected.add_header("content-disposition",
                        "attachment",
                        filename="test.coff")

    result = msg.attachments[0]

    assert result.get_content_type() == expected.get_content_type()
    assert result.get_content_disposition() == \
        expected.get_content_disposition()
    assert result.get_payload() == expected.get_payload()


def test_as_mime(mock_open):
    # write a test file to try to attach
    with open("attachment.txt", "w") as test_attachment:
        test_attachment.write("TEXT")

    msg = Message(body="Hello, world!",
                  to=["test@email.com"],
                  from_addresses=["test@email.com"],
                  date=datetime.strptime("2019-11-12T15:24:28+00:00",
                                         "%Y-%m-%dT%H:%M:%S%z"))
    msg.attach("attachment.txt")

    # we need to set a boundary for the MIME message as it's not
    # very deterministic
    boundary = "===============8171060537750829823=="
    expected_str = f"""Content-Type: multipart/mixed; boundary="{boundary}"
MIME-Version: 1.0
From: test@email.com
To: test@email.com
Date: Tue, 12 Nov 2019 15:24:28 +0000

--{boundary}
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Hello, world!
--{boundary}
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="attachment.txt"

TEXT

--{boundary}--
"""
    result = msg.as_mime()
    result.set_boundary(boundary)

    expected = email.message_from_string(expected_str)

    assert dict(result) == dict(expected)
    result_payload = result.get_payload()[0]
    expected_payload = expected.get_payload()[0]
    print(result)
    assert result_payload.get_payload() == \
        expected_payload.get_payload()
    assert result_payload.get_content_type() == \
        expected_payload.get_content_type()
    assert result_payload.get_content_disposition() == \
        expected_payload.get_content_disposition()
