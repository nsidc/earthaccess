from pathlib import Path
from unittest.mock import patch

import earthaccess
import pytest


def fail_to_download_file(*args, **kwargs):
    raise IOError("Download failed")


def test_download_immediate_failure(tmp_path: Path):
    earthaccess.login()

    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-10, 20, 10, 50),
        temporal=("1999-02", "2019-03"),
        count=10,
    )

    with patch.object(earthaccess.__store__, "_download_file", fail_to_download_file):
        with pytest.raises(IOError, match="Download failed"):
            earthaccess.download(results, str(tmp_path))


def test_download_deferred_failure(tmp_path: Path):
    earthaccess.login()

    count = 3
    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-10, 20, 10, 50),
        temporal=("1999-02", "2019-03"),
        count=count,
    )

    with patch.object(earthaccess.__store__, "_download_file", fail_to_download_file):
        with pytest.raises(Exception) as exc_info:
            earthaccess.download(
                results,
                tmp_path,
                None,
                8,
                pqdm_kwargs={"exception_behaviour": "deferred"},
            )

    errors = exc_info.value.args
    assert len(errors) == count
    assert all(isinstance(e, IOError) and str(e) == "Download failed" for e in errors)
