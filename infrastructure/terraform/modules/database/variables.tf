variable "environment" {
  description = "Environnement de déploiement (dev, staging, prod)"
  type        = string
}

variable "postgresql_image_name" {
  description = "Nom de l'image OpenStack pour PostgreSQL"
  type        = string
  default     = "Ubuntu 20.04"
}

variable "postgresql_flavor" {
  description = "Type d'instance OpenStack pour PostgreSQL"
  type        = string
  default     = "m1.small"
}

variable "postgresql_version" {
  description = "Version de PostgreSQL à installer"
  type        = string
  default     = "12"
}

variable "database_name" {
  description = "Nom de la base de données à créer"
  type        = string
  default     = "ml_pipeline"
}

variable "database_user" {
  description = "Utilisateur de la base de données"
  type        = string
  default     = "ml_user"
}

variable "database_password" {
  description = "Mot de passe de l'utilisateur de la base de données"
  type        = string
  sensitive   = true
}

variable "volume_size" {
  description = "Taille du volume pour la base de données (en Go)"
  type        = number
  default     = 20
}

variable "network_name" {
  description = "Nom du réseau OpenStack"
  type        = string
}

variable "key_pair_name" {
  description = "Nom de la clé SSH pour l'accès aux instances"
  type        = string
}

variable "allowed_cidr" {
  description = "CIDR autorisé à accéder à la base de données"
  type        = string
  default     = "10.0.0.0/8"
}

variable "admin_cidr" {
  description = "CIDR autorisé pour l'accès SSH d'administration"
  type        = string
  default     = "0.0.0.0/0"
}

variable "common_tags" {
  description = "Tags communs à toutes les ressources"
  type        = map(string)
  default     = {}
}
