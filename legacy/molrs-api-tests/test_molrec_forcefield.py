from __future__ import annotations

import molrs
import molrs.ff
import molrs.io


class TestMMFFForceField:
    def test_roundtrip(self, tmp_zarr_path):
        mol = molrs.io.SmilesIR("CCO").to_atomistic()
        typifier = molrs.ff.MMFF94Typifier()
        typed_frame = typifier.typify(mol).to_frame()
        ff = typifier.forcefield()

        record = molrs.MolRec()
        record.set_frame(typed_frame)
        record.set_forcefield(ff)
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert loaded.method["type"] == "classical"
        assert loaded.method["classical"]["force_field"]["name"] == ff.name

    def test_meta_preserved(self, tmp_zarr_path):
        mol = molrs.io.SmilesIR("CCO").to_atomistic()
        typifier = molrs.ff.MMFF94Typifier()
        typed_frame = typifier.typify(mol).to_frame()
        ff = typifier.forcefield()

        record = molrs.MolRec()
        record.set_frame(typed_frame)
        record.set_forcefield(ff)
        record.meta = {"creator": {"name": "pytest"}}
        record.write_zarr(str(tmp_zarr_path))
        loaded = molrs.MolRec.read_zarr(str(tmp_zarr_path))

        assert loaded.meta["creator"]["name"] == "pytest"
        assert loaded.method["type"] == "classical"
