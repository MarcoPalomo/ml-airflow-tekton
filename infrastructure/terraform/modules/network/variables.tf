variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
}

variable "network_cidr" {
  description = "CIDR block for the ML network"
  type        = string
  default     = "10.0.0.0/24"
}

variable "external_network_id" {
  description = "ID of the external network for internet access"
  type        = string
}

variable "dns_servers" {
  description = "List of DNS servers"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "admin_cidr" {
  description = "CIDR block for administrative access (SSH, etc.)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

variable "enable_k8s_support" {
  description = "Enable Kubernetes-specific network rules"
  type        = bool
  default     = true
}

variable "allowed_ingress_ports" {
  description = "List of additional ports to allow ingress traffic"
  type = list(object({
    port        = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  default = []
}
