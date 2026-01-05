# Configuration du provider OpenStack
provider "openstack" {
  # Ces variables peuvent être définies via des variables d'environnement ou directement ici
  # OS_AUTH_URL, OS_USERNAME, OS_PASSWORD, OS_TENANT_NAME, etc.
}

# Réseau principal
resource "openstack_networking_network_v2" "ml_network" {
  name           = "${var.environment}-ml-network"
  admin_state_up = true
}

# Sous-réseau pour le réseau ML
resource "openstack_networking_subnet_v2" "ml_subnet" {
  name            = "${var.environment}-ml-subnet"
  network_id      = openstack_networking_network_v2.ml_network.id
  cidr            = var.network_cidr
  ip_version      = 4
  dns_nameservers = var.dns_servers
  
  allocation_pool {
    start = cidrhost(var.network_cidr, 10)
    end   = cidrhost(var.network_cidr, 200)
  }
}

# Routeur pour la connectivité externe
resource "openstack_networking_router_v2" "ml_router" {
  name                = "${var.environment}-ml-router"
  external_network_id = var.external_network_id
  admin_state_up      = true
}

# Connexion du routeur au sous-réseau
resource "openstack_networking_router_interface_v2" "ml_router_interface" {
  router_id = openstack_networking_router_v2.ml_router.id
  subnet_id = openstack_networking_subnet_v2.ml_subnet.id
}

# Groupe de sécurité par défaut
resource "openstack_networking_secgroup_v2" "default" {
  name        = "${var.environment}-default-sg"
  description = "Groupe de sécurité par défaut pour les ressources ML"
}

# Règles de sécurité pour le groupe par défaut
resource "openstack_networking_secgroup_rule_v2" "ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.default.id
}

resource "openstack_networking_secgroup_rule_v2" "internal" {
  direction         = "ingress"
  ethertype         = "IPv4"
  remote_group_id   = openstack_networking_secgroup_v2.default.id
  security_group_id = openstack_networking_secgroup_v2.default.id
}

# Variables nécessaires
variable "environment" {
  description = "Environnement (dev, staging, prod)"
  type        = string
}

variable "network_cidr" {
  description = "CIDR du réseau ML"
  type        = string
  default     = "10.0.0.0/24"
}

variable "external_network_id" {
  description = "ID du réseau externe pour la connectivité Internet"
  type        = string
}

variable "dns_servers" {
  description = "Liste des serveurs DNS"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

# Outputs utiles
output "network_id" {
  value = openstack_networking_network_v2.ml_network.id
}

output "subnet_id" {
  value = openstack_networking_subnet_v2.ml_subnet.id
}

output "security_group_id" {
  value = openstack_networking_secgroup_v2.default.id
}

output "router_id" {
  value = openstack_networking_router_v2.ml_router.id
}
