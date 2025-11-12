# ZIP-Based Lambda Build Guide

This guide explains how to use the `scripts/build_zip.py` script to create optimized ZIP packages for AWS Lambda deployment.

## Overview

The ZIP build script creates:

1. **Lambda Layers**: Reusable packages for shared dependencies
2. **Service Packages**: Minimal ZIP files containing only source code
3. **Deployment Info**: JSON file with deployment metadata

## Benefits of ZIP + Layers Approach

### Size Optimization
- **Common Layer**: Shared dependencies (pydantic, aws-lambda-powertools) used by all Lambdas
- **Service-Specific Layers**: Dependencies unique to each service
- **Minimal Packages**: Only source code, no duplicated dependencies

### Deployment Advantages
- **Faster Updates**: Update code without redeploying dependencies
- **Version Management**: Layers can be versioned independently
- **Reduced Cold Starts**: Smaller deployment packages
- **Cost Efficiency**: Less storage and faster deployments

## Usage

### Build All Services

```bash
# From project root
python scripts/build_zip.py

# Or with uv
uv run python scripts/build_zip.py
```

### Build Specific Services

```bash
python scripts/build_zip.py --services idp_api player_account_api
```

### Options

- `--services [names]`: Build only specified services
- `--no-common-layer`: Skip creating common dependency layer
- `--output-dir path`: Custom output directory (default: `build/zip/`)
- `--clean`: Clean output directory before building

## Output Structure

```
build/zip/
├── deployment_info.json          # Deployment metadata
├── common.zip                    # Shared dependencies layer
├── idp_api-deps.zip             # IDP API specific dependencies
├── player_account_api-deps.zip  # Player Account API dependencies
├── idp_api.zip                  # IDP API source code
└── player_account_api.zip       # Player Account API source code
```

## Dependency Management

### Shared Dependencies

These dependencies are included in the common layer (truly shared across all services):
- `aws-lambda-powertools` - Core logging and utilities
- `typing-extensions` - Python typing extensions

### Service-Specific Dependencies

Dependencies that are specific to each service (even if multiple services use them):
- **IDP API**: `pydantic[email]>=2.10.0` - Includes email validation
- **Player Account API**: `pydantic[email]>=2.10.0` - Includes email validation

Note: Services get their own layers for dependencies like `pydantic` because they might use different extras or versions in the future.

### Version Management

Dependencies are installed with exact version specifications from `pyproject.toml`:
- **IDP API**: `pydantic[email]>=2.10.0`, `aws-lambda-powertools>=3.4.0`
- **Player Account API**: `pydantic[email]>=2.10.0`, `aws-lambda-powertools>=3.4.0`

This ensures consistent builds and version pinning across deployments.

### Excluded Dependencies

The following are excluded from all packages:
- Test dependencies (pytest, coverage, etc.)
- Development tools (black, ruff, mypy, etc.)
- Documentation and metadata files
- Build tools (setuptools, wheel, pip, uv)

## Deployment Steps

### 1. Upload Layers

```bash
# Common layer
aws lambda publish-layer-version \
    --layer-name psn-emulator-common \
    --zip-file fileb://build/zip/common.zip \
    --compatible-runtimes python3.13

# Service-specific layers
aws lambda publish-layer-version \
    --layer-name psn-emulator-idp-api-deps \
    --zip-file fileb://build/zip/idp_api-deps.zip \
    --compatible-runtimes python3.13

aws lambda publish-layer-version \
    --layer-name psn-emulator-player-account-api-deps \
    --zip-file fileb://build/zip/player_account_api-deps.zip \
    --compatible-runtimes python3.13
```

### 2. Create/Update Lambda Functions

```bash
# IDP API Lambda
aws lambda create-function \
    --function-name psn-emulator-idp-api \
    --runtime python3.13 \
    --handler src.handler.lambda_handler \
    --zip-file fileb://build/zip/idp_api.zip \
    --layers arn:aws:lambda:region:account:layer:psn-emulator-common:version \
    --layers arn:aws:lambda:region:account:layer:psn-emulator-idp-api-deps:version \
    --role arn:aws:iam::account:role/lambda-execution-role

# Player Account API Lambda
aws lambda create-function \
    --function-name psn-emulator-player-account-api \
    --runtime python3.13 \
    --handler src.handler.lambda_handler \
    --zip-file fileb://build/zip/player_account_api.zip \
    --layers arn:aws:lambda:region:account:layer:psn-emulator-common:version \
    --layers arn:aws:lambda:region:account:layer:psn-emulator-player-account-api-deps:version \
    --role arn:aws:iam::account:role/lambda-execution-role
```

### 3. Update Function Code

When updating only source code:

```bash
aws lambda update-function-code \
    --function-name psn-emulator-idp-api \
    --zip-file fileb://build/zip/idp_api.zip

aws lambda update-function-code \
    --function-name psn-emulator-player-account-api \
    --zip-file fileb://build/zip/player_account_api.zip
```

## Deployment Info

