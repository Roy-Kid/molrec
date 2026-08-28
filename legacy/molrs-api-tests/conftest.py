from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

TESTS_DATA_URL = "https://github.com/MolCrafts/tests-data.git"
CACHE_DIR = Path.home() / ".cache" / "molrs-tests-data"


@pytest.fixture(scope="session")
def tests_data() -> Path:
    if env_path := os.environ.get("MOLRS_TEST_DATA"):
        p = Path(env_path)
        assert p.exists(), f"MOLRS_TEST_DATA path not found: {p}"
        return p
    if not CACHE_DIR.exists():
        subprocess.run(
            ["git", "clone", "--depth=1", TESTS_DATA_URL, str(CACHE_DIR)],
            check=True,
        )
    return CACHE_DIR


@pytest.fixture
def tmp_zarr_path(tmp_path: Path) -> Path:
    return tmp_path / "record.zarr"
