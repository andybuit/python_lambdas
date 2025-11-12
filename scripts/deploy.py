#!/usr/bin/env python3
"""
Cross-platform deployment script for Lambda functions.
Works on Windows, Linux, and macOS.

This script handles:
1. Building Docker images
2. Pushing to ECR
3. Updating Lambda functions with new images

Usage:
    python scripts/deploy.py [options]

Options:
    --tag, -t       Docker image tag (default: latest)
    --environment   Environment to deploy to (dev, test, prod)
    --services      Comma-separated list of services (default: all)
    --no-build      Skip building images (use existing local images)
    --region        AWS region (default: us-east-1)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

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


def generate_service_map(services: list[str]) -> dict[str, dict[str, str]]:
    """Generate service mapping dynamically from service names."""
    service_map = {}

    for service_name in services:
        # Generate Terraform output keys based on naming convention
        ecr_key = f"ecr_repository_{service_name}"
        lambda_key = f"{service_name}_lambda_name"

        service_map[service_name] = {
            "ecr_key": ecr_key,
            "lambda_key": lambda_key,
        }

    return service_map


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    return result


def ecr_login(region: str) -> bool:
    """Authenticate Docker to ECR."""
    print(f"\n{'='*60}")
    print("Authenticating to ECR")
    print(f"{'='*60}\n")

    try:
        # Get ECR login password
        login_result = run_command(
            ["aws", "ecr", "get-login-password", "--region", region]
        )

        # Login to ECR using the password
        subprocess.run(
            [
                "docker",
                "login",
                "--username",
                "AWS",
                "--password-stdin",
                "public.ecr.aws",
            ],
            input=login_result.stdout,
            text=True,
            check=False,
        )

        print("Successfully authenticated to ECR")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to authenticate to ECR: {e}")
        return False


def get_terraform_outputs() -> dict[str, Any]:
    """Get Terraform outputs."""
    terraform_dir = Path(__file__).parent.parent / "infra" / "terraform"

    try:
        result = run_command(["terraform", "output", "-json"], cwd=terraform_dir)
        return cast("dict[str, Any]", json.loads(result.stdout))
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Failed to get Terraform outputs: {e}")
        return {}


def update_lambda_function(function_name: str, image_uri: str, region: str) -> bool:
    """Update Lambda function with new image."""
    print(f"\nUpdating Lambda function: {function_name}")

    try:
        run_command(
            [
                "aws",
                "lambda",
                "update-function-code",
                "--function-name",
                function_name,
                "--image-uri",
                image_uri,
                "--region",
                region,
            ]
        )
        print(f"Successfully updated {function_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to update {function_name}: {e}")
        return False


def deploy(
    tag: str,
    environment: str,
    services: list[str],
    build: bool,
    region: str,
) -> int:
    """Deploy Lambda functions."""
    project_root = Path(__file__).parent.parent

    print(f"\n{'='*60}")
    print("Deploying Lambda Functions")
    print(f"{'='*60}")
    print(f"Environment: {environment}")
    print(f"Tag: {tag}")
    print(f"Region: {region}")
    print(f"Services: {', '.join(services)}")
    print(f"{'='*60}\n")

    # Step 1: Build images if requested
    if build:
        print(f"\n{'='*60}")
        print("Building Docker Images")
        print(f"{'='*60}\n")

        build_cmd = [
            sys.executable,
            str(project_root / "scripts" / "build.py"),
            "--tag",
            tag,
            "--service",
        ] + services

        result = subprocess.run(build_cmd)
        if result.returncode != 0:
            print("\nBuild failed")
            return 1

    # Step 2: Authenticate to ECR
    if not ecr_login(region):
        return 1

    # Step 3: Get Terraform outputs for ECR repos and Lambda names
    outputs = get_terraform_outputs()
    if not outputs:
        print("\nFailed to get deployment information from Terraform")
        print("   Make sure Terraform has been applied successfully")
        return 1

    # Step 4: Generate dynamic service mapping and deploy
    service_map = generate_service_map(services)

    results = {}

    for service_id in services:
        if service_id not in service_map:
            print(f"\nUnknown service: {service_id}")
            results[service_id] = False
            continue

        service = service_map[service_id]
        ecr_repo = outputs.get(service["ecr_key"], {}).get("value")
        lambda_name = outputs.get(service["lambda_key"], {}).get("value")

        if not ecr_repo or not lambda_name:
            print(f"\nMissing deployment info for {service_id}")
            results[service_id] = False
            continue

        image_uri = f"{ecr_repo}:{tag}"

        # Tag and push image
        print(f"\n{'='*60}")
        print(f"Deploying {service_id}")
        print(f"{'='*60}\n")

        local_image = f"fips-psn-{service_id.replace('_', '-')}:{tag}"

        try:
            # Tag for ECR
            run_command(["docker", "tag", local_image, image_uri])

            # Push to ECR
            run_command(["docker", "push", image_uri])

            # Update Lambda
            success = update_lambda_function(lambda_name, image_uri, region)
            results[service_id] = success

        except subprocess.CalledProcessError as e:
            print(f"\nDeployment failed for {service_id}: {e}")
            results[service_id] = False

    # Print summary
    print(f"\n{'='*60}")
    print("Deployment Summary")
    print(f"{'='*60}")

    for service_id, success in results.items():
        status = "OK" if success else "FAIL"
        print(f"{status} {service_id}: {'SUCCESS' if success else 'FAILED'}")

    success_count = sum(1 for s in results.values() if s)
    total_count = len(results)
    print(f"\nTotal: {success_count}/{total_count} succeeded")
    print(f"{'='*60}\n")

    return 0 if all(results.values()) else 1


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    try:
        available_services = discover_services(project_root)
    except FileNotFoundError:
        print("Error: Services directory not found")
        return 1

    parser = argparse.ArgumentParser(description="Deploy Lambda functions to AWS")
    parser.add_argument(
        "--tag", "-t", default="latest", help="Docker image tag (default: latest)"
    )
    parser.add_argument(
        "--environment",
        "-e",
        default="dev",
        choices=["dev", "test", "prod"],
        help="Environment to deploy to (default: dev)",
    )
    parser.add_argument(
        "--services",
        help=f"Comma-separated list of services. Available: {', '.join(available_services)} (default: all)"
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip building images (use existing local images)",
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    # Parse services
    if args.services:
        services = [s.strip() for s in args.services.split(",")]
        # Validate services against discovered ones
        for service in services:
            if service not in available_services:
                print(f"Error: Unknown service '{service}'. Available services: {', '.join(available_services)}")
                return 1
    else:
        services = available_services

    return deploy(
        tag=args.tag,
        environment=args.environment,
        services=services,
        build=not args.no_build,
        region=args.region,
    )


if __name__ == "__main__":
    sys.exit(main())
