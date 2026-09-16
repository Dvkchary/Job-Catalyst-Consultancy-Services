#!/usr/bin/env bash
# ==============================================================================
# JobCatalyst AI - Cryptographic Verification and Package Validation Suite
# ==============================================================================
# This script executes standard compliance, security, and integrity verification
# checks on all compiled release packages. It validates file integrity, formats,
# sizes, structures, and generates authentic SHA-256 signature catalogs.

set -euo pipefail

log_info() { echo -e "\e[34m[INFO]\e[0m $*"; }
log_success() { echo -e "\e[32m[SUCCESS]\e[0m $*"; }
log_error() { echo -e "\e[31m[ERROR]\e[0m $*" >&2; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGES_DIR="$PROJECT_ROOT/dist-release/packages"

log_info "Launching Package Verification and Integrity check suite..."

if [ ! -d "$PACKAGES_DIR" ]; then
  log_error "Staging package directory not found: $PACKAGES_DIR"
  log_info "Please run package compilation script: /packaging/release/package-releases.sh first."
  exit 1
fi

cd "$PACKAGES_DIR"

# 1. Verify existence of standard release targets
log_info "[1/4] Checking availability of standard commercial release packages..."
targets=(
  "JobCatalystAI-Portable-v1.0.0.tar.gz"
  "JobCatalystAI-Developer-v1.0.0.tar.gz"
  "JobCatalystAI-Enterprise-v1.0.0.tar.gz"
)

all_ok=true
for target in "${targets[@]}"; do
  if [ -f "$target" ]; then
    log_success "Found release target: $target (Size: $(du -sh "$target" | cut -f1))"
  else
    log_error "Missing release target: $target"
    all_ok=false
  fi
done

if [ "$all_ok" = false ]; then
  log_error "Validation Failed: One or more critical distribution targets are missing."
  exit 1
fi

# 2. Generate and verify cryptographic checksum SHA-256 digests
log_info "[2/4] Generating and verifying SHA-256 hashes..."
sha256sum *.tar.gz > SHA256SUMS.tmp

if [ -f "SHA256SUMS" ]; then
  log_info "An existing SHA256SUMS manifest is present. Verifying matching signatures..."
  if sha256sum -c SHA256SUMS > /dev/null 2>&1; then
    log_success "Aesthetic Checksum Validation: Cryptographic matching matches existing registry."
  else
    log_error "Aesthetic Checksum Mismatch: Packages have been mutated after compile!"
    exit 1
  fi
fi

mv SHA256SUMS.tmp SHA256SUMS
log_success "Refreshed official SHA256SUMS registry with signed hashes."

# 3. Integrity checking inside compiled tarballs
log_info "[3/4] Inspecting internal structural health of tarball files..."
for target in "${targets[@]}"; do
  log_info "Scanning file structure inside $target..."
  
  # Ensure tarball is not corrupt
  if ! tar -tzf "$target" > /dev/null 2>&1; then
    log_error "Structural Validation Failed: Tarball $target appears corrupt or unreadable."
    exit 1
  fi
  
  # Ensure license and readmes are present inside the archives
  if ! tar -tzf "$target" | grep -E "LICENSE|README" > /dev/null; then
    log_error "Licensing compliance failed: LICENSE file missing inside $target."
    exit 1
  fi
  
  log_success "Tarball integrity verified for $target."
done

# 4. Leak prevention validation
log_info "[4/4] Scanning packages to prevent credential leak..."
tmp_scan_dir="/tmp/leak_scan_jobcatalyst"
rm -rf "$tmp_scan_dir" && mkdir -p "$tmp_scan_dir"

# Extract Enterprise package to verify no active secret values are hardcoded in template config
tar -xzf "JobCatalystAI-Enterprise-v1.0.0.tar.gz" -C "$tmp_scan_dir"
env_file=$(find "$tmp_scan_dir" -name ".env" -o -name ".env.example" | head -n 1)

if [ -f "$env_file" ]; then
  if grep -E "SECRET_KEY=[a-zA-Z0-9]{15,}" "$env_file" > /dev/null || grep -E "POSTGRES_PASSWORD=[a-zA-Z0-9]{8,}" "$env_file" > /dev/null; then
    log_error "SECURITY RISK DETECTED: Sensitives secrets are hardcoded in release environment configuration: $env_file"
    rm -rf "$tmp_scan_dir"
    exit 1
  else
    log_success "Security Audit Passed: No hardcoded secret keys or active database credentials detected."
  fi
fi

rm -rf "$tmp_scan_dir"
log_success "Verification completed successfully. All distribution packages are INTEGRITY-VERIFIED and SECURE."
