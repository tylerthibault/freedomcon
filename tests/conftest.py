import os
import pytest

# Must be set before importing the app so SECRET_KEY is deterministic
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("FORCE_HTTPS", "false")


@pytest.fixture(scope="session")
def client():
    from run import create_app

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
