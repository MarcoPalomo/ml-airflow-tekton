output "database_host" {
  description = "Adresse IP de l'instance PostgreSQL"
  value       = openstack_compute_instance_v2.postgresql.access_ip_v4
}

output "database_port" {
  description = "Port d'écoute de PostgreSQL"
  value       = 5432
}

output "database_name" {
  description = "Nom de la base de données"
  value       = var.database_name
}

output "database_user" {
  description = "Nom d'utilisateur de la base de données"
  value       = var.database_user
}

output "database_password" {
  description = "Mot de passe de la base de données"
  value       = var.database_password
  sensitive   = true
}

output "security_group_id" {
  description = "ID du groupe de sécurité de la base de données"
  value       = openstack_networking_secgroup_v2.database.id
}
