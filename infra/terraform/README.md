# Terraform Infrastructure

This directory contains Terraform configuration for deploying the PSN Partner Emulator service to AWS.

## Architecture

The infrastructure includes:
- **API Gateway HTTP API**: Single API Gateway with routes for all Lambda functions
- **Lambda Functions**: Separate functions for IDP API and Player Account API
- **CloudWatch Logs**: Log groups for Lambda functions and API Gateway
- **IAM Roles**: Execution roles for Lambda functions with minimal permissions

## Prerequisites

1. **Python and uv**: Install dependencies and create virtual environment
   ```bash
   # From project root
   uv sync

   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

2. **Terraform**: Install Terraform >= 1.5.0
   ```bash
   brew install terraform  # macOS
   ```

3. **AWS CLI**: Configure AWS credentials
   ```bash
   aws configure
   ```

4. **S3 Backend** (Optional): Create an S3 bucket for Terraform state
   ```bash
   aws s3 mb s3://your-terraform-state-bucket
   ```

## File Structure

```
terraform/
├── main.tf           # Provider configuration and backend
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── lambda.tf         # Lambda function resources
├── api_gateway.tf    # API Gateway configuration
└── README.md         # This file
```

## Configuration

### 1. Configure Backend (Optional but Recommended)

Edit `main.tf` to configure S3 backend:

```hcl
backend "s3" {
  bucket = "your-terraform-state-bucket"
  key    = "psn-emulator/terraform.tfstate"
  region = "us-east-1"
}
```

### 2. Set Variables

Create a `terraform.tfvars` file:

```hcl
aws_region              = "us-east-1"
environment             = "dev"
project_name            = "psn-emulator"
lambda_timeout          = 30
lambda_memory_size      = 512
log_retention_days      = 7
enable_api_gateway_logging = true
enable_xray_tracing     = false
```

Or pass variables via command line:
```bash
terraform apply -var="environment=prod" -var="aws_region=us-west-2"
```

## Deployment

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Changes

```bash
terraform plan
```

### Apply Infrastructure

```bash
terraform apply
```

Review the plan and type `yes` to confirm.

### Destroy Infrastructure

```bash
terraform destroy
```

## Outputs

After deployment, Terraform will output:

- `api_gateway_url`: The base URL for your API Gateway
- `idp_api_lambda_arn`: ARN of the IDP API Lambda function
- `player_account_api_lambda_arn`: ARN of the Player Account API Lambda function
- `cloudwatch_log_group_*`: CloudWatch log group names

View outputs:
```bash
terraform output
terraform output api_gateway_url
```

## Building Lambda Packages

Before deploying, ensure Lambda packages are built:

```bash
# From project root
cd terraform
terraform init
terraform plan  # This will create the zip files in build/
```

For production deployments, consider using a proper build pipeline that:
1. Installs dependencies in a Lambda-compatible environment
2. Creates deployment packages with dependencies
3. Uses Lambda layers for shared dependencies

## Multi-Environment Setup

### Using Workspaces

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new test
terraform workspace new prod

# Switch between environments
terraform workspace select dev
terraform apply -var="environment=dev"

terraform workspace select prod
terraform apply -var="environment=prod"
```

### Using Separate State Files

```bash
# Dev environment
terraform apply -var-file="dev.tfvars" -state="dev.tfstate"

# Prod environment
terraform apply -var-file="prod.tfvars" -state="prod.tfstate"
```

## Updating Lambda Functions

When you make changes to Lambda code:

1. Terraform will detect changes via `source_code_hash`
2. Run `terraform apply` to update the functions
3. API Gateway is automatically updated

## Monitoring and Logs

### View Lambda Logs

```bash
# IDP API logs
aws logs tail /aws/lambda/psn-emulator-dev-idp-api --follow

# Player Account API logs
aws logs tail /aws/lambda/psn-emulator-dev-player-account-api --follow
```

### View API Gateway Logs

```bash
aws logs tail /aws/apigateway/psn-emulator-dev --follow
```

## Cost Optimization

- Lambda: Pay per invocation and duration
- API Gateway: Pay per request
- CloudWatch Logs: Pay for storage (adjust retention_days)

Estimated costs for dev environment with low traffic: ~$5-10/month

## Security Considerations

1. **IAM Roles**: Lambda functions have minimal permissions
2. **API Gateway**: CORS is configured (adjust for production)
3. **Secrets**: Use AWS Secrets Manager for sensitive data (not implemented yet)
4. **VPC**: Lambdas are not in VPC by default (add if needed for database access)

## Troubleshooting

### Lambda Package Too Large

If Lambda package exceeds 50MB:
- Use Lambda Layers for dependencies
- Exclude unnecessary files
- Use S3 for deployment packages

### Permission Errors

Ensure your AWS credentials have permissions to:
- Create Lambda functions
- Create API Gateway resources
- Create IAM roles
- Create CloudWatch log groups

### State Lock Errors

If using S3 backend with DynamoDB locking:
```bash
terraform force-unlock <lock-id>
```

## Advanced Configuration

### Add DynamoDB Tables

Create `dynamodb.tf`:
```hcl
resource "aws_dynamodb_table" "players" {
  name           = "${var.project_name}-${var.environment}-players"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "player_id"

  attribute {
    name = "player_id"
    type = "S"
  }
}
```

### Add Lambda Layers

```hcl
resource "aws_lambda_layer_version" "dependencies" {
  filename   = "lambda_layer.zip"
  layer_name = "psn-emulator-dependencies"
  compatible_runtimes = ["python3.12"]
}
```

### Enable X-Ray Tracing

Set `enable_xray_tracing = true` in your variables.

## CI/CD Integration

See `.github/workflows/terraform.yml` for automated deployment pipeline.

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)
