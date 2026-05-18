"""Unit tests for earthaccess.virtual.

Covers the high-level public API:
  - virtualize()
  - open_virtual() (str, DataCollection, load, force_external paths)
  - DataCollection.virtual_collection_url() / get_s3_credentials()

All external I/O is mocked so the suite runs without network access or
optional heavy dependencies.
"""

from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from earthaccess.results import DataCollection, DataGranule

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_granules(n: int = 1, base_url: str = "s3://bucket/file") -> list[DataGranule]:
    granules = []
    for i in range(n):
        g = MagicMock()
        g.data_links.return_value = [f"{base_url}_{i}.nc"]
        g.__getitem__ = MagicMock(
            side_effect=lambda key, i=i: {
                "meta": {
                    "collection-concept-id": f"C{i}-PODAAC",
                    "provider-id": "PODAAC",
                },
            }[key],
        )
        granules.append(g)
    return cast("list[DataGranule]", granules)


def _patch_internals(mock_vds: MagicMock | None = None):
    """Return the two patches used by most virtualize() tests."""
    if mock_vds is None:
        mock_vds = MagicMock()
    return (
        patch(
            "earthaccess.virtual.core.build_obstore_registry",
            return_value=MagicMock(),
        ),
        patch(
            "earthaccess.virtual.core._open_virtual_mfdataset",
            return_value=mock_vds,
        ),
    )


# ---------------------------------------------------------------------------
# virtualize
# ---------------------------------------------------------------------------


def test_virtualize_empty_granules_raises() -> None:
    from earthaccess.virtual.core import virtualize

    with pytest.raises(ValueError, match=r"[Nn]o granules"):
        virtualize([])


def test_virtualize_multi_granule_no_concat_dim_raises() -> None:
    from earthaccess.virtual.core import virtualize

    with (
        patch(
            "earthaccess.virtual.core.build_obstore_registry",
            return_value=MagicMock(),
        ),
        pytest.raises(ValueError, match="concat_dim"),
    ):
        virtualize(_make_granules(2))


def test_virtualize_invalid_parser_string_raises() -> None:
    from earthaccess.virtual.core import virtualize

    with pytest.raises(ValueError, match="BadParser"):
        virtualize(_make_granules(1), parser="BadParser")


def test_virtualize_load_false_returns_virtual_dataset() -> None:
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with (
        reg_patch,
        open_patch,
        patch("earthaccess.virtual.core._load_via_kerchunk") as mock_load,
    ):
        result = virtualize(_make_granules(1), load=False)

    assert result is mock_vds
    mock_load.assert_not_called()


def test_virtualize_load_true_delegates_to_kerchunk(tmp_path) -> None:
    from earthaccess.virtual.core import virtualize

    expected_ds = MagicMock()
    reg_patch, open_patch = _patch_internals()
    with (
        reg_patch,
        open_patch,
        patch(
            "earthaccess.virtual.core._load_via_kerchunk",
            return_value=expected_ds,
        ) as mock_load,
    ):
        result = virtualize(
            _make_granules(1),
            load=True,
            reference_dir=str(tmp_path),
        )

    mock_load.assert_called_once()
    assert result is expected_ds


def test_virtualize_dmrpp_fallback_emits_user_warning() -> None:
    from earthaccess.virtual.core import virtualize

    mock_vds_hdf = MagicMock()
    call_count = {"n": 0}

    def side_effect(*args, **kwargs):  # noqa: ARG001
        call_count["n"] += 1
        if call_count["n"] == 1:
            msg = "no .dmrpp sidecar"
            raise FileNotFoundError(msg)
        return mock_vds_hdf

    with (
        patch(
            "earthaccess.virtual.core.build_obstore_registry",
            return_value=MagicMock(),
        ),
        patch(
            "earthaccess.virtual.core._open_virtual_mfdataset",
            side_effect=side_effect,
        ),
        pytest.warns(UserWarning, match="HDFParser"),
    ):
        result = virtualize(_make_granules(1), parser="DMRPPParser")

    assert result is mock_vds_hdf
    assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# open_virtual — str URL routing
# ---------------------------------------------------------------------------


def test_open_virtual_unrecognised_uri_raises() -> None:
    from earthaccess.virtual.core import open_virtual

    with pytest.raises(ValueError, match="Unrecognised"):
        open_virtual("data.nc")


