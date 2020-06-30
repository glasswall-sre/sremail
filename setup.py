"""setup.py

Used for installing sremail via pip.

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""
from setuptools import setup, find_packages


def repo_file_as_string(file_path: str) -> str:
    with open(file_path, "r") as repo_file:
        return repo_file.read()


setup(dependency_links=[],
      install_requires=["marshmallow", "aiosmtplib"],
      name="sremail",
      version="#{VERSION}#",
      description="Python package to make it easier to handle email.",
      long_description=repo_file_as_string("README.md"),
      long_description_content_type="text/markdown",
      author="Sam Gibson",
      author_email="sgibson@glasswallsolutions.com",
      packages=find_packages(),
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Topic :: Communications :: Email",
          "Topic :: Software Development :: Libraries"
      ],
      python_requires=">=3.6",
      url="https://github.com/glasswall-sre/sremail")
