output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = aws_apigatewayv2_stage.main.invoke_url
}

output "idp_api_lambda_arn" {
  description = "IDP API Lambda function ARN"
  value       = aws_lambda_function.idp_api.arn
}

output "player_account_api_lambda_arn" {
  description = "Player Account API Lambda function ARN"
  value       = aws_lambda_function.player_account_api.arn
}

output "idp_api_lambda_name" {
  description = "IDP API Lambda function name"
  value       = aws_lambda_function.idp_api.function_name
}

output "player_account_api_lambda_name" {
  description = "Player Account API Lambda function name"
  value       = aws_lambda_function.player_account_api.function_name
}

output "cloudwatch_log_group_idp_api" {
  description = "CloudWatch log group for IDP API"
  value       = aws_cloudwatch_log_group.idp_api.name
}

output "cloudwatch_log_group_player_account_api" {
  description = "CloudWatch log group for Player Account API"
  value       = aws_cloudwatch_log_group.player_account_api.name
}
