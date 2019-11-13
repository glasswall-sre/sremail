import builtins
import contextlib
import io

import pytest


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