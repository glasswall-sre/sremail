"""smtp.py

Methods for sending message.Message objects to SMTP servers.

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""

import smtplib
from typing import List, Optional

import aiosmtplib

from .message import Message


def connect(smtp_url: str, timeout: Optional[float] = None) -> smtplib.SMTP:
    """Connect to an SMTP server at a URL.

    Args:
        smtp_url (str): The SMTP server URL.
        timeout (float): The connection timeout in seconds. If not specified,
            the system default timeout will be used.
    """
    return smtplib.SMTP(smtp_url, timeout=timeout)


async def connect_async(smtp_url,
                        timeout: Optional[float] = None) -> aiosmtplib.SMTP:
    """Asynchronously connect to an SMTP server at a URL.

    Args:
        smtp_url (str): The SMTP server URL.
        timeout (float): The connection timeout in seconds. If not specified,
            the system default timeout will be used.
    """
    return await aiosmtplib.SMTP(smtp_url, timeout=timeout)


def send(message: Message, smtp_url: str,
         timeout: Optional[float] = None) -> None:
    """Send a Message to an SMTP server at a URL.

    Args:
        message (Message): The message to send.
        smtp_url (str): The SMTP server URL to send the message to.
        timeout (float): The timeout in seconds. If not specified then system
            default will be used.
    """
    with smtplib.SMTP(smtp_url, timeout=timeout) as smtp:
        smtp.send_message(message.as_mime())


async def send_async(message: Message,
                     smtp_url: str,
                     timeout: Optional[float] = None) -> None:
    """Asynchronously send a message to an SMTP server at a URL.

    Args:
        message (Message): The message to send.
        smtp_url (str): The SMTP server URL to send the message to.
        timeout (float): The timeout in seconds. If not specified then system
            default will be used.
    """
    await aiosmtplib.send(message.as_mime(),
                          hostname=smtp_url,
                          timeout=timeout)


def send_all(messages: List[Message], smtp_url: str) -> None:
    """Send a list of Messages to an SMTP server at a URL.

    Args:
        messages (List[Message]): The messages to send.
        smtp_url (str): The SMTP server URL to send the messages to.
    """
    with smtplib.SMTP(smtp_url) as smtp:
        for message in messages:
            smtp.send_message(message.as_mime())
