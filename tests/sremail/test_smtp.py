"""
smtp test module
"""
from datetime import datetime
import email
import smtplib

import pytest

from sremail.message import Message
from sremail import smtp


@pytest.fixture
def mock_smtp(monkeypatch):
    """

    Args:
        monkeypatch:

    Returns:
        monkeypatch: Object
    """
    class MockSMTP:
        """
        Creates a mock smtp
        """
        def __init__(self, *args, **kwargs):
            pass

        @staticmethod
        def send_message(message):
            print(message)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)


def test_send_message(mock_smtp, mock_open, capsys):
    """

    Args:
        mock_smtp:
        mock_open:
        capsys:

    Returns:

    """
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
Date: Tue, 12 Nov 2019 16:48:25 -0000
To: test@email.com
From: test@email.com

--{boundary}
Content-Type: text/plain
MIME-Version: 1.0
content-disposition: attachment; filename="attachment.txt"

TEXT

--{boundary}--
"""
    expected = email.message_from_string(expected_str)

    smtp.send(msg, "smtp.test.not_real.com:25")

    captured = capsys.readouterr()
    result_after_send = email.message_from_string(captured.out)
    result_after_send.set_boundary(boundary)

    assert dict(result_after_send) == dict(expected)
    result_payload = result_after_send.get_payload()[0]
    expected_payload = expected.get_payload()[0]
    assert result_payload.get_payload() == \
        expected_payload.get_payload()
    assert result_payload.get_content_type() == \
        expected_payload.get_content_type()
    assert result_payload.get_content_disposition() == \
        expected_payload.get_content_disposition()


def test_send_messages(mock_smtp, mock_open, capsys):
    # write a test file to try to attach
    with open("attachment.txt", "w") as test_attachment:
        test_attachment.write("TEXT")

    msgs = []
    for _ in range(0, 5):
        msg = Message(to=["test@email.com"],
                      from_addresses=["test@email.com"],
                      date=datetime.strptime("2019-11-12T16:48:25.773537",
                                             "%Y-%m-%dT%H:%M:%S.%f"))
        msg.attach("attachment.txt")
        msgs.append(msg)

    # we need to set a boundary for the MIME message as it's not
    # very deterministic
    boundary = "===============8171060537750829823=="
    expected_str = f"""Content-Type: multipart/mixed; boundary="{boundary}"
MIME-Version: 1.0
Date: Tue, 12 Nov 2019 16:48:25 -0000
To: test@email.com
From: test@email.com

--{boundary}
Content-Type: text/plain
MIME-Version: 1.0
Content-Transfer-Encoding: base64
content-disposition: attachment; filename="attachment.txt"

TEXT

--{boundary}--
"""
    expected = email.message_from_string(expected_str)

    smtp.send_all(msgs, "smtp.test.not_real.com:25")

    captured = capsys.readouterr()
    for message in captured.out.split("--\n\n"):
        if len(message.strip()) == 0:
            continue

        result_after_send = email.message_from_string(message.strip())
        result_after_send.set_boundary(boundary)

        assert dict(result_after_send) == dict(expected)
        result_payload = result_after_send.get_payload()[0]
        expected_payload = expected.get_payload()[0]
        assert result_payload.get_payload() == \
            expected_payload.get_payload()
        assert result_payload.get_content_type() == \
            expected_payload.get_content_type()
        assert result_payload.get_content_disposition() == \
            expected_payload.get_content_disposition()
