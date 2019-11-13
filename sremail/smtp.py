"""smtp.py

Methods for sending message.Message objects to SMTP servers.

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""

import smtplib
from typing import List

from .message import Message


def send(message: Message, smtp_url: str) -> None:
    """Send a Message to an SMTP server at a URL.

    Args:
        message (Message): The message to send.
        smtp_url (str): The SMTP server URL to send the message to.
    """
    with smtplib.SMTP(smtp_url) as smtp:
        smtp.send_message(message.as_mime())


def send_all(messages: List[Message], smtp_url: str) -> None:
    """Send a list of Messages to an SMTP server at a URL.

    Args:
        messages (List[Message]): The messages to send.
        smtp_url (str): The SMTP server URL to send the messages to.
    """
    with smtplib.SMTP(smtp_url) as smtp:
        for message in messages:
            smtp.send_message(message.as_mime())