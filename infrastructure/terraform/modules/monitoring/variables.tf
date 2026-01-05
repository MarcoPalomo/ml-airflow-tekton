variable "environment" {
  description = "Environnement de déploiement (dev, staging, prod)"
  type        = string
}

variable "namespace" {
  description = "Namespace Kubernetes pour le déploiement"
  type        = string
  default     = "monitoring"
}

variable "prometheus_storage_size" {
  description = "Taille du stockage pour Prometheus (ex: '10Gi')"
  type        = string
  default     = "20Gi"
}

variable "grafana_storage_size" {
  description = "Taille du stockage pour Grafana (ex: '5Gi')"
  type        = string
  default     = "10Gi"
}

variable "storage_class_name" {
  description = "Classe de stockage à utiliser pour les volumes persistants"
  type        = string
  default     = "standard"
}

variable "grafana_admin_password" {
  description = "Mot de passe administrateur pour Grafana"
  type        = string
  sensitive   = true
}

variable "node_selector" {
  description = "Sélecteurs de nœuds pour le déploiement des pods"
  type        = map(string)
  default     = {}
}

variable "tolerations" {
  description = "Tolérations pour le déploiement des pods"
  type = list(object({
    key      = string
    operator = string
    value    = string
    effect   = string
  }))
  default = []
}

variable "common_tags" {
  description = "Tags communs à toutes les ressources"
  type        = map(string)
  default     = {}
}
