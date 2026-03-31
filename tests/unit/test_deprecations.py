import contextlib
import warnings
from unittest import mock

import earthaccess
import pytest
import responses
from earthaccess.api import get_s3fs_session
from earthaccess.store import Store


@pytest.fixture(scope="session")
@responses.activate
@mock.patch("getpass.getpass")
@mock.patch("builtins.input")
def auth(user_input, user_password):
    user_input.return_value = "user"
    user_password.return_value = "password"
    json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}

    responses.add(
        responses.POST,
        "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
        json=json_response,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://urs.earthdata.nasa.gov/profile",
        json={"email_address": "test@test.edu"},
        status=200,
    )

    earthaccess.login(strategy="interactive")

    return earthaccess.__auth__


def test_deprecation_warning_for_api():
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")
        # Trigger a warning.
        with contextlib.suppress(Exception):
            get_s3fs_session()
        # Verify some things
        assert issubclass(w[0].category, DeprecationWarning)
        assert "Use get_s3_filesystem instead" in str(w[0].message)


def test_deprecation_warning_for_store(auth):
    store = Store(auth)
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")
        # Trigger a warning.
        with contextlib.suppress(ValueError):
            store.get_s3fs_session()
        # Verify some things
        assert issubclass(w[0].category, DeprecationWarning)
        assert "Use get_s3_filesystem instead" in str(w[0].message)


# ---------------------------------------------------------------------------
# Breaking-change assertions: removed names must not appear on the namespace
# ---------------------------------------------------------------------------


def test_open_virtual_mfdataset_removed_from_namespace() -> None:
    """open_virtual_mfdataset is no longer exported from earthaccess."""
    assert not hasattr(earthaccess, "open_virtual_mfdataset")


def test_open_virtual_dataset_removed_from_namespace() -> None:
    """open_virtual_dataset is no longer exported from earthaccess."""
    assert not hasattr(earthaccess, "open_virtual_dataset")


def test_consolidate_metadata_removed_from_namespace() -> None:
    """consolidate_metadata is no longer exported from earthaccess."""
    assert not hasattr(earthaccess, "consolidate_metadata")


def test_virtualize_present_on_namespace() -> None:
    """earthaccess.virtualize is the new primary virtual-dataset entry point."""
    assert hasattr(earthaccess, "virtualize")
    assert callable(earthaccess.virtualize)
