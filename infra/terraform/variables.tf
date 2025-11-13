variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be dev, test, or prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "psn-emulator"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "enable_api_gateway_logging" {
  description = "Enable API Gateway access logging"
  type        = bool
  default     = true
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing for Lambda functions"
  type        = bool
  default     = false
}

variable "idp_api_image_tag" {
  description = "Docker image tag for IDP API Lambda"
  type        = string
  default     = "latest"
}

variable "player_account_api_image_tag" {
  description = "Docker image tag for Player Account API Lambda"
  type        = string
  default     = "latest"
}

# ZIP deployment variables
variable "use_zip_deployment" {
  description = "Use ZIP-based Lambda deployment instead of container images"
  type        = bool
  default     = false
}

variable "shared_layer_zip_path" {
  description = "Path to shared layer ZIP file"
  type        = string
  default     = "../../build/zip/shared-layer.zip"
}

variable "idp_api_zip_path" {
  description = "Path to IDP API ZIP file"
  type        = string
  default     = "../../build/zip/idp_api.zip"
}

variable "player_account_api_zip_path" {
  description = "Path to Player Account API ZIP file"
  type        = string
  default     = "../../build/zip/player_account_api.zip"
}
