from __future__ import annotations

import molrs
import numpy as np


class TestFramePDB:
    def test_roundtrip(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert loaded.count_frames() == 1
        assert "atoms" in loaded.frame
        assert loaded.frame["atoms"].nrows == frame["atoms"].nrows

    def test_meta_and_method_preserved(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        record = molrs.MolRec()
        record.set_frame(frame)
        record.meta = {"version": [0, 2], "creator": {"name": "pytest"}}
        record.method = {
            "type": "static_structure",
            "description": "single-frame pdb import",
        }
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert loaded.meta["creator"]["name"] == "pytest"
        assert loaded.method["type"] == "static_structure"


class TestScalarObservable:
    def test_roundtrip(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        record = molrs.MolRec()
        record.set_frame(frame)

        obs = molrs.ScalarObservable(
            "total_energy",
            np.array([1.0, 1.5, 2.0], dtype=np.float32),
            description="Total energy by step",
            unit="eV",
            axes=["timestep"],
            time_dependent=True,
            sampling="trajectory_sample",
            domain="trajectory",
        )
        record.observables.add(obs)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert "total_energy" in loaded.observables
        assert loaded.observables.get("total_energy").kind == "scalar"


class TestVectorObservable:
    def test_roundtrip(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        record = molrs.MolRec()
        record.set_frame(frame)

        dipole = record.observables.add_vector(
            "dipole",
            np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
            description="Dipole vector",
            unit="D",
            axes=["sample", "component"],
            domain="record",
        )
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert "dipole" in loaded.observables
        assert loaded.observables.get("dipole").kind == dipole.kind


class TestGridInFrame:
    def test_roundtrip(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        grid = molrs.Grid(
            dim=np.array([4, 4, 4], dtype=np.intp),
            origin=np.zeros(3, dtype=np.float32),
            cell=(np.eye(3) * 10.0).astype(np.float32),
            pbc=np.array([True, True, True]),
        )
        grid["electron_density"] = np.ones((4, 4, 4), dtype=np.float32) * 0.25
        grid["spin_density"] = np.zeros((4, 4, 4), dtype=np.float32)
        frame["density"] = grid

        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        loaded_grid = loaded.frame["density"]
        assert isinstance(loaded_grid, molrs.Grid)
        assert list(loaded_grid.dim) == [4, 4, 4]
        assert "electron_density" in loaded_grid
        assert "spin_density" in loaded_grid
        assert loaded_grid["electron_density"].shape == (4, 4, 4)

    def test_multi_array_grid(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        grid = molrs.Grid(
            dim=np.array([2, 3, 4], dtype=np.intp),
            origin=np.zeros(3, dtype=np.float32),
            cell=(np.eye(3) * 5.0).astype(np.float32),
            pbc=np.array([False, False, False]),
        )
        grid["total"] = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
        grid["diff"] = np.zeros((2, 3, 4), dtype=np.float32)
        frame["chgcar"] = grid

        record = molrs.MolRec()
        record.set_frame(frame)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        g = loaded.frame["chgcar"]
        assert isinstance(g, molrs.Grid)
        assert set(g.keys()) == {"total", "diff"}
        assert g["total"].shape == (2, 3, 4)


class TestGridObservable:
    def test_roundtrip(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        grid = molrs.Grid(
            dim=np.array([4, 4, 4], dtype=np.intp),
            origin=np.zeros(3, dtype=np.float32),
            cell=(np.eye(3) * 10.0).astype(np.float32),
            pbc=np.array([True, True, True]),
        )
        grid["density"] = np.ones((4, 4, 4), dtype=np.float32) * 0.25

        record = molrs.MolRec()
        record.set_frame(frame)
        record.observables.add_grid(
            "charge_density",
            grid,
            description="Electron charge density",
            unit="e/Angstrom^3",
        )
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert "charge_density" in loaded.observables
        obs = loaded.observables.get("charge_density")
        assert obs.kind == "grid"
        assert isinstance(obs.data, molrs.Grid)
        assert list(obs.data.dim) == [4, 4, 4]
        assert "density" in obs.data
        np.testing.assert_allclose(obs.data["density"], 0.25, atol=1e-5)

    def test_multi_array_grid_observable(self, tests_data, tmp_zarr_path):
        frame = molrs.read_pdb(str(tests_data / "pdb" / "water.pdb"))
        grid = molrs.Grid(
            dim=np.array([2, 2, 2], dtype=np.intp),
            origin=np.zeros(3, dtype=np.float32),
            cell=(np.eye(3) * 5.0).astype(np.float32),
            pbc=np.array([True, True, True]),
        )
        grid["total"] = np.ones((2, 2, 2), dtype=np.float32)
        grid["diff"] = np.full((2, 2, 2), 0.5, dtype=np.float32)

        record = molrs.MolRec()
        record.set_frame(frame)
        record.observables.add_grid("spin_density", grid)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        obs = loaded.observables.get("spin_density")
        assert obs.kind == "grid"
        assert set(obs.data.keys()) == {"total", "diff"}
        np.testing.assert_allclose(obs.data["total"], 1.0, atol=1e-5)
        np.testing.assert_allclose(obs.data["diff"], 0.5, atol=1e-5)
