#!/usr/bin/env python3
"""
ZIP-based Lambda build script for PSN Partner Emulator Service.

This script builds optimized ZIP packages for AWS Lambda deployment with:
- Separate Lambda layers for shared dependencies
- Minimal deployment packages with only runtime dependencies
- Cross-platform support (Windows/Linux/macOS)
- Dependency analysis to exclude unnecessary packages

Best practices implemented:
1. Shared common layer for frequently used dependencies
2. Per-Lambda layers for service-specific dependencies
3. Minimal source code packages
4. Exclusion of dev dependencies, test files, and documentation
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
from typing import Dict, List, Set

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
SERVICES_DIR = PROJECT_ROOT / "services"
LIBS_DIR = PROJECT_ROOT / "libs"
OUTPUT_DIR = PROJECT_ROOT / "build" / "zip"

# Core dependencies that should go in a common layer (truly shared across all services)
SHARED_DEPENDENCIES = {
    "aws-lambda-powertools",  # Core logging and utilities used by all services
    "typing-extensions",      # Python typing extensions
}

# Dependencies that should be packaged per-service (even if multiple services use them)
SERVICE_SPECIFIC_DEPENDENCIES = {
    "pydantic",              # Often used with different extras [email], etc.
    "pydantic-core",         # Core pydantic
    "annotated-types",       # Pydantic typing support
    "email-validator",       # Email validation (pydantic[email])
    "idna",                  # IDNA encoding (pydantic[email])
}

# Dependencies to exclude from packages (dev/test only)
EXCLUDE_DEPENDENCIES = {
    "pytest",
    "pytest-cov",
    "pytest-mock",
    "pytest-xdist",
    "black",
    "ruff",
    "mypy",
    "isort",
    "bandit",
    "pre-commit",
    "build",
    "setuptools",
    "wheel",
    "pip",
    "uv",
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

    def run_command(self, cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
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

    def get_service_dependencies(self, service_path: Path) -> Set[str]:
        """Get runtime dependencies for a service."""
        pyproject_path = service_path / "pyproject.toml"
        if not pyproject_path.exists():
            return set()

        # Create a temporary Python script to parse dependencies and extract version specs
        parser_script = f'''
import tomllib
import sys
import re

def parse_deps(file_path):
    dependencies = []

    try:
        with open("{pyproject_path}", "rb") as f:
            data = tomllib.load(f)
        deps = data.get("project", {{}}).get("dependencies", [])
        for dep in deps:
            # Keep the full dependency string with version specifiers
            print(dep.strip())
    except ImportError:
        try:
            import tomli
            with open("{pyproject_path}", "rb") as f:
                data = tomli.load(f)
            deps = data.get("project", {{}}).get("dependencies", [])
            for dep in deps:
                print(dep.strip())
        except ImportError:
            print("tomllib/tomli not available, using fallback", file=sys.stderr)
            # Fallback: parse with regex
            with open("{pyproject_path}", "r") as f:
                content = f.read()
            # Find dependencies in the dependencies array
            deps_match = re.search(r"dependencies\\s*=\\s*\\[(.*?)\\]", content, re.DOTALL)
            if deps_match:
                deps_str = deps_match.group(1)
                # Extract dependency strings with quotes
                deps = re.findall(r'"([^"]+)"', deps_str)
                for dep in deps:
                    if not dep.startswith('#') and '=' in dep:
                        print(dep.strip())

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
        for line in result.stdout.strip().split('\n'):
            if line and not line.startswith('#') and line.strip():
                dependencies.add(line.strip())

        # Filter out dev dependencies
        return dependencies - EXCLUDE_DEPENDENCIES

    def create_lambda_layer(
        self,
        layer_name: str,
        dependencies: Set[str],
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
        """Create a deployment package for a specific service."""
        print(f"Creating service package: {service_name}")

        service_path = SERVICES_DIR / service_name
        if not service_path.exists():
            raise FileNotFoundError(f"Service directory not found: {service_path}")

        service_build_dir = self.temp_dir / "services" / service_name
        service_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy source code
        src_dir = service_path / "src"
        if src_dir.exists():
            self._copy_directory(src_dir, service_build_dir)

        # Copy common library
        common_src = LIBS_DIR / "common" / "src"
        if common_src.exists():
            libs_dir = service_build_dir / "libs"
            self._copy_directory(common_src, libs_dir / "common")

        # Create service ZIP
        return self._create_zip(service_build_dir, f"{service_name}.zip")

    def _copy_directory(self, src: Path, dst: Path):
        """Copy directory while excluding unnecessary files."""
        dst.mkdir(parents=True, exist_ok=True)

        for item in src.iterdir():
            # Skip excluded patterns
            if any(pattern.replace('*', '') in item.name for pattern in EXCLUDE_PATTERNS):
                continue

            if item.is_file():
                # Skip files matching exclude patterns
                if any(pattern.replace('*', '') in item.name for pattern in EXCLUDE_PATTERNS):
                    continue

                dst_file = dst / item.name
                shutil.copy2(item, dst_file)
            elif item.is_dir():
                # Recursively copy subdirectories
                self._copy_directory(item, dst / item.name)

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
        services: List[str] = None,
        include_common_layer: bool = True
    ) -> Dict[str, Path]:
        """Build all packages and layers."""
        results = {}

        # Determine which services to build
        if services is None:
            services = [d.name for d in SERVICES_DIR.iterdir() if d.is_dir() and (d / "src").exists()]

        print(f"Building services: {services}")

        # Analyze dependencies for each service
        service_dependencies = {}
        all_shared_deps = set()

        for service in services:
            deps = self.get_service_dependencies(SERVICES_DIR / service)
            service_dependencies[service] = deps

            # Extract package names from full dependency strings to identify shared deps
            package_names = set()
            for dep in deps:
                # Extract package name before any version specifiers or brackets
                import re
                package_name = re.split(r'[<>=~![]', dep)[0].strip()
                if package_name:
                    package_names.add(package_name)

            # Find shared dependencies among all services
            shared_package_names = package_names & SHARED_DEPENDENCIES
            all_shared_deps.update(shared_package_names)

        # Create common layer for truly shared dependencies
        if include_common_layer and all_shared_deps:
            common_layer = self.create_lambda_layer("common", all_shared_deps)
            results["common_layer"] = common_layer

        # Create service-specific layers with remaining dependencies
        for service in services:
            deps = service_dependencies[service]
            if deps:
                # Filter out dependencies that went to common layer
                remaining_deps = []
                for dep in deps:
                    import re
                    package_name = re.split(r'[<>=~![]', dep)[0].strip()
                    if package_name not in all_shared_deps:
                        remaining_deps.append(dep)

                if remaining_deps:
                    layer_name = f"{service}-deps"
                    layer = self.create_lambda_layer(layer_name, remaining_deps)
                    results[f"{service}_layer"] = layer

        # Create service packages (source code only)
        for service in services:
            package = self.create_service_package(service)
            results[f"{service}_package"] = package

        # Generate deployment info
        self._generate_deployment_info(results, services)

        return results

    def _generate_deployment_info(self, results: Dict[str, Path], services: List[str]):
        """Generate deployment information file."""
        deployment_info = {
            "services": {},
            "layers": {},
            "deployment_order": []
        }

        # Add service information
        for service in services:
            package_key = f"{service}_package"
            layer_key = f"{service}_layer"

            # Get full dependency strings from pyproject.toml
            deps = self.get_service_dependencies(SERVICES_DIR / service)

            service_info = {
                "package": str(results[package_key]) if package_key in results else None,
                "layer": str(results[layer_key]) if layer_key in results else None,
                "dependencies": list(deps)
            }

            deployment_info["services"][service] = service_info
            deployment_info["deployment_order"].append(service)

        # Add common layer if exists
        if "common_layer" in results:
            deployment_info["layers"]["common"] = str(results["common_layer"])

        # Write deployment info
        info_file = self.output_dir / "deployment_info.json"
        with open(info_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)

        print(f"\nDeployment info written to: {info_file}")

        # Print summary
        print("\nBuild Summary:")
        print("=" * 50)
        for name, path in results.items():
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
        "--no-common-layer",
        action="store_true",
        help="Skip creating a common layer for shared dependencies"
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
            include_common_layer=not args.no_common_layer
        )

        print("\nBuild completed successfully!")
        print(f"Output directory: {args.output_dir}")

        # Print next steps
        print("\nNext Steps:")
        print("1. Upload layers to AWS Lambda:")
        for name, path in results.items():
            if "layer" in name:
                print(f"   aws lambda publish-layer-version --layer-name {name.replace('_layer', '')} --zip-file fileb://{path}")

        print("\n2. Update Lambda functions to use layers:")
        print("   - Common layer: Add to all Lambda functions")
        for service in args.services or [d.name for d in SERVICES_DIR.iterdir() if d.is_dir()]:
            print(f"   - {service} layer: Add to {service} Lambda function")

        print("\n3. Update function code:")
        for name, path in results.items():
            if "package" in name:
                service_name = name.replace("_package", "")
                print(f"   aws lambda update-function-code --function-name {service_name} --zip-file fileb://{path}")

    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    finally:
        builder.cleanup()


if __name__ == "__main__":
    main()