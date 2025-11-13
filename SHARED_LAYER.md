# Shared Layer Deployment Guide

This document explains how to use the shared layer (`shared-layer.zip`) for ZIP-based Lambda deployment in the PSN Partner Emulator Service.

## Overview

The shared layer contains:
- **Common Libraries**: All code from `libs/` directory (`common/` library)
- **Root Dependencies**: All dependencies from the root `pyproject.toml` file (uv, click, rich, pyyaml, docker, gitpython)

This approach allows Lambda functions to share common code and dependencies, reducing deployment package sizes and ensuring consistency across functions.

## Architecture

```
shared-layer.zip (Lambda Layer)
├── python/
│   ├── common/              # From libs/common/src/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── logger.py
│   │   └── models.py
│   ├── uv/                  # From root pyproject.toml
│   ├── click/               # From root pyproject.toml
│   ├── rich/                # From root pyproject.toml
│   ├── pyyaml/              # From root pyproject.toml
│   ├── docker/              # From root pyproject.toml
│   └── gitpython/           # From root pyproject.toml

idp_api.zip (Lambda Function Code)
├── handler.py               # Lambda entry point
├── service.py               # Business logic
├── models.py                # Request/response models
└── __init__.py

player_account_api.zip (Lambda Function Code)
├── handler.py               # Lambda entry point
├── service.py               # Business logic
├── models.py                # Request/response models
└── __init__.py
```

## Building ZIP Packages

### Build All Services with Shared Layer

```bash
# Build all services with shared layer
python scripts/build_zip.py --clean

# Build specific services only
python scripts/build_zip.py --services idp_api player_account_api --clean

# Build without shared layer (not recommended)
python scripts/build_zip.py --no-shared-layer
```

### Output Files

The build process creates these files in `build/zip/`:
- `shared-layer.zip` - Shared layer containing libs/ code and root dependencies
- `idp_api.zip` - IDP API Lambda function code
- `player_account_api.zip` - Player Account API Lambda function code
- `deployment_info.json` - Deployment metadata

## AWS Deployment

### Step 1: Upload Shared Layer

```bash
# Upload shared layer to AWS Lambda
aws lambda publish-layer-version \
  --layer-name psn-emulator-dev-shared \
  --zip-file fileb://build/zip/shared-layer.zip \
  --compatible-runtimes python3.13 \
  --description "Shared layer containing common libraries and root dependencies"
```

### Step 2: Update Lambda Functions

```bash
# Update IDP API Lambda function
aws lambda update-function-code \
  --function-name psn-emulator-dev-idp-api \
  --zip-file fileb://build/zip/idp_api.zip

# Update Player Account API Lambda function
aws lambda update-function-code \
  --function-name psn-emulator-dev-player-account-api \
  --zip-file fileb://build/zip/player_account_api.zip
```

### Step 3: Attach Layer to Functions

```bash
# Get the latest layer version
LAYER_VERSION=$(aws lambda list-layer-versions --layer-name psn-emulator-dev-shared --query 'LayerVersions[0].Version' --output text)

# Attach shared layer to IDP API
aws lambda update-function-configuration \
  --function-name psn-emulator-dev-idp-api \
  --layers "arn:aws:lambda:us-east-1:123456789012:layer:psn-emulator-dev-shared:${LAYER_VERSION}"

# Attach shared layer to Player Account API
aws lambda update-function-configuration \
  --function-name psn-emulator-dev-player-account-api \
  --layers "arn:aws:lambda:us-east-1:123456789012:layer:psn-emulator-dev-shared:${LAYER_VERSION}"
```

## Terraform Deployment

### Using ZIP-based Deployment

1. **Enable ZIP deployment** in your `terraform.tfvars`:

```hcl
use_zip_deployment = true
```

2. **Set paths to built ZIP files**:

```hcl
shared_layer_zip_path     = "../../build/zip/shared-layer.zip"
idp_api_zip_path         = "../../build/zip/idp_api.zip"
player_account_api_zip_path = "../../build/zip/player_account_api.zip"
```

3. **Deploy infrastructure**:

```bash
cd infra/terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Using Container-based Deployment (Default)

The project defaults to container-based deployment (`use_zip_deployment = false`). In this mode:
- Lambda functions are deployed as Docker containers from ECR
- Shared layer is not used (dependencies are included in container images)
- Use `scripts/build.py` and `scripts/deploy.py` instead

## Benefits of Shared Layer

1. **Reduced Package Size**: Common code and dependencies are shared, not duplicated
2. **Consistent Dependencies**: All functions use the same versions of shared libraries
3. **Faster Deployment**: Smaller function packages upload and update faster
4. **Easier Maintenance**: Update shared code in one place, deploy layer once
5. **Cost Savings**: Smaller packages can reduce storage and transfer costs

## Layer Contents

### Common Libraries (from libs/)

- `common/exceptions.py` - Custom exception hierarchy
- `common/logger.py` - AWS Lambda Powertools logger
- `common/models.py` - Common response models

### Root Dependencies (from pyproject.toml)

- `uv>=0.5.0` - Fast Python package manager
- `click>=8.0.0` - CLI interface framework
- `rich>=13.0.0` - Rich terminal output
- `pyyaml>=6.0.0` - YAML parsing
- `docker>=7.0.0` - Docker Python SDK
- `gitpython>=3.1.0` - Git operations

## Migration Notes

### From Docker to ZIP

If migrating from container-based to ZIP-based deployment:

1. **Build ZIP packages**: `python scripts/build_zip.py --clean`
2. **Upload shared layer**: See AWS deployment steps above
3. **Update Terraform variables**: Set `use_zip_deployment = true`
4. **Deploy infrastructure**: `terraform apply`
5. **Verify functions**: Test that all imports work correctly

### Import Changes

No import changes are required. The shared layer places libraries in the Python path so that:

```python
# These imports work the same in both deployment modes
from libs.common.src.exceptions import ValidationException
from libs.common.src.logger import get_logger
from libs.common.src.models import APIResponse
```

## Troubleshooting

### Import Errors

If you get import errors after ZIP deployment:

1. **Check layer attachment**: Verify the layer is attached to the function
2. **Check layer contents**: Verify the layer contains the required files
3. **Check Python path**: Layer files should be in `/python/` directory
4. **Check runtime**: Ensure Lambda runtime is Python 3.13 or later

### Large Package Size

If packages are still large:

1. **Verify shared layer**: Ensure common dependencies are in layer, not function packages
2. **Check for exclusions**: Verify unnecessary files are excluded from ZIP
3. **Review dependencies**: Check for unused dependencies in service pyproject.toml

### Layer Version Conflicts

When updating the layer:

1. **Create new version**: Always publish new layer version, don't modify existing
2. **Update all functions**: Update all functions to use new layer version
3. **Test thoroughly**: Verify all functions work with new layer version
4. **Clean old versions**: Remove old layer versions after successful rollout

## Best Practices

1. **Version Control**: Always track layer versions in your deployment process
2. **Test Staging**: Test layer updates in a non-production environment first
3. **Monitor Performance**: Watch Lambda cold start times after layer changes
4. **Document Changes**: Keep track of what's included in each layer version
5. **Regular Updates**: Update layer dependencies regularly for security patches