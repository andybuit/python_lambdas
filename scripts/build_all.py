#!/usr/bin/env python3
"""
Cross-platform orchestration script to build all Lambda Docker images.
Works on Windows, Linux, and macOS.

Usage:
    python scripts/build_all.py [options]

Options:
    --tag, -t       Docker image tag (default: latest)
    --platform      Target platform (default: linux/amd64)
    --no-cache      Build without using cache
    --push          Push images to ECR after building
    --services      Comma-separated list of services to build (default: all)
                    Available: idp_api,player_account_api
"""

import argparse
import subprocess
import sys
from pathlib import Path

SERVICES = {
    "idp_api": {
        "name": "IDP API",
        "path": "services/idp_api",
        "script": "services/idp_api/scripts/build.py",
    },
    "player_account_api": {
        "name": "Player Account API",
        "path": "services/player_account_api",
        "script": "services/player_account_api/scripts/build.py",
    },
}


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def build_all_services(
    tag: str,
    platform: str,
    no_cache: bool,
    push: bool,
    services: list[str],
    ecr_repos: dict[str, str] | None = None,
) -> int:
    """Build all Lambda services."""
    project_root = Path(__file__).parent.parent

    print(f"\n{'='*70}")
    print("Building Lambda Docker Images")
    print(f"{'='*70}")
    print(f"Tag: {tag}")
    print(f"Platform: {platform}")
    print(f"Services: {', '.join(services)}")
    print(f"{'='*70}\n")

    results = {}

    for service_id in services:
        if service_id not in SERVICES:
            print(f"\n✗ Unknown service: {service_id}")
            results[service_id] = 1
            continue

        service = SERVICES[service_id]
        print(f"\n{'='*70}")
        print(f"Building: {service['name']}")
        print(f"{'='*70}\n")

        # Build command for individual service
        build_cmd = [
            sys.executable,
            str(project_root / service["script"]),
            "--tag",
            tag,
            "--platform",
            platform,
        ]

        if no_cache:
            build_cmd.append("--no-cache")

        if push:
            build_cmd.append("--push")
            if ecr_repos and service_id in ecr_repos:
                build_cmd.extend(["--ecr-repo", ecr_repos[service_id]])

        exit_code = run_command(build_cmd)
        results[service_id] = exit_code

        if exit_code != 0:
            print(f"\n✗ Failed to build {service['name']}")
        else:
            print(f"\n✓ Successfully built {service['name']}")

    # Print summary
    print(f"\n{'='*70}")
    print("Build Summary")
    print(f"{'='*70}")

    success_count = sum(1 for code in results.values() if code == 0)
    total_count = len(results)

    for service_id, exit_code in results.items():
        status = "✓" if exit_code == 0 else "✗"
        print(
            f"{status} {SERVICES[service_id]['name']}: {'SUCCESS' if exit_code == 0 else 'FAILED'}"
        )

    print(f"\nTotal: {success_count}/{total_count} succeeded")
    print(f"{'='*70}\n")

    # Return non-zero if any builds failed
    return 0 if all(code == 0 for code in results.values()) else 1


def get_ecr_repos_from_terraform() -> dict[str, str] | None:
    """Get ECR repository URLs from Terraform outputs."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=Path(__file__).parent.parent / "infra" / "terraform",
            capture_output=True,
            text=True,
            check=True,
        )

        import json

        outputs = json.loads(result.stdout)

        return {
            "idp_api": outputs.get("ecr_repository_idp_api", {}).get("value"),
            "player_account_api": outputs.get(
                "ecr_repository_player_account_api", {}
            ).get("value"),
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        print("\n⚠ Warning: Could not get ECR repository URLs from Terraform")
        print(
            "   Make sure to run 'terraform apply' first, or provide --ecr-repo manually"
        )
        return None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build all Lambda Docker images")
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
        "--services", help="Comma-separated list of services to build (default: all)"
    )

    args = parser.parse_args()

    # Parse services list
    if args.services:
        services = [s.strip() for s in args.services.split(",")]
    else:
        services = list(SERVICES.keys())

    # Get ECR repos if pushing
    ecr_repos = None
    if args.push:
        ecr_repos = get_ecr_repos_from_terraform()

    return build_all_services(
        tag=args.tag,
        platform=args.platform,
        no_cache=args.no_cache,
        push=args.push,
        services=services,
        ecr_repos=ecr_repos,
    )


if __name__ == "__main__":
    sys.exit(main())