The `deployment_info.json` file contains:

```json
{
  "services": {
    "idp_api": {
      "package": "build/zip/idp_api.zip",
      "layer": "build/zip/idp_api-deps.zip",
      "dependencies": ["pydantic[email]", "aws-lambda-powertools"]
    },
    "player_account_api": {
      "package": "build/zip/player_account_api.zip",
      "layer": "build/zip/player_account_api-deps.zip",
      "dependencies": ["pydantic[email]", "aws-lambda-powertools"]
    }
  },
  "layers": {
    "common": "build/zip/common.zip"
  },
  "deployment_order": ["idp_api", "player_account_api"]
}
```

## Best Practices

### 1. Layer Management

- **Version Layers**: Use semantic versioning for layers
- **Test Layers**: Test layers in a staging environment first
- **Document Changes**: Keep a changelog for layer updates

### 2. Package Size Optimization

The script automatically:
- Excludes development dependencies
- Removes `.pyc` files and `__pycache__` directories
- Strips documentation and metadata
- Uses binary packages when available

### 3. CI/CD Integration

```yaml
# GitHub Actions example
- name: Build Lambda packages
  run: |
    python scripts/build_zip.py --clean

- name: Upload layers
  run: |
    # Upload layers using deployment_info.json

- name: Deploy functions
  run: |
    # Update Lambda functions
```

### 4. Local Testing

```bash
# Build packages
python scripts/build_zip.py

# Test locally with SAM CLI
sam local start-api --template infra/terraform/sam_template.yaml

# Or test with LocalStack
localstack start
```

## Troubleshooting

### Import Errors

If you get import errors:

1. **Check Layer Order**: Ensure common layer is listed first
2. **Verify Dependencies**: Check `deployment_info.json` for required packages
3. **Layer Compatibility**: Ensure layers are compatible with Python 3.13

### Size Issues

If packages are too large:

1. **Check Dependencies**: Review what's included in each layer
2. **Exclude Unnecessary Packages**: Add to `EXCLUDE_DEPENDENCIES` in script
3. **Use Binary Packages**: Ensure `--only-binary=:all:` is working

### Performance

For optimal performance:

1. **Keep Layers Small**: Split large dependencies into separate layers
2. **Warm Functions**: Use provisioned concurrency for critical functions
3. **Monitor Cold Starts**: Track Lambda cold start metrics

## Comparison: Docker vs ZIP

| Aspect | Docker | ZIP + Layers |
|--------|--------|--------------|
| **Package Size** | Larger (includes OS) | Smaller (code only) |
| **Cold Start** | Slower | Faster |
| **Dependencies** | Full control | Layer constraints |
| **Local Testing** | Full environment | Requires SAM/LocalStack |
| **CI/CD** | Docker build steps | Simpler packaging |
| **Portability** | High | Medium |

Choose ZIP + Layers when:
- You need fastest cold starts
- You want minimal package sizes
- You have standardized dependencies
- You prefer simpler CI/CD

Choose Docker when:
- You need system-level dependencies
- You want maximum portability
- You have complex build requirements
- You prefer container-based workflows

## Migration from Docker

To migrate from Docker to ZIP + Layers:

1. **Build ZIP Packages**: `python scripts/build_zip.py`
2. **Create Layers**: Upload to AWS Lambda
3. **Update Functions**: Modify to use layers
4. **Update Terraform**: Change `package_type` from "Image" to "Zip"
5. **Test Thoroughly**: Verify all functionality works

## Integration with Existing Tools

### Terraform

```hcl
# Lambda function
resource "aws_lambda_function" "idp_api" {
  filename         = "build/zip/idp_api.zip"
  function_name    = "psn-emulator-idp-api"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "src.handler.lambda_handler"
  runtime         = "python3.13"
  layers          = [
    aws_lambda_layer_version.common.arn,
    aws_lambda_layer_version.idp_api_deps.arn
  ]

  depends_on = [
    aws_lambda_layer_version.common,
    aws_lambda_layer_version.idp_api_deps
  ]
}

# Common layer
resource "aws_lambda_layer_version" "common" {
  filename            = "build/zip/common.zip"
  layer_name         = "psn-emulator-common"
  compatible_runtimes = ["python3.13"]
}

# Service-specific layer
resource "aws_lambda_layer_version" "idp_api_deps" {
  filename            = "build/zip/idp_api-deps.zip"
  layer_name         = "psn-emulator-idp-api-deps"
  compatible_runtimes = ["python3.13"]
}
```

### AWS SAM

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  CommonLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: psn-emulator-common
      Description: Shared dependencies for PSN emulator
      ContentUri: build/zip/common.zip
      CompatibleRuntimes:
        - python3.13

  IdpApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: psn-emulator-idp-api
      Runtime: python3.13
      Handler: src.handler.lambda_handler
      CodeUri: build/zip/idp_api.zip
      Layers:
        - !Ref CommonLayer
      MemorySize: 512
      Timeout: 30
```