def test_open_virtual_icechunk_delegates(tmp_path) -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()
    icechunk_path = tmp_path / "store.icechunk"
    icechunk_path.write_text("")

    with patch(
        "earthaccess.virtual.core._open_icechunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual(str(icechunk_path))

    mock_open.assert_called_once_with(str(icechunk_path), storage_options=None)
    assert result is mock_ds


def test_open_virtual_kerchunk_json_delegates() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_kerchunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual("refs.json")

    mock_open.assert_called_once_with("refs.json", storage_options=None)
    assert result is mock_ds


def test_open_virtual_kerchunk_parquet_delegates() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_kerchunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual("refs.parquet", storage_options={"key": "val"})

    mock_open.assert_called_once_with(
        "refs.parquet",
        storage_options={"key": "val"},
    )
    assert result is mock_ds


def test_open_virtual_forwards_storage_options_to_icechunk(tmp_path) -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()
    icechunk_path = tmp_path / "store.icechunk"
    icechunk_path.write_text("")
    opts = {"some": "option"}

    with patch(
        "earthaccess.virtual.core._open_icechunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual(
            str(icechunk_path),
            storage_options=opts,
        )

    mock_open.assert_called_once_with(str(icechunk_path), storage_options=opts)
    assert result is mock_ds


# ---------------------------------------------------------------------------
# DataCollection — virtual_collection_url / get_s3_credentials
# ---------------------------------------------------------------------------


def test_collection_virtual_url_found() -> None:
    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "https://example.com/refs.json",
                        "Type": "GET DATA",
                        "Subtype": "VIRTUAL COLLECTION",
                    },
                    {
                        "URL": "https://example.com/data.nc",
                        "Type": "GET DATA",
                    },
                ],
            },
        },
    )
    assert collection.virtual_collection_url() == "https://example.com/refs.json"


def test_collection_virtual_url_not_found() -> None:
    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "https://example.com/data.nc",
                        "Type": "GET DATA",
                    },
                ],
            },
        },
    )
    assert collection.virtual_collection_url() is None


def test_collection_virtual_url_no_related_urls() -> None:
    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {},
        },
    )
    assert collection.virtual_collection_url() is None


def test_collection_get_s3_credentials() -> None:
    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "DirectDistributionInformation": {
                    "S3CredentialsAPIEndpoint": "https://example.com/s3credentials",
                    "Region": "us-west-2",
                },
            },
        },
    )
    mock_creds = {
        "accessKeyId": "AKIA...",
        "secretAccessKey": "secret...",
        "sessionToken": "token...",
    }
    with patch(
        "earthaccess.results.earthaccess.__auth__",
        autospec=True,
    ) as mock_auth:
        mock_auth.get_s3_credentials.return_value = mock_creds
        result = collection.get_s3_credentials()

    mock_auth.get_s3_credentials.assert_called_once_with(
        endpoint="https://example.com/s3credentials",
    )
    assert result == mock_creds


def test_collection_get_s3_credentials_no_endpoint() -> None:
    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "DirectDistributionInformation": {
                    "Region": "us-west-2",
                },
            },
        },
    )
    with pytest.raises(ValueError, match="S3CredentialsAPIEndpoint"):
        collection.get_s3_credentials()


# ---------------------------------------------------------------------------
# open_virtual — DataCollection
# ---------------------------------------------------------------------------


def test_open_virtual_with_collection_kerchunk() -> None:
    from earthaccess.virtual.core import open_virtual

    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "https://example.com/refs.json",
                        "Type": "GET DATA",
                        "Subtype": "VIRTUAL COLLECTION",
                    },
                ],
            },
        },
    )
    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_kerchunk_from_collection",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual(collection)

    mock_open.assert_called_once_with(
        collection, "https://example.com/refs.json", access="indirect"
    )
    assert result is mock_ds


def test_open_virtual_with_collection_icechunk() -> None:
    from earthaccess.virtual.core import open_virtual

    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "s3://bucket/store.icechunk",
                        "Type": "GET DATA",
                        "Subtype": "VIRTUAL COLLECTION",
                    },
                ],
            },
        },
    )
    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_icechunk_from_collection",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual(collection, access="direct")

    mock_open.assert_called_once_with(
        collection, "s3://bucket/store.icechunk", access="direct"
    )
    assert result is mock_ds


def test_open_virtual_with_collection_no_virtual_url() -> None:
    from earthaccess.virtual.core import open_virtual

    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {},
        },
    )
    with pytest.raises(ValueError, match="VIRTUAL COLLECTION"):
        open_virtual(collection)


# ---------------------------------------------------------------------------
# open_virtual — str path still works
# ---------------------------------------------------------------------------


def test_open_virtual_str_path_still_works_after_refactor() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_kerchunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual("refs.parquet")

    mock_open.assert_called_once_with("refs.parquet", storage_options=None)
    assert result is mock_ds


# ---------------------------------------------------------------------------
# open_virtual — load=False (VirtualiZarr path)
# ---------------------------------------------------------------------------


def test_open_virtual_load_false_url() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_virtual_via_virtualizarr",
        return_value=mock_ds,
    ) as mock_vz:
        result = open_virtual("https://example.com/refs.json", load=False)

    assert mock_vz.called
    assert result is mock_ds


