"""setup.py

Used for installing sremail via pip.

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""
from setuptools import setup, find_packages

setup(
    dependency_links=[],
    install_requires=["marshmallow", "aiosmtplib"],
    name="sremail",
    version="#{TAG_NAME}#",
    description=
    "Python package to make it easier to send mail to SaaS clusters",
    author="Sam Gibson",
    author_email="sgibson@glasswallsolutions.com",
    packages=find_packages(),
)