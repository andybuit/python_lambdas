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

# IDP API Lambda Function (Container Image)
resource "aws_lambda_function" "idp_api" {
  function_name = "${var.project_name}-${var.environment}-idp-api"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.idp_api.repository_url}:${var.idp_api_image_tag}"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

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
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.idp_api
  ]

  lifecycle {
    ignore_changes = [
      image_uri, # Allow image updates without Terraform plan changes
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-idp-api"
    Environment = var.environment
    Service     = "idp-api"
  }
}

# Player Account API Lambda Function (Container Image)
resource "aws_lambda_function" "player_account_api" {
  function_name = "${var.project_name}-${var.environment}-player-account-api"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.player_account_api.repository_url}:${var.player_account_api_image_tag}"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

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
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.player_account_api
  ]

  lifecycle {
    ignore_changes = [
      image_uri, # Allow image updates without Terraform plan changes
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-player-account-api"
    Environment = var.environment
    Service     = "player-account-api"
  }
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