def test_open_virtual_load_false_collection() -> None:
    from earthaccess.virtual.core import open_virtual

    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "https://example.com/refs.json",
                        "Type": "GET DATA",
                        "Subtype": "VIRTUAL COLLECTION",
                    },
                ],
            },
        },
    )
    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_virtual_via_virtualizarr",
        return_value=mock_ds,
    ) as mock_vz:
        result = open_virtual(collection, load=False)

    assert mock_vz.called
    assert result is mock_ds


def test_open_virtual_load_false_external_url() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_virtual_via_virtualizarr",
        return_value=mock_ds,
    ) as mock_vz:
        result = open_virtual(
            "https://its-live-data.s3-us-west-2.amazonaws.com/test-space/vds/SPL4SMGP.parquet",
            load=False,
        )

    assert mock_vz.called
    assert result is mock_ds


def test_open_virtual_load_true_default_still_works() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_kerchunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual("refs.parquet")

    mock_open.assert_called_once_with("refs.parquet", storage_options=None)
    assert result is mock_ds


# ---------------------------------------------------------------------------
# open_virtual — force_external
# ---------------------------------------------------------------------------


def test_open_virtual_force_external_url() -> None:
    from earthaccess.virtual.core import open_virtual

    remote_url = "https://example.com/data/refs.json"
    mock_session = MagicMock()
    mock_session.storage_options = {
        "client_kwargs": {"headers": {"Authorization": "Bearer x"}}
    }
    mock_ds = MagicMock()

    with (
        patch(
            "earthaccess.virtual.core._sanitize_references_for_external",
            return_value="/tmp/external_refs.json",
        ) as mock_sanitize,
        patch(
            "earthaccess.virtual.core._open_kerchunk",
            return_value=mock_ds,
        ) as mock_open,
        patch(
            "earthaccess.get_fsspec_https_session",
            return_value=mock_session,
        ),
    ):
        result = open_virtual(remote_url, force_external=True)

    mock_sanitize.assert_called_once_with(remote_url)
    mock_open.assert_called_once_with(
        "/tmp/external_refs.json",
        storage_options={
            "remote_protocol": "https",
            "remote_options": mock_session.storage_options,
        },
    )
    assert result is mock_ds


def test_open_virtual_force_external_with_collection() -> None:
    from earthaccess.virtual.core import open_virtual

    collection = DataCollection(
        {
            "meta": {"concept-id": "C1234-PROV"},
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "https://example.com/data/refs.json",
                        "Type": "GET DATA",
                        "Subtype": "VIRTUAL COLLECTION",
                    },
                ],
            },
        },
    )
    mock_session = MagicMock()
    mock_session.storage_options = {
        "client_kwargs": {"headers": {"Authorization": "Bearer x"}}
    }
    mock_ds = MagicMock()

    with (
        patch(
            "earthaccess.virtual.core._sanitize_references_for_external",
            return_value="/tmp/external_refs.json",
        ) as mock_sanitize,
        patch(
            "earthaccess.virtual.core._open_kerchunk",
            return_value=mock_ds,
        ) as mock_open,
        patch(
            "earthaccess.get_fsspec_https_session",
            return_value=mock_session,
        ),
    ):
        result = open_virtual(collection, force_external=True)

    mock_sanitize.assert_called_once_with("https://example.com/data/refs.json")
    mock_open.assert_called_once_with(
        "/tmp/external_refs.json",
        storage_options={
            "remote_protocol": "https",
            "remote_options": mock_session.storage_options,
        },
    )
    assert result is mock_ds


def test_open_virtual_force_external_does_not_affect_plain_string() -> None:
    from earthaccess.virtual.core import open_virtual

    mock_ds = MagicMock()

    with patch(
        "earthaccess.virtual.core._open_kerchunk",
        return_value=mock_ds,
    ) as mock_open:
        result = open_virtual("refs.parquet")

    mock_open.assert_called_once_with("refs.parquet", storage_options=None)
    assert result is mock_ds


# ---------------------------------------------------------------------------
# homogenize_dataset_codec_level — data integrity after patching
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level", [1, 6, 7, 9])
def test_zlib_decompression_is_level_independent(level: int) -> None:
    """Zlib decompression produces the same result regardless of the level param.

    Data compressed at level 6 must decompress correctly with any level in
    the codec config.  This validates that patching Zlib levels in
    ManifestArray metadata is safe.
    """
    import numcodecs
    import numpy as np

    original = np.array([1.0, np.nan, 3.0, -999.0, 42.5], dtype="f8")
    compressed = numcodecs.Zlib(level=6).encode(original.tobytes())

    result = np.frombuffer(
        numcodecs.Zlib(level=level).decode(compressed),
        dtype="f8",
    )
    assert np.allclose(original, result, equal_nan=True), (
        f"Mismatch at Zlib level {level}"
    )
