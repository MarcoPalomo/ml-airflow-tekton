# 🚁 Guide d'Installation Airflow

## Problème Courant: Timeout lors de l'Installation

### Symptôme
```
Error: context deadline exceeded
make: *** [Makefile:214: install-airflow] Error 1
```

### Cause
Airflow est un composant **très lourd** qui nécessite:
- Initialisation d'une base de données PostgreSQL
- Migration de schéma (peut prendre 5-10 minutes)
- Démarrage de plusieurs composants (webserver, scheduler, triggerer, etc.)
- Téléchargement d'images Docker volumineuses

Le timeout par défaut de 10 minutes n'est **pas suffisant** pour la première installation.

---

## ✅ Solution Appliquée

### 1. **Configuration Optimisée**

Un fichier `infrastructure/airflow-values.yaml` a été créé avec une configuration optimisée:
- Redis désactivé (pas nécessaire avec KubernetesExecutor)
- Triggerer désactivé (non essentiel)
- Ressources réduites pour démarrage plus rapide
- Persistence désactivée pour simplifier l'installation initiale

### 2. **Timeout augmenté à 30 minutes**

```makefile
--timeout 30m
```

### 3. **Installation Automatique**

Le Makefile détecte automatiquement le fichier `airflow-values.yaml` et l'utilise si disponible:
```bash
make install-airflow  # Utilise airflow-values.yaml automatiquement
```

### 4. **Nouvelle commande `make wait-airflow`**

```bash
make wait-airflow
```

Cette commande attend que les composants essentiels soient prêts:
- Webserver (UI)
- Scheduler (orchestration)

Timeout: 15 minutes (900 secondes)

---

## 📋 Workflow d'Installation Recommandé

### Installation Complète

```bash
# 1. Installer Airflow (non-bloquant)
make install-airflow

# 2. Vérifier l'état pendant l'installation
watch kubectl get pods -n airflow

# 3. Attendre que tout soit prêt (optionnel)
make wait-airflow

# 4. Vérifier le déploiement
make status
make test-deployment
```

### Installation Rapide (sans attente)

```bash
# Installer en arrière-plan
make install-airflow

# Continuer avec d'autres tâches
# Airflow continuera à s'initialiser en background
```

---

## 🔍 Diagnostic et Debugging

### Vérifier l'État des Pods

```bash
# État général
kubectl get pods -n airflow

# Détails d'un pod spécifique
kubectl describe pod <pod-name> -n airflow

# Logs du webserver
kubectl logs -n airflow -l component=webserver --tail=100

# Logs du scheduler
kubectl logs -n airflow -l component=scheduler --tail=100
```

### Événements du Namespace

```bash
# Voir tous les événements (utile pour diagnostiquer les problèmes)
kubectl get events -n airflow --sort-by='.lastTimestamp'
```

### Pods en Erreur

```bash
# Lister les pods qui ne sont pas en Running
kubectl get pods -n airflow | grep -v Running

# Supprimer les pods en erreur (ils redémarreront)
kubectl delete pod <pod-name> -n airflow
```

---

## ⏱️ Temps d'Installation Typiques

| Phase | Durée Estimée |
|-------|---------------|
| **Helm install** | 1-2 minutes |
| **PostgreSQL init** | 3-5 minutes |
| **Database migration** | 5-8 minutes |
| **Webserver ready** | 2-3 minutes |
| **Scheduler ready** | 1-2 minutes |
| **TOTAL** | **12-20 minutes** |

---

## 🛠️ Commandes Utiles

### Vérifier la Version d'Airflow Installée

```bash
kubectl exec -n airflow <webserver-pod> -- airflow version
```

### Accéder à l'UI Airflow

```bash
# Port-forward (bloquant)
make port-forward-airflow

# Accéder à http://localhost:8080
# Login: admin / admin
```

### Récupérer le Mot de Passe Admin

Si vous n'avez pas défini de mot de passe personnalisé:

```bash
kubectl get secret airflow-webserver-secret -n airflow \
  -o jsonpath='{.data.webserver-secret-key}' | base64 -d
```

---

## 🔧 Personnalisation de l'Installation

### Fichier de Configuration Optimisé (Déjà Fourni)

Le fichier [`infrastructure/airflow-values.yaml`](infrastructure/airflow-values.yaml) est déjà configuré avec des paramètres optimisés pour une installation rapide:

```yaml
# Configuration simplifiée
executor: KubernetesExecutor
redis:
  enabled: false  # Pas nécessaire
triggerer:
  enabled: false  # Non essentiel
postgresql:
  enabled: true
  auth:
    postgresPassword: postgres
webserver:
  defaultUser:
    username: admin
    password: admin
```

Cette configuration est **automatiquement utilisée** par `make install-airflow`.

### Modifier les Valeurs Helm (Avancé)

Pour personnaliser davantage, éditez `infrastructure/airflow-values.yaml`:

```yaml
# airflow-values.yaml
executor: KubernetesExecutor

webserver:
  defaultUser:
    enabled: true
    username: admin
    password: votre-mot-de-passe-securise
    email: admin@example.com

postgresql:
  enabled: true
  persistence:
    enabled: true
    size: 10Gi

redis:
  enabled: false  # Pas nécessaire avec KubernetesExecutor

config:
  core:
    dags_folder: /opt/airflow/dags
  webserver:
    expose_config: 'True'
```

Puis installer avec:

```bash
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow \
  --create-namespace \
  --values airflow-values.yaml \
  --timeout 20m
```

---

## 🐛 Problèmes Courants et Solutions

### 1. Pod PostgreSQL en CrashLoopBackOff

**Cause**: Problème de permissions ou de stockage

**Solution**:
```bash
# Vérifier les PVC
kubectl get pvc -n airflow

# Si nécessaire, supprimer et réinstaller
make uninstall-airflow
kubectl delete pvc --all -n airflow
make install-airflow
```

### 2. Webserver en ImagePullBackOff

**Cause**: Problème de téléchargement d'image Docker

**Solution**:
```bash
# Vérifier les événements
kubectl describe pod <pod-name> -n airflow

# Le téléchargement peut prendre du temps (image ~1GB)
# Attendre quelques minutes
```

### 3. Database Migration Timeout

**Cause**: La migration de schéma prend trop de temps

**Solution**:
```bash
# Vérifier les logs du job de migration
kubectl logs -n airflow -l component=migration --tail=100

# Augmenter les ressources PostgreSQL si nécessaire
```

### 4. Scheduler ne Démarre pas

**Cause**: Dépendance sur la base de données

**Solution**:
```bash
# S'assurer que PostgreSQL est prêt
kubectl get pods -n airflow | grep postgres

# Vérifier les logs du scheduler
kubectl logs -n airflow -l component=scheduler --tail=100

# Si besoin, redémarrer le scheduler
kubectl delete pod -n airflow -l component=scheduler
```

---

## 📊 Monitoring après Installation

### Dashboard Kubernetes

```bash
# Si vous avez le dashboard K8s installé
kubectl proxy
# Accéder à http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### Métriques des Pods

```bash
# CPU et mémoire
kubectl top pods -n airflow

# Si 'top' ne fonctionne pas, installer metrics-server:
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## 🔄 Mise à Jour d'Airflow

```bash
# Mettre à jour vers la dernière version
helm repo update
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --timeout 20m

# Vérifier la nouvelle version
kubectl exec -n airflow deployment/airflow-webserver -- airflow version
```

---

## 🗑️ Désinstallation Complète

```bash
# Désinstaller Airflow
make uninstall-airflow

# Ou manuellement
helm uninstall airflow -n airflow
kubectl delete namespace airflow

# Supprimer les PVC (données persistantes)
kubectl delete pvc -l app.kubernetes.io/instance=airflow -n airflow
```

---

## 📚 Ressources

- **Documentation Officielle Airflow**: https://airflow.apache.org/docs/
- **Chart Helm Airflow**: https://airflow.apache.org/docs/helm-chart/stable/index.html
- **Kubernetes Executor**: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html
- **Troubleshooting**: https://airflow.apache.org/docs/apache-airflow/stable/troubleshooting.html

---

## ✅ Checklist Post-Installation

- [ ] PostgreSQL pod en Running
- [ ] Webserver pod en Running
- [ ] Scheduler pod en Running
- [ ] `make test-deployment` passe
- [ ] Accès à l'UI via `make port-forward-airflow`
- [ ] Login avec admin/admin fonctionne
- [ ] Pas d'erreurs dans les logs (`make logs COMPONENT=airflow`)

---

**Dernière mise à jour**: 2026-01-06
**Testé avec**: Apache Airflow 2.x, Kubernetes 1.28+
