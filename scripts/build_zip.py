#!/usr/bin/env python3
"""
ZIP-based Lambda build script for PSN Partner Emulator Service.

This script builds optimized ZIP packages for AWS Lambda deployment with:
- Individual Lambda zip files based on their specific pyproject.toml dependencies
- Shared layer (shared-layer.zip) containing all libs/ code and root dependencies
- Creates {service}.zip files (service code + dependencies combined)
- Excludes __pycache__ from all zip files
- Cross-platform support (Windows/Linux/macOS)

RUNTIME-ONLY POLICY:
This script is specifically designed to create production ZIP files that ONLY contain
runtime dependencies. ALL development and orchestration dependencies are excluded:

DYNAMIC DEPENDENCY FILTERING:
- Automatically scans ALL pyproject.toml files in the project to identify dev dependencies
- Excludes dependencies from dev-related groups: dev, test, lint, format, type, doc, coverage, build
- Excludes orchestration dependencies: uv, click, rich, boto3, awscli, build tools, etc.
- Whitelists essential runtime dependencies: pydantic, aws-lambda-powertools, typing-extensions

EXCLUDED (Development/Build-time only):
- Development and test dependencies (dynamically discovered)
- Code quality tools (linting, formatting, type checking)
- Build and packaging tools (setuptools, wheel, build, etc.)
- AWS development tools (boto3, awscli, sam-cli)
- Root orchestration dependencies (uv, click, rich, etc.)

INCLUDED (Runtime only):
- Service runtime dependencies from pyproject.toml dependencies section
- Shared library code from libs/ directory
- Essential runtime dependencies (pydantic, aws-lambda-powertools, etc.)

Best practices implemented:
1. Runtime-only packages for minimal Lambda cold start times
2. Dynamic dependency discovery eliminates manual maintenance
3. Shared layer for all libs/ code and common runtime dependencies
4. Single deployment packages with service code + runtime dependencies only
5. Automatic exclusion of dev dependencies from both optional-dependencies.dev and dependency-groups.dev
6. Comprehensive dependency filtering ensures production-ready ZIP files
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
SERVICES_DIR = PROJECT_ROOT / "services"
LIBS_DIR = PROJECT_ROOT / "libs"
OUTPUT_DIR = PROJECT_ROOT / "build" / "zip"

# Categories of dependencies that should be excluded from runtime packages
DEV_DEPENDENCY_CATEGORIES = {
    "build",
    "dev",
    "test",
    "lint",
    "format",
    "type",
    "doc",
    "coverage",
    "debug",
    "optional-dependencies",
}

# Runtime-only dependencies that should be included even if they might appear in dev contexts
RUNTIME_WHITELIST = {
    "pydantic",
    "aws-lambda-powertools",
    "typing-extensions",  # Actually needed at runtime for some packages
}

# File patterns to exclude from ZIP
EXCLUDE_PATTERNS = {
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    ".git*",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
    "*.log",
    "tests",
    "test_*",
    "*_test.py",
    "conftest.py",
    "README*",
    "CHANGELOG*",
    "LICENSE*",
    "*.md",
    ".env*",
    "Dockerfile*",
    "docker-compose*",
    ".terraform*",
    "terraform.tfstate*",
    "*.tf",
    "*.tfvars",
    ".vscode",
    ".idea",
    "node_modules",
    ".venv",
    "venv",
    "*.dist-info",
    "*.egg-info",
    "libs",  # Exclude libs/ directory from service packages (moved to shared layer)
}


class ZipBuilder:
    """Builds optimized ZIP packages for AWS Lambda deployment."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.temp_dir = Path(tempfile.mkdtemp(prefix="lambda_build_"))

    def cleanup(self):
        """Clean up temporary directories."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def run_command(self, cmd: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
        return result

    def _extract_package_name(self, dep_string: str) -> str:
        """Extract package name from dependency string (ignores version specifiers and extras)."""
        # Remove any environment markers and extras
        for sep in ['<', '>', '=', '!', '[', ';']:
            if sep in dep_string:
                dep_string = dep_string.split(sep)[0].strip()

        # Handle version specifiers like >=1.0.0
        for spec in ['>=', '<=', '==', '!=', '>', '<', '~=']:
            if spec in dep_string:
                dep_string = dep_string.split(spec)[0].strip()

        return dep_string.strip()

    def _get_dev_dependencies(self) -> set[str]:
        """Dynamically scan all pyproject.toml files to identify development dependencies."""
        dev_deps = set()
        pyproject_files = []

        # Find all pyproject.toml files in the project
        pyproject_files.append(PROJECT_ROOT / "pyproject.toml")
        pyproject_files.extend(PROJECT_ROOT.rglob("pyproject.toml"))

        print(f"Scanning {len(pyproject_files)} pyproject.toml files for dev dependencies...")

        # Create a temporary Python script to parse all pyproject.toml files
        pyproject_paths = [str(p) for p in pyproject_files]
        parser_script = f'''
import tomllib
import sys
import re

def is_dev_dependency(dep_group_name):
    """Check if a dependency group name indicates dev dependencies."""
    dev_indicators = {list(DEV_DEPENDENCY_CATEGORIES)}
    return any(indicator in dep_group_name.lower() for indicator in dev_indicators)

def parse_all_pyprojects(file_paths):
    all_dev_deps = set()

    for file_path in file_paths:
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            # Check optional-dependencies for dev-related groups
            opt_deps = data.get("project", {{}}).get("optional-dependencies", {{}})
            for group_name, deps in opt_deps.items():
                if is_dev_dependency(group_name):
                    for dep in deps:
                        all_dev_deps.add(dep.strip())

            # Check dependency-groups (new format)
            dep_groups = data.get("dependency-groups", {{}})
            for group_name, deps in dep_groups.items():
                if is_dev_dependency(group_name):
                    for dep in deps:
                        all_dev_deps.add(dep.strip())

            # Check root dependencies that might be dev-only (like uv, click, etc.)
            root_deps = data.get("project", {{}}).get("dependencies", [])
            for dep in root_deps:
                package_name = dep.strip().split(">=")[0].split("==")[0].split("<")[0].split(">")[0].split("!=")[0].split("~=")[0].strip()

                # Known orchestration/build packages that aren't needed in Lambda runtime
                orchestration_packages = {{
                    "uv", "click", "rich", "pyyaml", "docker", "gitpython",
                    "build", "setuptools", "wheel", "pip", "hatchling", "twine",
                    "boto3", "awscli", "aws-sam-cli", "moto"
                }}
                if package_name in orchestration_packages:
                    all_dev_deps.add(dep.strip())

        except Exception as e:
            print(f"Error parsing {{file_path}}: {{e}}", file=sys.stderr)

    # Print all discovered dev dependencies
    for dep in sorted(all_dev_deps):
        print(dep)

if __name__ == "__main__":
    parse_all_pyprojects({pyproject_paths})
'''

        # Write the parser script to a temporary file
        temp_script = self.temp_dir / "scan_dev_deps.py"
        with open(temp_script, 'w') as f:
            f.write(parser_script)

        # Run the script
        result = self.run_command([sys.executable, str(temp_script)])

        for line in result.stdout.strip().split('\n'):
            if line and line.strip():
                dev_deps.add(line.strip())

        print(f"Discovered {len(dev_deps)} development dependencies to exclude")
        return dev_deps

    def get_service_dependencies(self, service_path: Path) -> set[str]:
        """Get runtime dependencies for a service from its pyproject.toml (dev dependencies excluded)."""
        pyproject_path = service_path / "pyproject.toml"
        if not pyproject_path.exists():
            return set()

        # Get the dynamic list of dev dependencies to exclude
        exclude_dev_deps = self._get_dev_dependencies()

        print(f"\nFiltering dependencies for {service_path.name}...")

        # Create a temporary Python script to parse dependencies
        parser_script = f'''
import tomllib
import sys
import re

def parse_deps(file_path):
    dependencies = []

    try:
        with open("{pyproject_path}", "rb") as f:
            data = tomllib.load(f)

        # Get runtime dependencies only
        deps = data.get("project", {{}}).get("dependencies", [])
        for dep in deps:
            # Skip workspace dependencies (like fips-psn-common)
            if not dep.startswith("fips-psn-"):
                print(f"RUNTIME: {{dep.strip()}}")

    except ImportError:
        try:
            import tomli
            with open("{pyproject_path}", "rb") as f:
                data = tomli.load(f)

            deps = data.get("project", {{}}).get("dependencies", [])
            for dep in deps:
                if not dep.startswith("fips-psn-"):
                    print(f"RUNTIME: {{dep.strip()}}")

        except ImportError:
            print("tomllib/tomli not available, using fallback", file=sys.stderr)
            with open("{pyproject_path}", "r") as f:
                content = f.read()

            # Parse main dependencies
            deps_match = re.search(r"dependencies\\s*=\\s*\\[(.*?)\\]", content, re.DOTALL)
            if deps_match:
                deps_str = deps_match.group(1)
                deps = re.findall(r'"([^"]+)"', deps_str)
                for dep in deps:
                    if not dep.startswith('#') and not dep.startswith("fips-psn-"):
                        print(f"RUNTIME: {{dep.strip()}}")

if __name__ == "__main__":
    parse_deps("{pyproject_path}")
'''

        # Write the parser script to a temporary file
        temp_script = self.temp_dir / "parse_deps.py"
        with open(temp_script, 'w') as f:
            f.write(parser_script)

        # Run the script
        result = self.run_command([sys.executable, str(temp_script)])

        dependencies = set()
        excluded_packages = set()

        for line in result.stdout.strip().split('\n'):
            if line and not line.startswith('#') and line.strip():
                if line.startswith("RUNTIME:"):
                    dep = line[8:].strip()  # Remove "RUNTIME: " prefix
                    package_name = self._extract_package_name(dep)

                    # Check if this package should be excluded (dynamic check)
                    if dep in exclude_dev_deps and package_name not in RUNTIME_WHITELIST:
                        excluded_packages.add(dep)
                        print(f"Excluded dependency: {dep}", file=sys.stderr)
                    else:
                        dependencies.add(dep)

        if excluded_packages:
            print(f"Excluded {len(excluded_packages)} development dependencies: {', '.join(sorted(excluded_packages))}", file=sys.stderr)

        return dependencies

    def _get_root_dependencies(self) -> set[str]:
        """Get runtime dependencies from root pyproject.toml."""
        root_pyproject = PROJECT_ROOT / "pyproject.toml"
        if not root_pyproject.exists():
            return set()

        # Create a temporary Python script to parse root dependencies
        parser_script = f'''
import tomllib
import sys

def parse_root_deps(file_path):
    dependencies = []

    try:
        with open("{root_pyproject}", "rb") as f:
            data = tomllib.load(f)
        deps = data.get("project", {{}}).get("dependencies", [])
        for dep in deps:
            print(dep.strip())
    except ImportError:
        try:
            import tomli
            with open("{root_pyproject}", "rb") as f:
                data = tomli.load(f)
            deps = data.get("project", {{}}).get("dependencies", [])
            for dep in deps:
                print(dep.strip())
        except ImportError:
            print("tomllib/tomli not available", file=sys.stderr)

if __name__ == "__main__":
    parse_root_deps("{root_pyproject}")
'''

        # Write the parser script to a temporary file
        temp_script = self.temp_dir / "parse_root_deps.py"
        with open(temp_script, 'w') as f:
            f.write(parser_script)

        # Run the script
        result = self.run_command([sys.executable, str(temp_script)])

        dependencies = set()
        for line in result.stdout.strip().split('\n'):
            if line and not line.startswith('#') and line.strip():
                dep = line.strip()
                dependencies.add(dep)

        return dependencies

    def _install_dependencies_to_layer(self, dependencies: set[str], target_dir: Path):
        """Install dependencies to the layer directory."""
        if not dependencies:
            return

        print(f"Installing {len(dependencies)} root dependencies to shared layer")

        # Install dependencies to layer directory
        pip_cmd = [
            "pip", "install",
            "--target", str(target_dir),
            "--no-cache-dir",
            "--upgrade",
            "--only-binary=:all:",
        ] + list(dependencies)

        # Try using pip directly, fallback to python -m pip
        try:
            self.run_command(pip_cmd)
        except subprocess.CalledProcessError:
            pip_cmd = [
                sys.executable, "-m", "pip", "install",
                "--target", str(target_dir),
                "--no-cache-dir",
                "--upgrade",
                "--only-binary=:all:",
            ] + list(dependencies)
            self.run_command(pip_cmd)

        # Remove unnecessary files
        self._cleanup_directory(target_dir)

    def create_shared_layer(self, include_root_deps: bool = True) -> Path:
        """Create a shared layer containing all libs code and root dependencies."""
        print("Creating shared layer")

        layer_dir = self.temp_dir / "layers" / "shared"
        python_dir = layer_dir / "python"
        python_dir.mkdir(parents=True, exist_ok=True)

        # Copy all libs to the layer
        for lib_dir in LIBS_DIR.iterdir():
            if lib_dir.is_dir() and lib_dir.name != "__pycache__":
                dest_dir = python_dir / lib_dir.name
                self._copy_directory(lib_dir / "src", dest_dir)

        # Include root pyproject.toml dependencies if requested
        if include_root_deps:
            root_deps = self._get_root_dependencies()
            if root_deps:
                self._install_dependencies_to_layer(root_deps, python_dir)

        # Create layer ZIP
        return self._create_zip(layer_dir, "shared-layer.zip")

    def create_lambda_layer(
        self,
        layer_name: str,
        dependencies: set[str],
        python_dir: str = "python"
    ) -> Path:
        """Create a Lambda layer ZIP with specified dependencies."""
        print(f"Creating Lambda layer: {layer_name}")

        layer_dir = self.temp_dir / "layers" / layer_name
        python_dir = layer_dir / "python"
        python_dir.mkdir(parents=True, exist_ok=True)

        if not dependencies:
            print(f"No dependencies for layer {layer_name}")
            return self._create_zip(layer_dir, f"{layer_name}.zip")

        # Install dependencies to layer directory
        pip_cmd = [
            "pip", "install",
            "--target", str(python_dir),
            "--no-cache-dir",
            "--upgrade",
            "--only-binary=:all:",
        ] + list(dependencies)

        # Try using pip directly, fallback to python -m pip
        try:
            self.run_command(pip_cmd)
        except subprocess.CalledProcessError:
            pip_cmd = [
                sys.executable, "-m", "pip", "install",
                "--target", str(python_dir),
                "--no-cache-dir",
                "--upgrade",
                "--only-binary=:all:",
            ] + list(dependencies)
            self.run_command(pip_cmd)

        # Remove unnecessary files
        self._cleanup_directory(python_dir)

        # Create layer ZIP
        return self._create_zip(layer_dir, f"{layer_name}.zip")

    def create_service_package(self, service_name: str) -> Path:
        """Create a deployment package for a specific service (source code only)."""
        print(f"Creating service package: {service_name}")

        service_path = SERVICES_DIR / service_name
        if not service_path.exists():
            raise FileNotFoundError(f"Service directory not found: {service_path}")

        service_build_dir = self.temp_dir / "services" / service_name
        service_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy only the service source code (exclude libs)
        src_dir = service_path / "src"
        if src_dir.exists():
            self._copy_directory(src_dir, service_build_dir)

        # Create service ZIP (temporary, will be combined)
        # Use temp name to avoid conflict with final zip
        return self._create_zip(service_build_dir, f"{service_name}_temp.zip")

    def combine_zip_files(self, service_name: str, service_zip: Path, deps_zip: Path = None) -> Path:
        """Combine service zip and dependencies zip into a single deployment package."""
        print(f"Combining ZIP files for {service_name}")

        final_zip_path = self.output_dir / f"{service_name}.zip"

        with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as final_zip:
            # Add service files first
            with zipfile.ZipFile(service_zip, 'r') as service_zip_file:
                for file_info in service_zip_file.infolist():
                    final_zip.writestr(file_info, service_zip_file.read(file_info.filename))

            # Add dependency files if provided
            if deps_zip:
                with zipfile.ZipFile(deps_zip, 'r') as deps_zip_file:
                    for file_info in deps_zip_file.infolist():
                        final_zip.writestr(file_info, deps_zip_file.read(file_info.filename))

                # Remove the deps zip since it's now combined
                if deps_zip.exists():
                    deps_zip.unlink()

        # Print final ZIP size
        size_mb = final_zip_path.stat().st_size / (1024 * 1024)
        print(f"Created final ZIP: {final_zip_path.name} ({size_mb:.2f} MB)")

        # Remove the temporary service zip since it's now combined
        if service_zip.exists():
            service_zip.unlink()

        return final_zip_path

    def _copy_directory(self, src: Path, dst: Path):
        """Copy directory while excluding unnecessary files."""
        if not src.exists():
            return

        dst.mkdir(parents=True, exist_ok=True)

        for item in src.iterdir():
            # Skip excluded patterns
            if any(self._matches_pattern(item.name, pattern) for pattern in EXCLUDE_PATTERNS):
                continue

            if item.is_file():
                dst_file = dst / item.name
                shutil.copy2(item, dst_file)
            elif item.is_dir():
                # Recursively copy subdirectories
                self._copy_directory(item, dst / item.name)

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a pattern."""
        if pattern.startswith('*'):
            return filename.endswith(pattern[1:])
        elif pattern.endswith('*'):
            return filename.startswith(pattern[:-1])
        else:
            return pattern in filename

    def _cleanup_directory(self, dir_path: Path):
        """Remove unnecessary files from directory."""
        for pattern in EXCLUDE_PATTERNS:
            for item in dir_path.rglob(pattern):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

        # Remove .dist-info and .egg-info directories
        for info_dir in dir_path.rglob("*.dist-info"):
            if info_dir.is_dir():
                shutil.rmtree(info_dir)

        for info_dir in dir_path.rglob("*.egg-info"):
            if info_dir.is_dir():
                shutil.rmtree(info_dir)

    def _create_zip(self, source_dir: Path, zip_name: str) -> Path:
        """Create a ZIP file from directory."""
        output_file = self.output_dir / zip_name
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Creating ZIP: {output_file}")

        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for ZIP
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

        # Print ZIP size
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"Created {zip_name}: {size_mb:.2f} MB")

        return output_file

    def build_all(
        self,
        services: list[str] = None,
        include_shared_layer: bool = True
    ) -> dict[str, Path]:
        """Build all packages and layers."""
        results = {}

        # Determine which services to build
        if services is None:
            services = [d.name for d in SERVICES_DIR.iterdir() if d.is_dir() and (d / "src").exists()]

        print(f"Building services: {services}")

        # Create shared layer
        if include_shared_layer:
            shared_layer = self.create_shared_layer(include_root_deps=True)
            results["shared_layer"] = shared_layer

        # Build each service individually
        for service in services:
            service_path = SERVICES_DIR / service
            print(f"\n--- Building {service} ---")

            # Get service dependencies
            deps = self.get_service_dependencies(service_path)
            print(f"Dependencies for {service}: {deps}")

            # Create service package (source code only)
            service_zip = self.create_service_package(service)

            # Create dependencies layer if there are dependencies
            if deps:
                deps_layer = self.create_lambda_layer(f"{service}-deps", deps)

                # Combine service and dependencies into single zip
                final_zip = self.combine_zip_files(service, service_zip, deps_layer)
                results[f"{service}_package"] = final_zip
            else:
                # No dependencies, just use service zip as final package
                final_zip = self.combine_zip_files(service, service_zip)
                results[f"{service}_package"] = final_zip

        # Generate deployment info
        self._generate_deployment_info(results, services)

        return results

    def _generate_deployment_info(self, results: dict[str, Path], services: list[str]):
        """Generate deployment information file."""
        deployment_info = {
            "services": {},
            "layers": {},
            "deployment_order": []
        }

        # Add service information
        for service in services:
            package_key = f"{service}_package"

            # Get full dependency strings from pyproject.toml
            deps = self.get_service_dependencies(SERVICES_DIR / service)

            service_info = {
                "package": str(results[package_key]) if package_key in results else None,
                "dependencies": list(deps)
            }

            deployment_info["services"][service] = service_info
            deployment_info["deployment_order"].append(service)

        # Add shared layer if exists
        if "shared_layer" in results:
            deployment_info["layers"]["shared"] = str(results["shared_layer"])

        # Write deployment info
        info_file = self.output_dir / "deployment_info.json"
        with open(info_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)

        print(f"\nDeployment info written to: {info_file}")

        # Print summary
        print("\nBuild Summary:")
        print("=" * 50)
        for name, path in results.items():
            if path.exists():  # Check if file still exists (temp files might be deleted)
                size_mb = path.stat().st_size / (1024 * 1024)
                print(f"{name:30} {size_mb:6.2f} MB  {path.name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build ZIP packages for AWS Lambda deployment"
    )
    parser.add_argument(
        "--services",
        nargs="*",
        help="Specific services to build (default: all services)",
        default=None
    )
    parser.add_argument(
        "--no-shared-layer",
        action="store_true",
        help="Skip creating a shared layer for libraries and root dependencies"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory for ZIP files (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before building"
    )

    args = parser.parse_args()

    builder = ZipBuilder(args.output_dir)

    try:
        # Clean output directory if requested
        if args.clean and args.output_dir.exists():
            shutil.rmtree(args.output_dir)
            print(f"Cleaned output directory: {args.output_dir}")

        # Build packages
        results = builder.build_all(
            services=args.services,
            include_shared_layer=not args.no_shared_layer
        )

        print("\nBuild completed successfully!")
        print(f"Output directory: {args.output_dir}")

        # Print next steps
        print("\nNext Steps:")
        if "shared_layer" in results:
            print("1. Upload shared layer to AWS Lambda:")
            print(f"   aws lambda publish-layer-version --layer-name shared --zip-file fileb://{results['shared_layer']}")

        print("\n2. Update Lambda functions:")
        for service in args.services or [d.name for d in SERVICES_DIR.iterdir() if d.is_dir() and (d / "src").exists()]:
            package_key = f"{service}_package"
            if package_key in results:
                print(f"   - Update {service} function code:")
                print(f"     aws lambda update-function-code --function-name {service} --zip-file fileb://{results[package_key]}")

    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    finally:
        builder.cleanup()


if __name__ == "__main__":
    main()