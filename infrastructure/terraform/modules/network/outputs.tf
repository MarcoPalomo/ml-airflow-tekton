output "network_id" {
  description = "ID du réseau ML créé"
  value       = openstack_networking_network_v2.ml_network.id
}

output "subnet_id" {
  description = "ID du sous-réseau ML créé"
  value       = openstack_networking_subnet_v2.ml_subnet.id
}

output "security_group_id" {
  description = "ID du groupe de sécurité par défaut"
  value       = openstack_networking_secgroup_v2.default.id
}

output "security_group_name" {
  description = "Nom du groupe de sécurité par défaut"
  value       = openstack_networking_secgroup_v2.default.name
}

output "router_id" {
  description = "ID du routeur créé"
  value       = openstack_networking_router_v2.ml_router.id
}

output "router_name" {
  description = "Nom du routeur créé"
  value       = openstack_networking_router_v2.ml_router.name
}

output "network_name" {
  description = "Nom du réseau ML créé"
  value       = openstack_networking_network_v2.ml_network.name
}

output "subnet_cidr" {
  description = "CIDR du sous-réseau ML"
  value       = openstack_networking_subnet_v2.ml_subnet.cidr
}

output "allocation_pools" {
  description = "Plages d'adresses IP allouées dans le sous-réseau"
  value       = openstack_networking_subnet_v2.ml_subnet.allocation_pools
}

output "dns_nameservers" {
  description = "Serveurs DNS configurés pour le réseau"
  value       = var.dns_servers
}

output "external_network_id" {
  description = "ID du réseau externe utilisé pour la connectivité Internet"
  value       = var.external_network_id
}
