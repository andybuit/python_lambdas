# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "PSN Partner Emulator API Gateway"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 300
  }
}

# IDP API Integration
resource "aws_apigatewayv2_integration" "idp_api" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.idp_api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# Player Account API Integration
resource "aws_apigatewayv2_integration" "player_account_api" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.player_account_api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# IDP API Routes
resource "aws_apigatewayv2_route" "idp_auth_token" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /auth/token"
  target    = "integrations/${aws_apigatewayv2_integration.idp_api.id}"
}

resource "aws_apigatewayv2_route" "idp_auth_userinfo" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /auth/userinfo"
  target    = "integrations/${aws_apigatewayv2_integration.idp_api.id}"
}

resource "aws_apigatewayv2_route" "idp_auth_refresh" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /auth/refresh"
  target    = "integrations/${aws_apigatewayv2_integration.idp_api.id}"
}

# Player Account API Routes
resource "aws_apigatewayv2_route" "player_create" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /players"
  target    = "integrations/${aws_apigatewayv2_integration.player_account_api.id}"
}

resource "aws_apigatewayv2_route" "player_list" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /players"
  target    = "integrations/${aws_apigatewayv2_integration.player_account_api.id}"
}

resource "aws_apigatewayv2_route" "player_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /players/{player_id}"
  target    = "integrations/${aws_apigatewayv2_integration.player_account_api.id}"
}

resource "aws_apigatewayv2_route" "player_update" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /players/{player_id}"
  target    = "integrations/${aws_apigatewayv2_integration.player_account_api.id}"
}

resource "aws_apigatewayv2_route" "player_delete" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /players/{player_id}"
  target    = "integrations/${aws_apigatewayv2_integration.player_account_api.id}"
}

resource "aws_apigatewayv2_route" "player_stats" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /players/{player_id}/stats"
  target    = "integrations/${aws_apigatewayv2_integration.player_account_api.id}"
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }

  dynamic "access_log_settings" {
    for_each = var.enable_api_gateway_logging ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
      format = jsonencode({
        requestId      = "$context.requestId"
        ip             = "$context.identity.sourceIp"
        requestTime    = "$context.requestTime"
        httpMethod     = "$context.httpMethod"
        routeKey       = "$context.routeKey"
        status         = "$context.status"
        protocol       = "$context.protocol"
        responseLength = "$context.responseLength"
      })
    }
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  count             = var.enable_api_gateway_logging ? 1 : 0
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days
}
