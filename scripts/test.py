#!/usr/bin/env python3
"""
Consolidated test script for PSN Emulator Lambda services using pytest.
Works on Windows, Linux, and macOS.

Each service has its own pyproject.toml and .venv directory. When testing individual
services, it uses that service's virtual environment. When testing all services,
it tests each service one by one using their respective .venv directories.

Usage:
    python scripts/test.py [options]

Options:
    --service, -s   Service to test: idp_api, player_account_api etc, or all (default: all)
    --type, -t      Test type: unit, integration, or all (default: all)
    --verbose, -v   Verbose output
    --coverage      Generate coverage report
    --html          Generate HTML coverage report
    --html-dir      Directory for HTML coverage report (default: htmlcov)
    --parallel      Run tests in parallel using pytest-xdist (per service)
    --workers, -n   Number of parallel workers (default: auto)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"In directory: {cwd}")

    result = subprocess.run(cmd, cwd=cwd, env=env)
    return result.returncode


def discover_services(project_root: Path) -> list[str]:
    """Dynamically discover all service directories in the services folder."""
    services_dir = project_root / "services"

    if not services_dir.exists():
        raise FileNotFoundError(f"Services directory not found: {services_dir}")

    # Find all subdirectories that contain at least a src/ or tests/ directory
    services = []
    for item in services_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            # Check if this looks like a valid service directory
            has_src = (item / "src").exists()
            has_tests = (item / "tests").exists()
            has_pyproject = (item / "pyproject.toml").exists()

            if (has_src or has_tests) and has_pyproject:
                services.append(item.name)

    return sorted(services)


def get_service_path(service_name: str, project_root: Path) -> Path:
    """Get the path to a service directory."""
    service_path = project_root / "services" / service_name

    if not service_path.exists():
        raise ValueError(f"Unknown service: {service_name}")

    return service_path


def get_service_python_executable(service_path: Path) -> Path:
    """Get the Python executable from the service's .venv directory."""
    if sys.platform == "win32":
        python_exe = service_path / ".venv" / "Scripts" / "python.exe"
    else:
        python_exe = service_path / ".venv" / "bin" / "python"

    if not python_exe.exists():
        raise FileNotFoundError(f"Python executable not found: {python_exe}")

    return python_exe


def build_pytest_command(
    test_type: str,
    verbose: bool,
    coverage: bool,
    html: bool,
    html_dir: str,
    parallel: bool,
    workers: str,
    use_service_venv: bool = True,
) -> list[str]:
    """Build the pytest command with appropriate options."""

    if use_service_venv:
        # Will use the service's Python executable directly
        pytest_cmd = ["pytest"]
    else:
        # Use uv run pytest (fallback)
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


