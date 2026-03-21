"""
Tests to verify all core dependencies can be imported successfully.

These tests ensure the environment is properly configured and all
required packages are installed correctly.
"""


class TestCoreImports:
    """Test that all core dependencies can be imported."""

    def test_import_fastapi(self) -> None:
        """Verify FastAPI can be imported."""
        import fastapi

        assert fastapi is not None
        assert hasattr(fastapi, "FastAPI")

    def test_import_uvicorn(self) -> None:
        """Verify Uvicorn can be imported."""
        import uvicorn

        assert uvicorn is not None
        assert hasattr(uvicorn, "run")

    def test_import_pydantic(self) -> None:
        """Verify Pydantic can be imported."""
        import pydantic

        assert pydantic is not None
        assert hasattr(pydantic, "BaseModel")

    def test_import_httpx(self) -> None:
        """Verify httpx can be imported."""
        import httpx

        assert httpx is not None
        assert hasattr(httpx, "AsyncClient")


class TestDevImports:
    """Test that development dependencies can be imported."""

    def test_import_pytest(self) -> None:
        """Verify pytest can be imported."""
        import pytest as pt

        assert pt is not None

    def test_import_pytest_asyncio(self) -> None:
        """Verify pytest-asyncio can be imported."""
        import pytest_asyncio

        assert pytest_asyncio is not None

    def test_import_ruff(self) -> None:
        """Verify ruff is available via CLI."""
        import subprocess

        result = subprocess.run(["ruff", "--version"], capture_output=True)
        assert result.returncode == 0


class TestPackageMetadata:
    """Test package metadata is correctly configured."""

    def test_package_version(self) -> None:
        """Verify package version is accessible."""
        from workflow_orchestration_queue import __version__

        assert __version__ == "0.1.0"

    def test_package_author(self) -> None:
        """Verify package author is accessible."""
        from workflow_orchestration_queue import __author__

        assert __author__ == "Intel Agency"
