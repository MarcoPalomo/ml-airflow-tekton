variable "environment" {
  description = "Environnement de déploiement (dev, staging, prod)"
  type        = string
}

variable "minio_endpoint" {
  description = "URL du point de terminaison MinIO"
  type        = string
  default     = "http://minio:9000"
}

variable "minio_access_key" {
  description = "Clé d'accès pour l'API MinIO"
  type        = string
  sensitive   = true
}

variable "minio_secret_key" {
  description = "Clé secrète pour l'API MinIO"
  type        = string
  sensitive   = true
}

variable "minio_ssl_verify" {
  description = "Vérifier les certificats SSL"
  type        = bool
  default     = false
}

variable "ml_bucket_name" {
  description = "Nom du bucket pour le stockage ML"
  type        = string
  default     = "ml-pipeline-bucket"
}

variable "enable_versioning" {
  description = "Activer le versioning des objets"
  type        = bool
  default     = true
}

variable "common_tags" {
  description = "Tags communs à toutes les ressources"
  type        = map(string)
  default     = {}
}

variable "create_service_account" {
  description = "Créer un compte de service pour l'application"
  type        = bool
  default     = true
}

variable "service_account_name" {
  description = "Nom du compte de service"
  type        = string
  default     = "ml-service-account"
}
