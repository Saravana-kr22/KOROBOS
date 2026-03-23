#!/usr/bin/env python3
"""
License Compliance Checker for KOROBOS

Validates dependencies against the license policy defined in license_policy.yml.
Supports multiple SBOM formats (JSON, YAML, CycloneDX).
"""

import json
import sys
from pathlib import Path
from typing import List

import yaml


class LicenseChecker:
    """Check dependency licenses against enterprise policy."""

    def __init__(self, policy_file: str):
        """Load license policy from YAML file."""
        with open(policy_file) as f:
            self.policy = yaml.safe_load(f)

        self.allowed = set(self.policy["licenses"]["allowed"])
        self.restricted = set(self.policy["licenses"]["restricted"])
        self.blocked = set(self.policy["licenses"]["blocked"])

    def check_dependency(self, name: str, license_str: str) -> tuple[bool, str]:
        """
        Check if a dependency's license is compliant.

        Returns (is_allowed, reason)
        """
        if not license_str:
            return False, f"{name}: No license specified"

        # Normalize license identifier
        licenses = [lic.strip() for lic in license_str.replace(" OR ", "|").split("|")]

        violations = []
        for lic in licenses:
            lic = lic.strip()
            if lic in self.blocked:
                violations.append(f"BLOCKED: {lic}")
            elif lic in self.restricted:
                violations.append(f"RESTRICTED (needs approval): {lic}")
            elif lic not in self.allowed:
                violations.append(f"UNKNOWN: {lic}")

        if violations:
            return False, f"{name}: {', '.join(violations)}"

        return True, f"{name}: ✓ {license_str}"

    def check_sbom_json(self, sbom_file: str) -> tuple[int, int, List[str]]:
        """Check licenses in CycloneDX/SBOM JSON format."""
        with open(sbom_file) as f:
            sbom = json.load(f)

        passed = 0
        failed = 0
        issues = []

        # Parse components (CycloneDX format)
        components = sbom.get("components", [])
        for comp in components:
            name = comp.get("name", "unknown")
            license_info = comp.get("license", {})

            # Handle different license formats
            if isinstance(license_info, dict):
                license_str = license_info.get("expression", "")
            elif isinstance(license_info, str):
                license_str = license_info
            else:
                license_str = ""

            is_ok, msg = self.check_dependency(name, license_str)
            if is_ok:
                passed += 1
            else:
                failed += 1
                issues.append(msg)

        return passed, failed, issues

    def check_pip_freeze(self, requirements_file: str) -> tuple[int, int, List[str]]:
        """Check licenses from pip freeze output with metadata."""
        # This would require pip-licenses or similar tool
        # For now, provide a note
        return 0, 0, ["pip-freeze check requires pip-licenses tool"]

    def check_npm_package_lock(
        self, package_lock_file: str
    ) -> tuple[int, int, List[str]]:
        """Check licenses from npm package-lock.json."""
        with open(package_lock_file) as f:
            lock = json.load(f)

        passed = 0
        failed = 0
        issues = []

        packages = lock.get("packages", {})
        for pkg_name, pkg_info in packages.items():
            if not pkg_name or pkg_name == "":  # Skip root
                continue

            license_str = pkg_info.get("license", "")
            if not license_str:
                continue

            is_ok, msg = self.check_dependency(pkg_name, license_str)
            if is_ok:
                passed += 1
            else:
                failed += 1
                issues.append(msg)

        return passed, failed, issues


def main():
    """Run license compliance checks."""
    policy_file = "scripts/compliance/license_policy.yml"

    if not Path(policy_file).exists():
        print(f"❌ Policy file not found: {policy_file}")
        sys.exit(1)

    checker = LicenseChecker(policy_file)
    print("🔍 Checking license compliance...")
    print()

    total_passed = 0
    total_failed = 0
    all_issues = []

    # Check backend (Python) dependencies
    # Note: requires pip-licenses or sbom generation
    backend_sbom = "backend/sbom.json"
    if Path(backend_sbom).exists():
        print(f"Checking Python dependencies ({backend_sbom})...")
        passed, failed, issues = checker.check_sbom_json(backend_sbom)
        total_passed += passed
        total_failed += failed
        all_issues.extend(issues)
        print(f"  ✓ Passed: {passed}, ❌ Failed: {failed}")
        if issues:
            for issue in issues:
                print(f"    {issue}")
        print()

    # Check frontend (Node.js) dependencies
    frontend_lock = "frontend/package-lock.json"
    if Path(frontend_lock).exists():
        print(f"Checking frontend dependencies ({frontend_lock})...")
        passed, failed, issues = checker.check_npm_package_lock(frontend_lock)
        total_passed += passed
        total_failed += failed
        all_issues.extend(issues)
        print(f"  ✓ Passed: {passed}, ❌ Failed: {failed}")
        if issues:
            for issue in issues[:5]:  # Show first 5
                print(f"    {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more issues")
        print()

    # Check mobile (Node.js) dependencies
    mobile_lock = "mobile/package-lock.json"
    if Path(mobile_lock).exists():
        print(f"Checking mobile dependencies ({mobile_lock})...")
        passed, failed, issues = checker.check_npm_package_lock(mobile_lock)
        total_passed += passed
        total_failed += failed
        all_issues.extend(issues)
        print(f"  ✓ Passed: {passed}, ❌ Failed: {failed}")
        if issues:
            for issue in issues[:5]:  # Show first 5
                print(f"    {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more issues")
        print()

    # Summary
    print("=" * 60)
    print("License Compliance Summary")
    print(f"  Total Passed: {total_passed}")
    print(f"  Total Failed: {total_failed}")
    print(f"  Policy File: {policy_file}")

    if total_failed > 0:
        print(f"\n⚠️  {total_failed} license violations found!")
        print("Review the issues above and either:")
        print("  1. Update dependencies to use compliant licenses")
        print("  2. Add to 'restricted' list with approval required")
        print("  3. Update license_policy.yml to allow")
        sys.exit(1)
    else:
        print("\n✅ All dependencies comply with license policy!")
        sys.exit(0)


if __name__ == "__main__":
    main()
