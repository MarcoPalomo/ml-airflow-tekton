output "bucket_name" {
  description = "Nom du bucket MinIO créé"
  value       = minio_s3_bucket.ml_bucket.bucket
}

output "bucket_arn" {
  description = "ARN du bucket MinIO"
  value       = "arn:aws:s3:::${minio_s3_bucket.ml_bucket.bucket}"
}

output "service_account_access_key" {
  description = "Clé d'accès du compte de service"
  value       = var.create_service_account ? minio_iam_service_account.ml_service_account[0].access_key : ""
  sensitive   = true
}

output "service_account_secret_key" {
  description = "Clé secrète du compte de service"
  value       = var.create_service_account ? minio_iam_service_account.ml_service_account[0].secret_key : ""
  sensitive   = true
}

output "endpoint" {
  description = "Point de terminaison MinIO"
  value       = var.minio_endpoint
}

output "bucket_policy" {
  description = "Politique d'accès du bucket"
  value       = minio_iam_policy.ml_bucket_policy.policy
  sensitive   = true
}
