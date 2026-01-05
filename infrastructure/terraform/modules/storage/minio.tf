# Configuration du provider MinIO
provider "minio" {
  # Ces valeurs peuvent être configurées via des variables d'environnement ou des variables Terraform
  endpoint   = var.minio_endpoint
  access_key = var.minio_access_key
  secret_key = var.minio_secret_key
  ssl_verify = var.minio_ssl_verify
}

# Bucket MinIO principal pour ML
resource "minio_s3_bucket" "ml_bucket" {
  bucket = var.ml_bucket_name
  acl    = "private"

  tags = merge(var.common_tags, {
    Name        = var.ml_bucket_name
    Purpose     = "ML Pipeline Storage"
    Environment = var.environment
  })
}

# Configuration du versioning
resource "minio_s3_bucket_versioning" "ml_bucket" {
  count = var.enable_versioning ? 1 : 0
  
  bucket = minio_s3_bucket.ml_bucket.bucket
  versioning_configuration {
    status = "Enabled"
  }
}

# Configuration de la politique de bucket
resource "minio_iam_policy" "ml_bucket_policy" {
  name   = "${var.environment}-ml-bucket-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.ml_bucket_name}",
          "arn:aws:s3:::${var.ml_bucket_name}/*"
        ]
      }
    ]
  })
}

# Utilisateur MinIO pour l'application
resource "minio_iam_user" "ml_user" {
  name          = "${var.environment}-ml-user"
  force_destroy = true
}

# Attachement de la politique à l'utilisateur
resource "minio_iam_user_policy_attachment" "ml_user_policy" {
  user_name   = minio_iam_user.ml_user.name
  policy_name = minio_iam_policy.ml_bucket_policy.name
}

# Création d'un compte de service pour l'application
resource "minio_iam_service_account" "ml_service_account" {
  target_user = minio_iam_user.ml_user.name
}

# Configuration des notifications (optionnel)
resource "minio_s3_bucket_notification" "ml_bucket_notification" {
  count  = var.enable_s3_notifications ? 1 : 0
  bucket = minio_s3_bucket.ml_bucket.bucket

  queue {
    id            = "ml-pipeline-notification"
    queue         = var.notification_queue_arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".parquet"
  }
}

# Variables nécessaires pour le module
variable "minio_endpoint" {
  description = "MinIO server endpoint"
  type        = string
  default     = "http://minio:9000"
}

variable "minio_access_key" {
  description = "MinIO access key"
  type        = string
  sensitive   = true
}

variable "minio_secret_key" {
  description = "MinIO secret key"
  type        = string
  sensitive   = true
}

variable "minio_ssl_verify" {
  description = "Disable SSL certificate verification"
  type        = bool
  default     = false
}

variable "ml_bucket_name" {
  description = "Name of the ML bucket"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

variable "enable_versioning" {
  description = "Enable versioning for the bucket"
  type        = bool
  default     = true
}

variable "enable_s3_notifications" {
  description = "Enable S3 bucket notifications"
  type        = bool
  default     = false
}

variable "notification_queue_arn" {
  description = "ARN of the notification queue"
  type        = string
  default     = ""
}

# Outputs utiles
output "bucket_name" {
  value = minio_s3_bucket.ml_bucket.bucket
}

output "service_account_access_key" {
  value     = minio_iam_service_account.ml_service_account.access_key
  sensitive = true
}

output "service_account_secret_key" {
  value     = minio_iam_service_account.ml_service_account.secret_key
  sensitive = true
}
