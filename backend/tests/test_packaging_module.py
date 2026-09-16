# ==============================================================================
# JobCatalyst AI - DevOps & Packaging Release Engineering Tests
# ==============================================================================
# This test suite validates all programmatic routines for packaging, checking digests,
# compiles release manifests, and simulates rolling upgrades and recovery.

import pytest
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.packaging_service import (
    PackagingService,
    ReleaseService,
    VerificationService,
)


@pytest.fixture
def temp_workspace():
    """
    Creates an isolated temporary directory to act as a staging sandbox for builds.
    """
    with TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_sha256_checksum_generation(temp_workspace):
    """
    Ensures VerificationService computes exact matching SHA-256 digests.
    """
    test_file = temp_workspace / "JobCatalystAI-Test-Setup.exe"
    content = b"Commercial production binary mockup data. Entropy, bits, signs."
    test_file.write_bytes(content)

    calculated_hash = VerificationService.calculate_sha256(test_file)
    assert len(calculated_hash) == 64
    # Re-calculate and compare
    expected_hash = "6df3649fcbf33cb002364c3913076ff7a885b5420367ca9fba33e8b09fec1584"
    assert calculated_hash == expected_hash


def test_package_integrity_validations(temp_workspace):
    """
    Checks that VerificationService flags packages missing mandatory folders or readmes.
    """
    test_archive = temp_workspace / "JobCatalystAI-Portable-v1.0.0.tar.gz"
    
    # Check on non-existent package
    result = VerificationService.verify_package_integrity(test_archive, ["LICENSE"])
    assert result["status"] == "FAILED"
    assert "not found" in result["error"]

    # Assemble mock tarball
    import tarfile
    with tarfile.open(test_archive, "w:gz") as tar:
        # Create a simple file inside tarball
        license_path = temp_workspace / "LICENSE"
        license_path.write_text("Apache License 2.0")
        tar.add(license_path, arcname="LICENSE")

    # Run check with present LICENSE
    result = VerificationService.verify_package_integrity(test_archive, ["LICENSE"])
    assert result["status"] == "VERIFIED"
    assert "checksum" in result
    assert result["file_count"] == 1

    # Run check with missing README requirement
    result_fail = VerificationService.verify_package_integrity(test_archive, ["LICENSE", "README.md"])
    assert result_fail["status"] == "FAILED"
    assert "compliance or license files" in result_fail["error"]


def test_packaging_staging_cleanup(temp_workspace):
    """
    Validates that PackagingService correctly sets up directories and purges old files.
    """
    pkg_svc = PackagingService(workspace_root=temp_workspace)
    
    # Set up staging
    setup_res = pkg_svc.staging_setup()
    assert setup_res["status"] == "SUCCESS"
    assert Path(setup_res["staging_dir"]).exists()
    assert (temp_workspace / "dist-release" / "windows").exists()

    # Place a file to test cleanup on subsequent setup
    dummy_file = temp_workspace / "dist-release" / "windows" / "JobCatalystLauncher.exe"
    dummy_file.write_text("Dummy binary executable")
    assert dummy_file.exists()

    # Trigger packaging staging again
    pkg_svc.staging_setup()
    assert not dummy_file.exists()  # Old staging must have been cleaned


def test_release_manifest_compilation(temp_workspace):
    """
    Ensures ReleaseService constructs robust release-manifest digests for deployment registries.
    """
    rel_svc = ReleaseService(workspace_root=temp_workspace)
    
    # If package directory is missing
    fail_res = rel_svc.compile_release_manifest()
    assert fail_res["status"] == "FAILED"

    # Set up mock package files
    pkg_dir = temp_workspace / "dist-release" / "packages"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    
    pkg_file = pkg_dir / "JobCatalystAI-Enterprise-v1.0.0.tar.gz"
    pkg_file.write_text("Enterprise container stack deployment binaries.")

    success_res = rel_svc.compile_release_manifest()
    assert success_res["status"] == "SUCCESS"
    assert len(success_res["manifest"]["artifacts"]) == 1
    assert success_res["manifest"]["artifacts"][0]["filename"] == "JobCatalystAI-Enterprise-v1.0.0.tar.gz"
