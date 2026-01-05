# Configuration du réseau principal
resource "openstack_networking_network_v2" "ml_network" {
  name           = "${var.environment}-ml-network"
  admin_state_up = true
  
  tags = merge(var.common_tags, {
    Name        = "${var.environment}-ml-network"
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

# Configuration du sous-réseau
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
  
  tags = merge(var.common_tags, {
    Name        = "${var.environment}-ml-subnet"
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

# Configuration du routeur
resource "openstack_networking_router_v2" "ml_router" {
  name                = "${var.environment}-ml-router"
  external_network_id = var.external_network_id
  admin_state_up      = true
  
  tags = merge(var.common_tags, {
    Name        = "${var.environment}-ml-router"
    Environment = var.environment
    ManagedBy   = "terraform"
  })
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
  
  tags = merge(var.common_tags, {
    Name        = "${var.environment}-default-sg"
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

# Règles de sécurité par défaut
resource "openstack_networking_secgroup_rule_v2" "ssh_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.admin_cidr
  security_group_id = openstack_networking_secgroup_v2.default.id
}

resource "openstack_networking_secgroup_rule_v2" "internal_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  remote_group_id   = openstack_networking_secgroup_v2.default.id
  security_group_id = openstack_networking_secgroup_v2.default.id
}

resource "openstack_networking_secgroup_rule_v2" "egress" {
  direction         = "egress"
  ethertype         = "IPv4"
  security_group_id = openstack_networking_secgroup_v2.default.id
}

# Règle pour Kubernetes API
resource "openstack_networking_secgroup_rule_v2" "k8s_api" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 6443
  port_range_max    = 6443
  remote_ip_prefix  = var.network_cidr
  security_group_id = openstack_networking_secgroup_v2.default.id
}

# Règle pour les services NodePort
resource "openstack_networking_secgroup_rule_v2" "node_port" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 30000
  port_range_max    = 32767
  remote_ip_prefix  = var.network_cidr
  security_group_id = openstack_networking_secgroup_v2.default.id
}
