"""Unit tests for earthaccess.virtual.core.virtualize().

TDD-first: tests define the contract before the implementation exists.

All external I/O (obstore, VirtualiZarr, NASA APIs) is mocked so the suite
runs without network access or optional heavy dependencies.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_granules(n: int = 1, base_url: str = "s3://bucket/file") -> list[MagicMock]:
    granules = []
    for i in range(n):
        g = MagicMock()
        g.data_links.return_value = [f"{base_url}_{i}.nc"]
        g.__getitem__ = MagicMock(
            side_effect=lambda key, i=i: {
                "meta": {
                    "collection-concept-id": f"C{i}-PODAAC",
                    "provider-id": "PODAAC",
                }
            }[key]
        )
        granules.append(g)
    return granules


def _patch_internals(mock_vds: MagicMock | None = None):
    """Context manager that patches the heavy internals used by virtualize()."""
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
# Input validation
# ---------------------------------------------------------------------------


def test_virtualize_empty_granules_raises() -> None:
    """virtualize() raises ValueError when granules list is empty."""
    from earthaccess.virtual.core import virtualize

    with pytest.raises(ValueError, match="[Nn]o granules"):
        virtualize([])


def test_virtualize_multi_granule_no_concat_dim_raises() -> None:
    """virtualize() raises ValueError for >1 granule without concat_dim."""
    from earthaccess.virtual.core import virtualize

    reg_patch = patch(
        "earthaccess.virtual.core.build_obstore_registry", return_value=MagicMock()
    )
    with reg_patch:
        with pytest.raises(ValueError, match="concat_dim"):
            virtualize(_make_granules(2))


def test_virtualize_single_granule_without_concat_dim_is_ok() -> None:
    """virtualize() accepts a single granule without concat_dim."""
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        result = virtualize(_make_granules(1))
    assert result is mock_vds


def test_virtualize_invalid_parser_string_raises() -> None:
    """virtualize() raises ValueError for an unrecognised parser string."""
    from earthaccess.virtual.core import virtualize

    with pytest.raises(ValueError, match="BadParser"):
        virtualize(_make_granules(1), parser="BadParser")


# ---------------------------------------------------------------------------
# Return value — load=False (default)
# ---------------------------------------------------------------------------


def test_virtualize_load_false_returns_virtual_dataset() -> None:
    """virtualize(load=False) returns the raw virtual dataset."""
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        with patch("earthaccess.virtual.core._load_via_kerchunk") as mock_load:
            result = virtualize(_make_granules(1), load=False)

    assert result is mock_vds
    mock_load.assert_not_called()


# ---------------------------------------------------------------------------
# Return value — load=True (kerchunk round-trip)
# ---------------------------------------------------------------------------


def test_virtualize_load_true_calls_to_kerchunk(tmp_path) -> None:
    """virtualize(load=True) calls vds.virtualize.to_kerchunk()."""
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    expected_ds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        with patch(
            "earthaccess.virtual.core._load_via_kerchunk",
            return_value=expected_ds,
        ) as mock_load:
            result = virtualize(
                _make_granules(1), load=True, reference_dir=str(tmp_path)
            )

    mock_load.assert_called_once()
    assert result is expected_ds


def test_virtualize_load_true_reopens_with_xarray(tmp_path) -> None:
    """virtualize(load=True) delegates to _load_via_kerchunk which reopens with xarray."""
    from earthaccess.virtual.core import virtualize

    expected_ds = MagicMock()
    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        with patch(
            "earthaccess.virtual.core._load_via_kerchunk",
            return_value=expected_ds,
        ):
            result = virtualize(
                _make_granules(1), load=True, reference_dir=str(tmp_path)
            )

    assert result is expected_ds


def test_virtualize_load_true_uses_json_by_default(tmp_path) -> None:
    """virtualize(load=True) passes reference_format='json' to _load_via_kerchunk."""
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        with patch(
            "earthaccess.virtual.core._load_via_kerchunk",
            return_value=MagicMock(),
        ) as mock_load:
            virtualize(_make_granules(1), load=True, reference_dir=str(tmp_path))

    _, kwargs = mock_load.call_args
    assert kwargs.get("reference_format", "json") == "json"


def test_virtualize_load_true_parquet_format(tmp_path) -> None:
    """virtualize(load=True, reference_format='parquet') passes parquet to _load_via_kerchunk."""
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        with patch(
            "earthaccess.virtual.core._load_via_kerchunk",
            return_value=MagicMock(),
        ) as mock_load:
            virtualize(
                _make_granules(1),
                load=True,
                reference_dir=str(tmp_path),
                reference_format="parquet",
            )

    _, kwargs = mock_load.call_args
    assert kwargs.get("reference_format") == "parquet"


# ---------------------------------------------------------------------------
# DMR++ fallback
# ---------------------------------------------------------------------------


def test_virtualize_dmrpp_fallback_emits_user_warning() -> None:
    """When DMR++ sidecars are missing, virtualize() warns and retries with HDFParser."""
    from earthaccess.virtual.core import virtualize

    mock_vds_hdf = MagicMock()
    reg_mock = MagicMock()

    call_count = {"n": 0}

    def side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise FileNotFoundError("no .dmrpp sidecar")
        return mock_vds_hdf

    with patch(
        "earthaccess.virtual.core.build_obstore_registry", return_value=reg_mock
    ):
        with patch(
            "earthaccess.virtual.core._open_virtual_mfdataset", side_effect=side_effect
        ):
            with pytest.warns(UserWarning, match="HDFParser"):
                result = virtualize(_make_granules(1), parser="DMRPPParser")

    assert result is mock_vds_hdf
    assert call_count["n"] == 2


def test_virtualize_explicit_hdf_no_fallback_warning() -> None:
    """No UserWarning emitted when parser='HDFParser' is set explicitly."""
    from earthaccess.virtual.core import virtualize

    mock_vds = MagicMock()
    reg_patch, open_patch = _patch_internals(mock_vds)
    with reg_patch, open_patch:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            virtualize(_make_granules(1), parser="HDFParser")

    fallback_warnings = [x for x in w if "HDFParser" in str(x.message)]
    assert len(fallback_warnings) == 0


# ---------------------------------------------------------------------------
# Parameter forwarding
# ---------------------------------------------------------------------------


def test_virtualize_concat_dim_forwarded() -> None:
    """concat_dim is forwarded to _open_virtual_mfdataset."""
    from earthaccess.virtual.core import virtualize

    reg_patch, open_patch = _patch_internals()
    with reg_patch, open_patch as mock_open:
        virtualize(_make_granules(2), concat_dim="time")

    _, kwargs = mock_open.call_args
    assert kwargs["concat_dim"] == "time"


def test_virtualize_xr_combine_kwargs_forwarded() -> None:
    """Extra kwargs (coords, compat, combine_attrs) are forwarded."""
    from earthaccess.virtual.core import virtualize

    reg_patch, open_patch = _patch_internals()
    with reg_patch, open_patch as mock_open:
        virtualize(
            _make_granules(2),
            concat_dim="time",
            coords="minimal",
            compat="override",
            combine_attrs="override",
        )

    _, kwargs = mock_open.call_args
    assert kwargs["coords"] == "minimal"
    assert kwargs["compat"] == "override"
    assert kwargs["combine_attrs"] == "override"


def test_virtualize_preprocess_forwarded() -> None:
    """Preprocess callable is forwarded to _open_virtual_mfdataset."""
    from earthaccess.virtual.core import virtualize

    def my_preprocess(ds):
        return ds

    reg_patch, open_patch = _patch_internals()
    with reg_patch, open_patch as mock_open:
        virtualize(_make_granules(1), preprocess=my_preprocess)

    _, kwargs = mock_open.call_args
    assert kwargs["preprocess"] is my_preprocess


def test_virtualize_parallel_forwarded() -> None:
    """Parallel parameter is forwarded to _open_virtual_mfdataset."""
    from earthaccess.virtual.core import virtualize

    reg_patch, open_patch = _patch_internals()
    with reg_patch, open_patch as mock_open:
        virtualize(_make_granules(1), parallel=False)

    _, kwargs = mock_open.call_args
    assert kwargs["parallel"] is False


# ---------------------------------------------------------------------------
# group normalisation
# ---------------------------------------------------------------------------


def test_virtualize_group_slash_normalised_for_ref_name(tmp_path) -> None:
    """Group '/' produces a 'root' segment in the reference file name."""
    from earthaccess.virtual.core import _load_via_kerchunk

    mock_vds = MagicMock()
    with patch("earthaccess.virtual.core.earthaccess") as mock_ea:
        mock_ea.get_fsspec_https_session.return_value = MagicMock(storage_options={})
        with patch("xarray.open_dataset", return_value=MagicMock()):
            _load_via_kerchunk(
                vds=mock_vds,
                granules=_make_granules(1),
                group="/",
                access="indirect",
                reference_dir=str(tmp_path),
                reference_format="json",
            )

    to_kerchunk_args = mock_vds.virtualize.to_kerchunk.call_args[0]
    assert "root" in to_kerchunk_args[0]


def test_virtualize_group_nested_normalised_for_ref_name(tmp_path) -> None:
    """Nested group path produces a safe file-name segment (no slashes)."""
    from earthaccess.virtual.core import _load_via_kerchunk

    mock_vds = MagicMock()
    with patch("earthaccess.virtual.core.earthaccess") as mock_ea:
        mock_ea.get_fsspec_https_session.return_value = MagicMock(storage_options={})
        with patch("xarray.open_dataset", return_value=MagicMock()):
            _load_via_kerchunk(
                vds=mock_vds,
                granules=_make_granules(1),
                group="/science/grids",
                access="indirect",
                reference_dir=str(tmp_path),
                reference_format="json",
            )

    to_kerchunk_args = mock_vds.virtualize.to_kerchunk.call_args[0]
    # the filename component should not contain slashes
    filename = Path(to_kerchunk_args[0]).name
    assert "/" not in filename
