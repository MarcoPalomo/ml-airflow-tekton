# Création du namespace pour le monitoring
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.namespace
    labels = {
      name = var.namespace
    }
  }
}

# Installation de Prometheus Stack via Helm
resource "helm_release" "prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "65.5.1"
  
  values = [
    <<-EOT
    alertmanager:
      alertmanagerSpec:
        storage:
          volumeClaimTemplate:
            spec:
              storageClassName: ${var.storage_class_name}
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: ${var.prometheus_storage_size}
    
    prometheus:
      prometheusSpec:
        storageSpec:
          volumeClaimTemplate:
            spec:
              storageClassName: ${var.storage_class_name}
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: ${var.prometheus_storage_size}
    
    grafana:
      adminPassword: ${var.grafana_admin_password}
      persistence:
        enabled: true
        storageClassName: ${var.storage_class_name}
        size: ${var.grafana_storage_size}
      service:
        type: LoadBalancer
    
    prometheusOperator:
      nodeSelector:
        ${yamlencode(var.node_selector)}
      tolerations: ${jsonencode(var.tolerations)}
    
    prometheus-node-exporter:
      nodeSelector:
        ${yamlencode(var.node_selector)}
      tolerations: ${jsonencode(var.tolerations)}
    
    kube-state-metrics:
      nodeSelector:
        ${yamlencode(var.node_selector)}
      tolerations: ${jsonencode(var.tolerations)}
    EOT
  ]
  
  depends_on = [kubernetes_namespace.monitoring]
}

# Service pour exposer Grafana
resource "kubernetes_service" "grafana" {
  metadata {
    name      = "grafana"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    
    annotations = {
      "metallb.universe.tf/address-pool" = "default"
    }
  }
  
  spec {
    selector = {
      "app.kubernetes.io/instance" = "kube-prometheus-stack"
      "app.kubernetes.io/name"     = "grafana"
    }
    
    port {
      name        = "http"
      port        = 80
      target_port = 3000
    }
    
    type = "LoadBalancer"
  }
  
  depends_on = [helm_release.prometheus_stack]
}

# Service pour exposer Prometheus
resource "kubernetes_service" "prometheus" {
  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    
    annotations = {
      "metallb.universe.tf/address-pool" = "default"
    }
  }
  
  spec {
    selector = {
      "app.kubernetes.io/instance" = "kube-prometheus-stack"
      "app.kubernetes.io/name"     = "prometheus"
      "prometheus"                 = "kube-prometheus-stack-prometheus"
    }
    
    port {
      name        = "http"
      port        = 9090
      target_port = 9090
    }
    
    type = "LoadBalancer"
  }
  
  depends_on = [helm_release.prometheus_stack]
}

# Service pour exposer Alertmanager
resource "kubernetes_service" "alertmanager" {
  metadata {
    name      = "alertmanager"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    
    annotations = {
      "metallb.universe.tf/address-pool" = "default"
    }
  }
  
  spec {
    selector = {
      "app.kubernetes.io/instance" = "kube-prometheus-stack"
      "app.kubernetes.io/name"     = "alertmanager"
      "alertmanager"               = "kube-prometheus-stack-alertmanager"
    }
    
    port {
      name        = "http"
      port        = 9093
      target_port = 9093
    }
    
    type = "LoadBalancer"
  }
  
  depends_on = [helm_release.prometheus_stack]
}

# ServiceMonitor pour MinIO
resource "kubernetes_manifest" "minio_service_monitor" {
  depends_on = [helm_release.prometheus]

  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "minio-metrics"
      namespace = var.namespace
      labels = {
        app = "minio"
      }
    }
    spec = {
      selector = {
        matchLabels = {
          app = "minio"
        }
      }
      endpoints = [
        {
          port = "api"
          path = "/minio/v2/metrics/cluster"
        }
      ]
    }
  }
}

# ServiceMonitor pour PostgreSQL
resource "kubernetes_manifest" "postgresql_service_monitor" {
  depends_on = [helm_release.prometheus]

  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "postgresql-metrics"
      namespace = var.namespace
      labels = {
        app = "postgresql"
      }
    }
    spec = {
      selector = {
        matchLabels = {
          app = "postgresql-exporter"
        }
      }
      endpoints = [
        {
          port = "metrics"
        }
      ]
    }
  }
}

# PostgreSQL Exporter
resource "kubernetes_deployment" "postgresql_exporter" {
  metadata {
    name      = "postgresql-exporter"
    namespace = var.namespace
    labels = {
      app = "postgresql-exporter"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "postgresql-exporter"
      }
    }

    template {
      metadata {
        labels = {
          app = "postgresql-exporter"
        }
      }

      spec {
        container {
          name  = "postgresql-exporter"
          image = "prometheuscommunity/postgres-exporter:${var.postgresql_exporter_version}"

          port {
            name           = "metrics"
            container_port = 9187
          }

          env {
            name  = "DATA_SOURCE_NAME"
            value = "postgresql://postgres:$(POSTGRES_PASSWORD)@postgresql:5432/postgres?sslmode=disable"
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = "postgresql-secrets"
                key  = "postgres-password"
              }
            }
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "200m"
              memory = "256Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgresql_exporter" {
  metadata {
    name      = "postgresql-exporter"
    namespace = var.namespace
    labels = {
      app = "postgresql-exporter"
    }
  }

  spec {
    selector = {
      app = "postgresql-exporter"
    }

    port {
      name        = "metrics"
      port        = 9187
      target_port = 9187
    }

    type = "ClusterIP"
  }
}

# Dashboards Grafana personnalisés
resource "kubernetes_config_map" "grafana_dashboards" {
  metadata {
    name      = "ml-pipeline-dashboards"
    namespace = var.namespace
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "ml-pipeline-overview.json" = file("${path.module}/dashboards/ml-pipeline-overview.json")
    "minio-dashboard.json"      = file("${path.module}/dashboards/minio-dashboard.json")
    "postgresql-dashboard.json" = file("${path.module}/dashboards/postgresql-dashboard.json")
    "tekton-dashboard.json"     = file("${path.module}/dashboards/tekton-dashboard.json")
  }
}

# AlertManager configuration
resource "kubernetes_secret" "alertmanager_config" {
  metadata {
    name      = "alertmanager-config"
    namespace = var.namespace
  }

  data = {
    "alertmanager.yml" = base64encode(templatefile("${path.module}/config/alertmanager.yml.tpl", {
      slack_webhook_url = var.slack_webhook_url
      email_to         = var.alert_email_to
      email_from       = var.alert_email_from
      smtp_host        = var.smtp_host
      smtp_port        = var.smtp_port
    }))
  }
}