def setup_service_environment(service_path: Path) -> dict[str, str]:
    """Set up environment variables for the service's virtual environment."""
    import os

    # Copy current environment
    env = os.environ.copy()

    # Add service's .venv to PATH
    if sys.platform == "win32":
        venv_bin = str(service_path / ".venv" / "Scripts")
    else:
        venv_bin = str(service_path / ".venv" / "bin")

    # Prepend the service's virtual environment bin directory to PATH
    env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

    # Set PYTHONPATH to ensure service's source is found
    env["PYTHONPATH"] = str(service_path / "src")

    return env


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
    """Run tests for a specific service using its own virtual environment."""
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
    print(f"Using service virtual environment: {service_path / '.venv'}")
    print(f"{'='*60}\n")

    # Check if service directory exists
    if not service_path.exists():
        print(f"\n[ERROR] Service directory does not exist: {service_path}")
        return 1

    # Check if pyproject.toml exists
    pyproject_path = service_path / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"\n[ERROR] pyproject.toml not found: {pyproject_path}")
        return 1

    # Check if tests directory exists
    tests_path = service_path / "tests"
    if not tests_path.exists():
        print(f"\n[ERROR] Tests directory does not exist: {tests_path}")
        return 1

    # Check if .venv exists
    venv_path = service_path / ".venv"
    if not venv_path.exists():
        print(f"\n[INFO] Virtual environment not found for {service_name}, creating it...")
        # Create virtual environment and install dependencies
        sync_cmd = ["uv", "sync", "--dev"]
        sync_exit_code = run_command(sync_cmd, cwd=service_path)
        if sync_exit_code != 0:
            print(f"\n[ERROR] Failed to create virtual environment for {service_name}")
            return sync_exit_code
    else:
        print(f"[INFO] Using existing virtual environment for {service_name}")

        # Update dependencies if needed
        print("Updating dependencies...")
        sync_cmd = ["uv", "sync", "--dev"]
        sync_exit_code = run_command(sync_cmd, cwd=service_path)
        if sync_exit_code != 0:
            print(f"\n[WARNING] Failed to update dependencies for {service_name} (continuing anyway)")

    # Get the service's Python executable
    try:
        python_exe = get_service_python_executable(service_path)
        print(f"[INFO] Using Python: {python_exe}")
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return 1

    # Set up environment for the service
    service_env = setup_service_environment(service_path)

    # Build pytest command using service's virtual environment
    pytest_cmd = build_pytest_command(
        test_type=test_type,
        verbose=verbose,
        coverage=coverage,
        html=html,
        html_dir=html_dir,
        parallel=parallel,
        workers=workers,
        use_service_venv=True,
    )

    # Modify pytest command to use the service's Python executable
    # Note: pytest should be in the venv's Scripts/bin directory, so we don't need -m pytest
    pytest_cmd = [str(python_exe), "-m", "pytest"] + pytest_cmd[1:]

    # Run tests
    exit_code = run_command(pytest_cmd, cwd=service_path, env=service_env)

    if exit_code == 0:
        print(f"\n[OK] All tests passed for {service_name}!")
        if coverage:
            print(f"[INFO] Coverage report generated in {service_path / 'htmlcov' if html else service_path}")
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
    """Test one or more services using their individual virtual environments."""
    # Get project root (this script is in scripts/, so go up one level)
    project_root = Path(__file__).parent.parent

    # Determine which services to test
    if "all" in services:
        services_to_test = discover_services(project_root)
    else:
        services_to_test = services

    print(f"\n{'='*80}")
    print("Testing PSN Emulator Lambda Services")
    print(f"{'='*80}")
    print(f"Services: {', '.join(services_to_test)}")
    print(f"Test type: {test_type}")
    print(f"Coverage: {coverage}")
    print(f"HTML Report: {html}")
    print(f"Parallel: {parallel} (per service)")
    print(f"Note: Each service will be tested individually using its own .venv")
    print(f"{'='*80}\n")

    overall_exit_code = 0

    # Test each service one by one
    for i, service in enumerate(services_to_test, 1):
        print(f"\n[INFO] Testing service {i}/{len(services_to_test)}: {service}")

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
            if "all" in services:
                # When testing all services, continue testing even if one fails
                print(f"\n[WARNING] Service {service} failed, continuing with remaining services...")
                continue
            else:
                # When testing specific services, stop on first failure
                print(f"\n[ERROR] Service {service} failed. Stopping.")
                break

    # Print summary
    print(f"\n{'='*80}")
    if overall_exit_code == 0:
        print("[OK] All service tests passed!")
        print(f"[INFO] Tested {len(services_to_test)} service(s) successfully")
    else:
        print("[ERROR] Some tests failed. Check the output above for details.")
        failed_services = []
        for service in services_to_test:
            # We could track which ones failed, but for now just indicate there were failures
            pass
    print(f"{'='*80}")

    return overall_exit_code


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    try:
        available_services = discover_services(project_root)
    except FileNotFoundError:
        print("Error: Services directory not found")
        return 1

    parser = argparse.ArgumentParser(
        description="Run tests for PSN Emulator Lambda services"
    )
    parser.add_argument(
        "--service",
        "-s",
        choices=available_services + ["all"],
        nargs="+",
        default=["all"],
        help=f"Service(s) to test. Available: {', '.join(available_services)} (default: all)",
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
