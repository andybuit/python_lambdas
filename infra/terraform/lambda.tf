# IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Optional: X-Ray tracing policy
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count      = var.enable_xray_tracing ? 1 : 0
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Package Lambda functions
data "archive_file" "idp_api_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../services/idp_api/src"
  output_path = "${path.module}/../build/idp_api_lambda.zip"
  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "tests",
  ]
}

data "archive_file" "player_account_api_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../services/player_account_api/src"
  output_path = "${path.module}/../build/player_account_api_lambda.zip"
  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "tests",
  ]
}

# IDP API Lambda Function
resource "aws_lambda_function" "idp_api" {
  filename         = data.archive_file.idp_api_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-idp-api"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.idp_api_lambda.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      LOG_LEVEL      = var.environment == "prod" ? "INFO" : "DEBUG"
      POWERTOOLS_SERVICE_NAME = "idp-api"
    }
  }

  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.idp_api
  ]
}

# Player Account API Lambda Function
resource "aws_lambda_function" "player_account_api" {
  filename         = data.archive_file.player_account_api_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-player-account-api"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.player_account_api_lambda.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      LOG_LEVEL      = var.environment == "prod" ? "INFO" : "DEBUG"
      POWERTOOLS_SERVICE_NAME = "player-account-api"
    }
  }

  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.player_account_api
  ]
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "idp_api" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-idp-api"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "player_account_api" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-player-account-api"
  retention_in_days = var.log_retention_days
}

# Lambda Permissions for API Gateway
resource "aws_lambda_permission" "idp_api_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.idp_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "player_account_api_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.player_account_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
