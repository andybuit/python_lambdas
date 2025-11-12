#!/usr/bin/env python3
"""
Consolidated build script for PSN Emulator Lambda services.
Works on Windows, Linux, and macOS.

Usage:
    python scripts/build.py [options]

Options:
    --service, -s   Service to build: idp_api, player_account_api etc, or all (default: all)
    --tag, -t       Docker image tag (default: latest)
    --platform      Target platform (default: linux/amd64)
    --no-cache      Build without using cache
    --push          Push image to ECR after building
    --ecr-repo-map   JSON mapping of service names to ECR repository URIs (required if --push is used)
                    Format: '{"idp_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-idp-api", ...}'
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=False)
    return result


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


def get_service_config(service_name: str, project_root: Path) -> dict[str, str]:
    """Get configuration for a specific service dynamically."""
    service_path = project_root / "services" / service_name

    if not service_path.exists():
        raise ValueError(f"Unknown service: {service_name}")

    # Generate image name from service name (snake_case to kebab-case)
    image_name = f"fips-psn-{service_name.replace('_', '-')}"

    # Generate display name (snake_case to Title Case)
    display_name = " ".join(word.title() for word in service_name.split("_"))

    return {
        "service_dir": service_name,
        "image_name": image_name,
        "display_name": display_name,
    }


def build_docker_image(
    service_name: str,
    tag: str,
    platform: str,
    no_cache: bool,
    project_root: Path,
) -> int:
    """Build the Docker image for a specific service."""
    config = get_service_config(service_name, project_root)

    print(f"\n{'='*60}")
    print(f"Building {config['display_name']} Lambda Docker Image")
    print(f"{'='*60}")
    print(f"Project root: {project_root}")
    print(f"Image name: {config['image_name']}:{tag}")
    print(f"Platform: {platform}")
    print(f"{'='*60}\n")

    # Build the Docker image
    build_cmd = [
        "docker",
        "build",
        "-f",
        str(project_root / "services" / config["service_dir"] / "Dockerfile"),
        "-t",
        f"{config['image_name']}:{tag}",
        "--platform",
        platform,
    ]

    if no_cache:
        build_cmd.append("--no-cache")

    # Add project root as build context
    build_cmd.append(str(project_root))

    try:
        run_command(build_cmd)
        print(f"\n[OK] Successfully built {config['image_name']}:{tag}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with exit code {e.returncode}")
        return e.returncode


def push_to_ecr(
    service_name: str,
    tag: str,
    ecr_repo_map: dict[str, str],
    project_root: Path,
) -> int:
    """Push the Docker image to ECR."""
    config = get_service_config(service_name, project_root)

    if service_name not in ecr_repo_map:
        print(f"\n[ERROR] No ECR repository found for service '{service_name}'")
        return 1

    ecr_repo = ecr_repo_map[service_name]

    print(f"\n{'='*60}")
    print(f"Pushing {config['display_name']} to ECR")
    print(f"{'='*60}\n")

    # Tag the image for ECR
    ecr_image = f"{ecr_repo}:{tag}"
    tag_cmd = ["docker", "tag", f"{config['image_name']}:{tag}", ecr_image]

    try:
        run_command(tag_cmd)
        print(f"[OK] Tagged image as {ecr_image}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to tag image: {e}")
        return e.returncode

    # Push to ECR
    push_cmd = ["docker", "push", ecr_image]

    try:
        run_command(push_cmd)
        print(f"\n[OK] Successfully pushed {ecr_image}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Push failed: {e}")
        return e.returncode


def build_services(
    services: list[str],
    tag: str,
    platform: str,
    no_cache: bool,
    push: bool,
    ecr_repo_map: dict[str, str] | None,
) -> int:
    """Build one or more services."""
    # Get project root (this script is in scripts/, so go up one level)
    project_root = Path(__file__).parent.parent

    # Determine which services to build
    if "all" in services:
        services_to_build = discover_services(project_root)
    else:
        services_to_build = services

    print(f"\n{'='*80}")
    print("Building PSN Emulator Lambda Services")
    print(f"{'='*80}")
    print(f"Services: {', '.join(services_to_build)}")
    print(f"Tag: {tag}")
    print(f"Platform: {platform}")
    print(f"Push to ECR: {push}")
    print(f"{'='*80}\n")

    # Validate ECR configuration if pushing
    if push and not ecr_repo_map:
        print("\n[ERROR] --ecr-repo-map is required when using --push")
        return 1

    overall_exit_code = 0

    # Build each service
    for service in services_to_build:
        try:
            # Build the Docker image
            exit_code = build_docker_image(
                service_name=service,
                tag=tag,
                platform=platform,
                no_cache=no_cache,
                project_root=project_root,
            )

            if exit_code != 0:
                overall_exit_code = exit_code
                continue

            # Push to ECR if requested
            if push and ecr_repo_map:
                exit_code = push_to_ecr(
                    service_name=service,
                    tag=tag,
                    ecr_repo_map=ecr_repo_map,
                    project_root=project_root,
                )

                if exit_code != 0:
                    overall_exit_code = exit_code

        except ValueError as e:
            print(f"\n[ERROR] {e}")
            overall_exit_code = 1
        except Exception as e:
            print(f"\n[ERROR] Unexpected error building {service}: {e}")
            overall_exit_code = 1

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
        description="Build Docker images for PSN Emulator Lambda services"
    )
    parser.add_argument(
        "--service",
        "-s",
        choices=available_services + ["all"],
        nargs="+",
        default=["all"],
        help=f"Service(s) to build. Available: {', '.join(available_services)} (default: all)",
    )
    parser.add_argument(
        "--tag", "-t", default="latest", help="Docker image tag (default: latest)"
    )
    parser.add_argument(
        "--platform",
        default="linux/amd64",
        help="Target platform (default: linux/amd64)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Build without using cache"
    )
    parser.add_argument(
        "--push", action="store_true", help="Push images to ECR after building"
    )
    parser.add_argument(
        "--ecr-repo-map",
        help="JSON mapping of service names to ECR repository URIs (required if --push is used)",
    )

    args = parser.parse_args()

    # Parse ECR repository map if provided
    ecr_repo_map = None
    if args.ecr_repo_map:
        try:
            ecr_repo_map = json.loads(args.ecr_repo_map)
        except json.JSONDecodeError as e:
            print(f"\n[ERROR] Error parsing ECR repo map: {e}")
            return 1

    return build_services(
        services=args.service,
        tag=args.tag,
        platform=args.platform,
        no_cache=args.no_cache,
        push=args.push,
        ecr_repo_map=ecr_repo_map,
    )


if __name__ == "__main__":
    sys.exit(main())
