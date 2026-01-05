output "grafana_url" {
  description = "URL d'accès à Grafana"
  value       = "http://${kubernetes_service.grafana.status.0.load_balancer.0.ingress.0.hostname}:3000"
}

output "prometheus_url" {
  description = "URL d'accès à Prometheus"
  value       = "http://${kubernetes_service.prometheus.status.0.load_balancer.0.ingress.0.hostname}:9090"
}

output "alertmanager_url" {
  description = "URL d'accès à Alertmanager"
  value       = "http://${kubernetes_service.alertmanager.status.0.load_balancer.0.ingress.0.hostname}:9093"
}

output "grafana_admin_username" {
  description = "Nom d'utilisateur administrateur pour Grafana"
  value       = "admin"
}

output "grafana_admin_password" {
  description = "Mot de passe administrateur pour Grafana"
  value       = var.grafana_admin_password
  sensitive   = true
}
