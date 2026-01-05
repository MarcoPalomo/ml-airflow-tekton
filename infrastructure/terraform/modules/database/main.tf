# Configuration de l'instance PostgreSQL sur OpenStack
resource "openstack_compute_instance_v2" "postgresql" {
  name            = "${var.environment}-postgresql"
  image_name      = var.postgresql_image_name
  flavor_name     = var.postgresql_flavor
  key_pair        = var.key_pair_name
  security_groups = [openstack_networking_secgroup_v2.database.name]
  
  network {
    name = var.network_name
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.postgresql.id
    source_type           = "image"
    destination_type      = "volume"
    volume_size           = var.volume_size
    delete_on_termination = false
  }

  metadata = merge(var.common_tags, {
    environment = var.environment
    role        = "database"
  })

  user_data = <<-EOF
              #cloud-config
              packages:
                - postgresql-${var.postgresql_version}
                - postgresql-contrib
              runcmd:
                - systemctl enable postgresql
                - systemctl start postgresql
                - sudo -u postgres psql -c "CREATE DATABASE ${var.database_name};"
                - sudo -u postgres psql -c "CREATE USER ${var.database_user} WITH PASSWORD '${var.database_password}';"
                - sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${var.database_name} TO ${var.database_user};"
                - echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/${var.postgresql_version}/main/pg_hba.conf
                - echo "listen_addresses = '*'" >> /etc/postgresql/${var.postgresql_version}/main/postgresql.conf
                - systemctl restart postgresql
              EOF
}

# Groupe de sécurité pour PostgreSQL
resource "openstack_networking_secgroup_v2" "database" {
  name        = "${var.environment}-postgresql-sg"
  description = "Security group for PostgreSQL database"
}

# Règles de sécurité
resource "openstack_networking_secgroup_rule_v2" "postgresql_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 5432
  port_range_max    = 5432
  remote_ip_prefix  = var.allowed_cidr
  security_group_id = openstack_networking_secgroup_v2.database.id
}

# Règle SSH pour l'administration
resource "openstack_networking_secgroup_rule_v2" "ssh_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.admin_cidr
  security_group_id = openstack_networking_secgroup_v2.database.id
}

# Règle de sortie
resource "openstack_networking_secgroup_rule_v2" "egress" {
  direction         = "egress"
  ethertype         = "IPv4"
  security_group_id = openstack_networking_secgroup_v2.database.id
}

# Données pour l'image
# ... (le reste du code reste inchangé)
