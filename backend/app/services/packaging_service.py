# ==============================================================================
# JobCatalyst AI - Packaging, Release, and Verification Service Layer
# ==============================================================================
# This module implements the official programmatic backend services for
# administering commercial package builds, release manifests, and integrity checks.

import os
import hashlib
import tarfile
import shutil
import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger("jobcatalyst.release_engineering")


class VerificationService:
    """
    Programmatic service layer to execute security, cryptographic, and structural
    integrity verifications on compiled commercial distribution packages.
    """

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """
        Computes a secure SHA-256 cryptographic hash of a given file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    def verify_package_integrity(cls, archive_path: Path, expected_files: List[str]) -> Dict[str, Any]:
        """
        Extracts package metadata headers to verify the tarball is readable,
        uncorrupted, and contains all legally mandatory and operational files.
        """
        if not archive_path.exists():
            return {"status": "FAILED", "error": f"Target package not found at: {archive_path}"}

        try:
            # 1. Cryptographic hash calculation
            digest = cls.calculate_sha256(archive_path)

            # 2. Extract headers to inspect contents
            with tarfile.open(archive_path, "r:gz") as tar:
                members = [m.name for m in tar.getmembers()]
                
                # Check for mandatory files (e.g. LICENSE, README)
                missing = []
                for expected in expected_files:
                    found = False
                    for member in members:
                        if expected in member:
                            found = True
                            break
                    if not found:
                        missing.append(expected)

            if missing:
                return {
                    "status": "FAILED",
                    "checksum": digest,
                    "error": f"Missing compliance or license files: {', '.join(missing)}"
                }

            return {
                "status": "VERIFIED",
                "checksum": digest,
                "file_count": len(members),
                "archive_size_bytes": archive_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Integrity check failed for {archive_path.name}: {str(e)}")
            return {"status": "FAILED", "error": f"Internal tarball validation error: {str(e)}"}


class PackagingService:
    """
    Programmatic service layer to orchestrate local compilation staging
    and prepare local directories for the installer engines.
    """

    def __init__(self, workspace_root: Path = Path("/app")):
        self.workspace_root = workspace_root
        self.staging_dir = workspace_root / "dist-release"

    def staging_setup(self) -> Dict[str, Any]:
        """
        Prepares temporary build staging workspaces and cleans previous residues.
        """
        try:
            if self.staging_dir.exists():
                shutil.rmtree(self.staging_dir)
            
            self.staging_dir.mkdir(parents=True, exist_ok=True)
            (self.staging_dir / "windows").mkdir(parents=True, exist_ok=True)
            (self.staging_dir / "packages").mkdir(parents=True, exist_ok=True)
            
            logger.info("Distribution staging directory initialized.")
            return {"status": "SUCCESS", "staging_dir": str(self.staging_dir)}
        except Exception as e:
            logger.error(f"Staging setup failed: {str(e)}")
            return {"status": "FAILED", "error": str(e)}


class ReleaseService:
    """
    Programmatic service layer to coordinate distribution packaging,
    manifest generation, and compile release catalogs.
    """

    def __init__(self, workspace_root: Path = Path("/app")):
        self.workspace_root = workspace_root
        self.packages_dir = workspace_root / "dist-release" / "packages"

    def compile_release_manifest(self) -> Dict[str, Any]:
        """
        Searches staging, collects generated checksums, and produces
        the official release-manifest.json registry for deployment coordinators.
        """
        manifest = {
            "release_tag": "v1.0.0-RC1",
            "compiled_by": "JobCatalyst DevOps Automated Pipeline",
            "artifacts": []
        }

        if not self.packages_dir.exists():
            return {"status": "FAILED", "error": "No compiled distribution packages found."}

        try:
            for file_path in self.packages_dir.glob("*.tar.gz"):
                digest = VerificationService.calculate_sha256(file_path)
                manifest["artifacts"].append({
                    "filename": file_path.name,
                    "checksum_sha256": digest,
                    "size_bytes": file_path.stat().st_size
                })

            return {"status": "SUCCESS", "manifest": manifest}
        except Exception as e:
            logger.error(f"Manifest compilation failed: {str(e)}")
            return {"status": "FAILED", "error": str(e)}
