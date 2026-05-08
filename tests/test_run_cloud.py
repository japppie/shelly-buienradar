import sys
import os

# Add root directory to python path if not already there, though pytest handles it usually
# but for robust importing of scripts in the root dir we ensure it.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_run_cloud_imports_successfully():
    """
    Test that run_cloud.py can be imported without throwing any exceptions.
    This specifically guards against issues like missing attributes in third-party
    libraries (e.g., modal API changes).
    """
    try:
        import run_cloud

        assert run_cloud.app is not None
    except Exception as e:
        import pytest

        pytest.fail(f"Importing run_cloud.py failed with an exception: {e}")
