# ZIP-based Lambda Functions (Alternative to Container Image deployment)
# This file shows how to use the shared layer with ZIP-based Lambda deployment

# Shared Lambda Layer for common libraries and root dependencies
resource "aws_lambda_layer_version" "shared" {
  filename            = var.shared_layer_zip_path
  layer_name          = "${var.project_name}-${var.environment}-shared"
  compatible_runtimes = ["python3.13"]
  description         = "Shared layer containing common libraries and root dependencies"

  source_code_hash = data.archive_file.shared_layer.output_base64sha256

  depends_on = [
    aws_cloudwatch_log_group.idp_api_zip,
    aws_cloudwatch_log_group.player_account_api_zip,
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-shared"
    Environment = var.environment
    Type        = "shared-layer"
  }
}

# IDP API Lambda Function (ZIP package with shared layer)
resource "aws_lambda_function" "idp_api_zip" {
  count         = var.use_zip_deployment ? 1 : 0
  function_name = "${var.project_name}-${var.environment}-idp-api-zip"
  role          = data.aws_iam_role.lambda_execution.arn
  package_type  = "Zip"
  filename      = var.idp_api_zip_path
  handler       = "handler.lambda_handler"
  runtime       = "python3.13"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Reference the shared layer
  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      LOG_LEVEL               = var.environment == "prod" ? "INFO" : "DEBUG"
      POWERTOOLS_SERVICE_NAME = "idp-api"
    }
  }

  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  depends_on = [
    aws_cloudwatch_log_group.idp_api_zip,
    aws_lambda_layer_version.shared,
  ]

  lifecycle {
    ignore_changes = [
      layers, # Allow layer updates without Terraform plan changes
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-idp-api-zip"
    Environment = var.environment
    Service     = "idp-api"
    Deployment  = "zip"
  }
}

# Player Account API Lambda Function (ZIP package with shared layer)
resource "aws_lambda_function" "player_account_api_zip" {
  count         = var.use_zip_deployment ? 1 : 0
  function_name = "${var.project_name}-${var.environment}-player-account-api-zip"
  role          = data.aws_iam_role.lambda_execution.arn
  package_type  = "Zip"
  filename      = var.player_account_api_zip_path
  handler       = "handler.lambda_handler"
  runtime       = "python3.13"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Reference the shared layer
  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      LOG_LEVEL               = var.environment == "prod" ? "INFO" : "DEBUG"
      POWERTOOLS_SERVICE_NAME = "player-account-api"
    }
  }

  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  depends_on = [
    aws_cloudwatch_log_group.player_account_api_zip,
    aws_lambda_layer_version.shared,
  ]

  lifecycle {
    ignore_changes = [
      layers, # Allow layer updates without Terraform plan changes
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-player-account-api-zip"
    Environment = var.environment
    Service     = "player-account-api"
    Deployment  = "zip"
  }
}

# CloudWatch Log Groups for ZIP-based Lambda Functions
resource "aws_cloudwatch_log_group" "idp_api_zip" {
  count             = var.use_zip_deployment ? 1 : 0
  name              = "/aws/lambda/${var.project_name}-${var.environment}-idp-api-zip"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-idp-api-zip"
    Environment = var.environment
    Service     = "idp-api"
  }
}

resource "aws_cloudwatch_log_group" "player_account_api_zip" {
  count             = var.use_zip_deployment ? 1 : 0
  name              = "/aws/lambda/${var.project_name}-${var.environment}-player-account-api-zip"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-player-account-api-zip"
    Environment = var.environment
    Service     = "player-account-api"
  }
}

# Lambda Permissions for API Gateway (ZIP-based)
resource "aws_lambda_permission" "idp_api_zip_apigw" {
  count         = var.use_zip_deployment ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.idp_api_zip[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "player_account_api_zip_apigw" {
  count         = var.use_zip_deployment ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.player_account_api_zip[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Data source for shared layer ZIP file (for hash calculation)
data "archive_file" "shared_layer" {
  type        = "zip"
  source_file = var.shared_layer_zip_path
  output_path = "${path.module}/temp_shared_layer_hash.zip"
}