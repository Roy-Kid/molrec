"""Tests for the Gaussian Cube reader and its integration with the Grid type.

Tests use real cube files from tests-data/cube/ (from h5cube project).
"""
from __future__ import annotations

from pathlib import Path

import molrs
import numpy as np
import pytest


# ---------------------------------------------------------------------------
# TestReadCube – basic I/O
# ---------------------------------------------------------------------------


class TestReadCube:
    """Basic I/O tests for read_cube_file."""

    def test_returns_frame(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        assert isinstance(frame, molrs.Frame)

    def test_atoms_block_present(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        assert "atoms" in frame
        assert frame["atoms"].nrows == 2

    def test_atom_symbols(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        atoms = frame["atoms"]
        syms = atoms.view("element")
        assert list(syms) == ["H", "H"]

    def test_no_simbox(self, tests_data: Path):
        """Cube files are not periodic – no SimBox should be set."""
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        assert frame.simbox is None

    def test_units_in_meta(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20.cube"))
        assert frame.meta.get("cube_units") == "bohr"

    def test_angstrom_units(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20ang.cube"))
        assert frame.meta.get("cube_units") == "angstrom"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(Exception):
            molrs.read_cube_file(str(tmp_path / "nonexistent.cube"))


# ---------------------------------------------------------------------------
# TestCubeGrid – grid structure
# ---------------------------------------------------------------------------


class TestCubeGrid:
    """Tests that the Grid embedded in the Frame is correct."""

    def test_grid_key_exists(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        g = frame["cube"]
        assert isinstance(g, molrs.Grid)

    def test_grid_dimensions_valtest(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        g = frame["cube"]
        assert list(g.dim) == [1, 1, 5]

    def test_grid_dimensions_grid20(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20.cube"))
        g = frame["cube"]
        assert list(g.dim) == [20, 20, 20]

    def test_density_array_present(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20.cube"))
        g = frame["cube"]
        assert "density" in g

    def test_density_array_shape(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20.cube"))
        g = frame["cube"]
        density = g["density"]
        assert density.shape == (20, 20, 20)

    def test_valtest_known_values(self, tests_data: Path):
        """Check known data values from valtest.cube."""
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        density = frame["cube"]["density"]
        # From file: -1.00000E+02 -1.00000E-02 0 1.00000E-02 1.00000E+02
        np.testing.assert_allclose(density.flat[0], -100.0, atol=1e-5)
        np.testing.assert_allclose(density.flat[4], 100.0, atol=1e-5)

    def test_grid_meshgrid_shape(self, tests_data: Path):
        """grid.grid must have shape (nx, ny, nz, 3)."""
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))
        g = frame["cube"]
        assert g.grid.shape == (1, 1, 5, 3)


# ---------------------------------------------------------------------------
# TestCubeMO – molecular orbital variant
# ---------------------------------------------------------------------------


class TestCubeMO:
    """Tests for MO-mode cube files (negative NATOMS)."""

    def test_mo_grid_keys(self, tests_data: Path):
        """grid20mo6-8.cube has 3 orbitals: mo_6, mo_7, mo_8."""
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20mo6-8.cube"))
        g = frame["cube"]
        assert "mo_6" in g
        assert "mo_7" in g
        assert "mo_8" in g
        assert "density" not in g

    def test_mo_indices_meta(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20mo6-8.cube"))
        assert frame.meta.get("cube_mo_indices") == "6,7,8"

    def test_mo_array_shape(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20mo6-8.cube"))
        g = frame["cube"]
        assert g["mo_6"].shape == (20, 20, 20)

    def test_single_mo(self, tests_data: Path):
        """grid25mo.cube has 1 orbital: mo_5."""
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid25mo.cube"))
        g = frame["cube"]
        assert "mo_5" in g
        assert g["mo_5"].shape == (25, 25, 25)
        assert frame.meta.get("cube_mo_indices") == "5"

    def test_mo_atom_count(self, tests_data: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20mo6-8.cube"))
        assert frame["atoms"].nrows == 7


# ---------------------------------------------------------------------------
# TestCubeWriteRoundtrip – read → write → read
# ---------------------------------------------------------------------------


class TestCubeWriteRoundtrip:
    """Roundtrip: read cube → write cube → read back → compare."""

    def test_roundtrip_density(self, tests_data: Path, tmp_path: Path):
        path_in = str(tests_data / "cube" / "valtest.cube")
        path_out = str(tmp_path / "valtest_rt.cube")

        frame1 = molrs.read_cube_file(path_in)
        molrs.write_cube_file(path_out, frame1)
        frame2 = molrs.read_cube_file(path_out)

        assert frame2["atoms"].nrows == frame1["atoms"].nrows
        assert list(frame2["cube"].dim) == list(frame1["cube"].dim)

        d1 = frame1["cube"]["density"]
        d2 = frame2["cube"]["density"]
        np.testing.assert_allclose(d2, d1, atol=1e-4)

    def test_roundtrip_grid20(self, tests_data: Path, tmp_path: Path):
        path_in = str(tests_data / "cube" / "grid20.cube")
        path_out = str(tmp_path / "grid20_rt.cube")

        frame1 = molrs.read_cube_file(path_in)
        molrs.write_cube_file(path_out, frame1)
        frame2 = molrs.read_cube_file(path_out)

        assert frame2["atoms"].nrows == 16
        assert list(frame2["cube"].dim) == [20, 20, 20]

        d1 = frame1["cube"]["density"]
        d2 = frame2["cube"]["density"]
        np.testing.assert_allclose(d2, d1, rtol=1e-4, atol=1e-20)


# ---------------------------------------------------------------------------
# TestCubeZarrRoundtrip – cube Grid survives MolRec Zarr roundtrip
# ---------------------------------------------------------------------------


class TestCubeZarrRoundtrip:
    """The Grid read from a cube file survives a MolRec Zarr roundtrip."""

    def test_density_roundtrip(self, tests_data: Path, tmp_zarr_path: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "valtest.cube"))

        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        g = loaded.frame["cube"]
        assert isinstance(g, molrs.Grid)
        assert list(g.dim) == [1, 1, 5]
        assert "density" in g

        d_orig = frame["cube"]["density"]
        d_loaded = g["density"]
        np.testing.assert_allclose(d_loaded, d_orig, atol=1e-10)

    def test_grid20_roundtrip(self, tests_data: Path, tmp_zarr_path: Path):
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20.cube"))

        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        g = loaded.frame["cube"]
        assert isinstance(g, molrs.Grid)
        assert list(g.dim) == [20, 20, 20]
        assert "density" in g
        assert g["density"].shape == (20, 20, 20)

    def test_mo_roundtrip(self, tests_data: Path, tmp_zarr_path: Path):
        """MO cube grids (multiple arrays) survive Zarr roundtrip."""
        frame = molrs.read_cube_file(
            str(tests_data / "cube" / "grid20mo6-8.cube")
        )

        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        g = loaded.frame["cube"]
        assert isinstance(g, molrs.Grid)
        assert "mo_6" in g
        assert "mo_7" in g
        assert "mo_8" in g
        assert g["mo_6"].shape == (20, 20, 20)

        # Compare values
        g_orig = frame["cube"]
        np.testing.assert_allclose(g["mo_6"], g_orig["mo_6"], atol=1e-10)
        np.testing.assert_allclose(g["mo_7"], g_orig["mo_7"], atol=1e-10)
        np.testing.assert_allclose(g["mo_8"], g_orig["mo_8"], atol=1e-10)

    def test_atoms_preserved(self, tests_data: Path, tmp_zarr_path: Path):
        """Atoms block survives the Zarr roundtrip."""
        frame = molrs.read_cube_file(str(tests_data / "cube" / "grid20.cube"))

        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert "atoms" in loaded.frame
        assert loaded.frame["atoms"].nrows == 16
