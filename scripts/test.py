#!/usr/bin/env python3
"""
Consolidated test script for PSN Emulator Lambda services using pytest.
Works on Windows, Linux, and macOS.

Usage:
    python scripts/test.py [options]

Options:
    --service, -s   Service to test: idp_api, player_account_api, or all (default: all)
    --type, -t      Test type: unit, integration, or all (default: all)
    --verbose, -v   Verbose output
    --coverage      Generate coverage report
    --html          Generate HTML coverage report
    --html-dir      Directory for HTML coverage report (default: htmlcov)
    --parallel      Run tests in parallel using pytest-xdist
    --workers, -n   Number of parallel workers (default: auto)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"In directory: {cwd}")

    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def get_service_path(service_name: str, project_root: Path) -> Path:
    """Get the path to a service directory."""
    service_paths = {
        "idp_api": project_root / "services" / "idp_api",
        "player_account_api": project_root / "services" / "player_account_api",
    }

    if service_name not in service_paths:
        raise ValueError(f"Unknown service: {service_name}")

    return service_paths[service_name]


def build_pytest_command(
    test_type: str,
    verbose: bool,
    coverage: bool,
    html: bool,
    html_dir: str,
    parallel: bool,
    workers: str,
) -> list[str]:
    """Build the pytest command with appropriate options."""
    pytest_cmd = ["uv", "run", "pytest"]

    # Add test type marker
    if test_type == "unit":
        pytest_cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        pytest_cmd.extend(["-m", "integration"])
    # "all" runs without marker filter

    # Add verbosity
    if verbose:
        pytest_cmd.append("-v")

    # Add parallel execution
    if parallel:
        pytest_cmd.extend(["-n", workers])

    # Add coverage options
    if coverage:
        pytest_cmd.extend(
            [
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ]
        )

        if html:
            pytest_cmd.extend([f"--cov-report=html:{html_dir}"])

    return pytest_cmd


def run_service_tests(
    service_name: str,
    test_type: str,
    verbose: bool,
    coverage: bool,
    html: bool,
    html_dir: str,
    parallel: bool,
    workers: str,
    project_root: Path,
) -> int:
    """Run tests for a specific service."""
    try:
        service_path = get_service_path(service_name, project_root)
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        return 1

    print(f"\n{'='*60}")
    print(f"Running Tests for {service_name.replace('_', ' ').title()}")
    print(f"{'='*60}")
    print(f"Service path: {service_path}")
    print(f"Test type: {test_type}")
    print(f"{'='*60}\n")

    # Check if service directory exists
    if not service_path.exists():
        print(f"\n[ERROR] Service directory does not exist: {service_path}")
        return 1

    # Check if tests directory exists
    tests_path = service_path / "tests"
    if not tests_path.exists():
        print(f"\n[ERROR] Tests directory does not exist: {tests_path}")
        return 1

    # Install dev dependencies first
    print("Installing dev dependencies...")
    sync_cmd = ["uv", "sync", "--extra", "dev"]
    sync_exit_code = run_command(sync_cmd, cwd=service_path)
    if sync_exit_code != 0:
        print(f"\n[ERROR] Failed to install dev dependencies for {service_name}")
        return sync_exit_code

    # Build pytest command
    pytest_cmd = build_pytest_command(
        test_type=test_type,
        verbose=verbose,
        coverage=coverage,
        html=html,
        html_dir=html_dir,
        parallel=parallel,
        workers=workers,
    )

    # Run tests
    exit_code = run_command(pytest_cmd, cwd=service_path)

    if exit_code == 0:
        print(f"\n[OK] All tests passed for {service_name}!")
    else:
        print(f"\n[ERROR] Tests failed for {service_name} with exit code {exit_code}")

    return exit_code


def test_services(
    services: list[str],
    test_type: str,
    verbose: bool,
    coverage: bool,
    html: bool,
    html_dir: str,
    parallel: bool,
    workers: str,
) -> int:
    """Test one or more services."""
    # Get project root (this script is in scripts/, so go up one level)
    project_root = Path(__file__).parent.parent

    # Determine which services to test
    if "all" in services:
        services_to_test = ["idp_api", "player_account_api"]
    else:
        services_to_test = services

    print(f"\n{'='*80}")
    print("Testing PSN Emulator Lambda Services")
    print(f"{'='*80}")
    print(f"Services: {', '.join(services_to_test)}")
    print(f"Test type: {test_type}")
    print(f"Coverage: {coverage}")
    print(f"HTML Report: {html}")
    print(f"Parallel: {parallel}")
    print(f"{'='*80}\n")

    overall_exit_code = 0

    # Test each service
    for service in services_to_test:
        exit_code = run_service_tests(
            service_name=service,
            test_type=test_type,
            verbose=verbose,
            coverage=coverage,
            html=html,
            html_dir=html_dir,
            parallel=parallel,
            workers=workers,
            project_root=project_root,
        )

        if exit_code != 0:
            overall_exit_code = exit_code

    # Print summary
    print(f"\n{'='*80}")
    if overall_exit_code == 0:
        print("[OK] All service tests passed!")
    else:
        print("[ERROR] Some tests failed. Check the output above for details.")
    print(f"{'='*80}")

    return overall_exit_code


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests for PSN Emulator Lambda services"
    )
    parser.add_argument(
        "--service",
        "-s",
        choices=["idp_api", "player_account_api", "all"],
        nargs="+",
        default=["all"],
        help="Service(s) to test (default: all)",
    )
    parser.add_argument(
        "--type",
        "-t",
        choices=["unit", "integration", "all"],
        default="all",
        help="Test type to run (default: all)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report (requires --coverage)",
    )
    parser.add_argument(
        "--html-dir",
        default="htmlcov",
        help="Directory for HTML coverage report (default: htmlcov)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist",
    )
    parser.add_argument(
        "--workers",
        "-n",
        default="auto",
        help="Number of parallel workers (default: auto)",
    )

    args = parser.parse_args()

    return test_services(
        services=args.service,
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        html=args.html,
        html_dir=args.html_dir,
        parallel=args.parallel,
        workers=args.workers,
    )


if __name__ == "__main__":
    sys.exit(main())
