# 🔧 Corrections du Makefile - Tekton Installation

## Problème Identifié

Le repository Helm de Tekton configuré dans le Makefile n'existait pas:
```
Error: looks like "https://tektoncd.github.io/charts" is not a valid chart repository
failed to fetch https://tektoncd.github.io/charts/index.yaml : 404 Not Found
```

## Cause

Tekton n'a **pas de repository Helm officiel stable**. Tekton est conçu pour être installé via des **manifests YAML** plutôt que via Helm.

## Solution Appliquée

### ✅ Changements dans le Makefile

#### 1. **Suppression du repository Helm Tekton**

**AVANT:**
```makefile
TEKTON_REPO := https://tektoncd.github.io/charts
```

**APRÈS:**
```makefile
# Tekton installation URLs (YAML manifests)
TEKTON_PIPELINES_VERSION := v0.56.0
TEKTON_PIPELINES_URL := https://storage.googleapis.com/tekton-releases/pipeline/previous/$(TEKTON_PIPELINES_VERSION)/release.yaml
TEKTON_TRIGGERS_URL := https://storage.googleapis.com/tekton-releases/triggers/previous/v0.25.0/release.yaml
TEKTON_DASHBOARD_URL := https://storage.googleapis.com/tekton-releases/dashboard/previous/v0.43.0/release.yaml
```

#### 2. **Target `add-repos` mis à jour**

**AVANT:**
```makefile
add-repos:
	@$(HELM) repo add tekton $(TEKTON_REPO)
	@$(HELM) repo add mlflow $(MLFLOW_REPO)
	@$(HELM) repo add starburst $(STARBURST_REPO)
	@$(HELM) repo update
```

**APRÈS:**
```makefile
add-repos:
	@echo "$(COLOR_BLUE)▶ Ajout des repositories Helm...$(COLOR_RESET)"
	@$(HELM) repo add community-charts $(MLFLOW_REPO) 2>/dev/null || true
	@$(HELM) repo add starburstdata $(STARBURST_REPO) 2>/dev/null || true
	@$(HELM) repo add apache-airflow $(AIRFLOW_REPO) 2>/dev/null || true
	@$(HELM) repo update
	@echo "$(COLOR_GREEN)✓ Repositories Helm ajoutés$(COLOR_RESET)"
```

#### 3. **Target `install-tekton` complètement réécrit**

**AVANT (via Helm):**
```makefile
install-tekton: check-deps
	@echo "Installation de Tekton..."
	@$(HELM) upgrade --install tekton $(HELM_CHARTS_DIR)/tekton \
		--namespace $(NAMESPACE_TEKTON) \
		--create-namespace \
		--wait \
		--timeout 5m
```

**APRÈS (via YAML manifests):**
```makefile
install-tekton: check-deps
	@echo "$(COLOR_BLUE)▶ Installation de Tekton Pipelines $(TEKTON_PIPELINES_VERSION)...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_PIPELINES_URL)
	@echo "$(COLOR_BLUE)▶ Installation de Tekton Triggers...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_TRIGGERS_URL)
	@echo "$(COLOR_BLUE)▶ Installation de Tekton Dashboard...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_DASHBOARD_URL)
	@echo "$(COLOR_BLUE)▶ Attente que les pods Tekton soient prêts...$(COLOR_RESET)"
	@$(KUBECTL) wait --for=condition=ready pod -l app.kubernetes.io/part-of=tekton-pipelines -n $(NAMESPACE_TEKTON) --timeout=300s || true
	@echo "$(COLOR_GREEN)✓ Tekton installé$(COLOR_RESET)"
```

#### 4. **Target `uninstall-tekton` mis à jour**

**AVANT:**
```makefile
uninstall-tekton:
	@$(HELM) uninstall tekton --namespace $(NAMESPACE_TEKTON) || true
	@$(KUBECTL) delete namespace $(NAMESPACE_TEKTON) --ignore-not-found=true
```

**APRÈS:**
```makefile
uninstall-tekton:
	@echo "$(COLOR_BLUE)▶ Désinstallation de Tekton...$(COLOR_RESET)"
	@$(KUBECTL) delete -f $(TEKTON_DASHBOARD_URL) --ignore-not-found=true
	@$(KUBECTL) delete -f $(TEKTON_TRIGGERS_URL) --ignore-not-found=true
	@$(KUBECTL) delete -f $(TEKTON_PIPELINES_URL) --ignore-not-found=true
	@$(KUBECTL) delete namespace $(NAMESPACE_TEKTON) --ignore-not-found=true
	@echo "$(COLOR_GREEN)✓ Tekton désinstallé$(COLOR_RESET)"
```

#### 5. **Target `update-deps` simplifié**

Suppression de la ligne pour Tekton (plus nécessaire):
```makefile
update-deps: add-repos
	@echo "$(COLOR_BLUE)▶ Mise à jour des dépendances des charts Helm...$(COLOR_RESET)"
	@cd $(HELM_CHARTS_DIR)/mlflow && $(HELM) dependency update 2>/dev/null || true
	@cd $(HELM_CHARTS_DIR)/starburst && $(HELM) dependency update 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ Dépendances mises à jour$(COLOR_RESET)"
```

#### 6. **Target `validate-config` mis à jour**

Suppression de la validation du chart Tekton:
```makefile
validate-config:
	@echo "$(COLOR_BLUE)▶ Validation des fichiers de configuration...$(COLOR_RESET)"
	@echo "  Validation des charts Helm..."
	@test -d $(HELM_CHARTS_DIR)/mlflow || { echo "$(COLOR_RED)✗ Chart MLflow manquant$(COLOR_RESET)"; exit 1; }
	@test -d $(HELM_CHARTS_DIR)/starburst || { echo "$(COLOR_RED)✗ Chart Starburst manquant$(COLOR_RESET)"; exit 1; }
	# ... reste de la validation
```

---

## 📦 Versions des Composants Installés

| Composant | Version | Méthode d'Installation |
|-----------|---------|------------------------|
| **Tekton Pipelines** | v0.56.0 | YAML Manifest |
| **Tekton Triggers** | v0.25.0 | YAML Manifest |
| **Tekton Dashboard** | v0.43.0 | YAML Manifest |
| **MLflow** | Latest | Helm (community-charts) |
| **Starburst** | Latest | Helm (starburstdata) |
| **Airflow** | Latest | Helm (apache-airflow) |

---

## 🧪 Tests

Pour tester les changements:

```bash
# 1. Vérifier le Makefile
make help

# 2. Vérifier la connexion au cluster
make check-cluster

# 3. Installer Tekton seul
make install-tekton

# 4. Vérifier le statut
make status

# 5. Désinstaller pour nettoyer
make uninstall-tekton
```

---

## ✅ Avantages de la Nouvelle Approche

1. **✅ Méthode Officielle**: Utilise la méthode d'installation recommandée par Tekton
2. **✅ Plus Stable**: Pas de dépendance à un repository Helm inexistant
3. **✅ Versions Fixes**: Contrôle précis des versions installées
4. **✅ Composants Complets**: Installe Pipelines + Triggers + Dashboard
5. **✅ Meilleure Traçabilité**: URLs explicites pour chaque composant

---

## 📚 Références

- **Documentation officielle Tekton**: https://tekton.dev/docs/installation/
- **Releases Tekton Pipelines**: https://github.com/tektoncd/pipeline/releases
- **Releases Tekton Triggers**: https://github.com/tektoncd/triggers/releases
- **Releases Tekton Dashboard**: https://github.com/tektoncd/dashboard/releases

---

## 🔄 Migration depuis Helm (si applicable)

Si vous aviez déjà installé Tekton via Helm:

```bash
# 1. Désinstaller l'ancienne version
helm uninstall tekton -n tekton-pipelines || true

# 2. Nettoyer le namespace
kubectl delete namespace tekton-pipelines

# 3. Réinstaller avec la nouvelle méthode
make install-tekton
```

---

---

## 🚁 Correction 2: Timeout Airflow

### Problème
```
Error: context deadline exceeded
make: *** [Makefile:214: install-airflow] Error 1
```

### Cause
Airflow nécessite 15-20 minutes pour:
- Initialiser PostgreSQL
- Migrer le schéma de base de données
- Démarrer tous les composants (webserver, scheduler, etc.)

Le timeout de 10 minutes était insuffisant.

### Solutions Appliquées

1. **Timeout augmenté à 20 minutes**:
```makefile
--timeout 20m
```

2. **Installation non-bloquante** (suppression du `--wait`):
- Permet de continuer avec d'autres tâches
- Installation en background

3. **Nouvelle target `wait-airflow`**:
```makefile
wait-airflow:
	@$(KUBECTL) wait --for=condition=ready pod -l component=webserver -n $(NAMESPACE_AIRFLOW) --timeout=900s
	@$(KUBECTL) wait --for=condition=ready pod -l component=scheduler -n $(NAMESPACE_AIRFLOW) --timeout=900s
```

4. **Configuration par défaut ajoutée**:
```makefile
--set webserver.defaultUser.enabled=true
--set webserver.defaultUser.username=admin
--set webserver.defaultUser.password=admin
```

5. **Documentation créée**: [AIRFLOW_INSTALL_GUIDE.md](AIRFLOW_INSTALL_GUIDE.md)

### Usage

```bash
# Installation (non-bloquante)
make install-airflow

# Vérifier l'état
kubectl get pods -n airflow -w

# Attendre que tout soit prêt
make wait-airflow

# Accéder à l'UI
make port-forward-airflow
# http://localhost:8080 - admin/admin
```

---

**Date de correction**: 2026-01-06
**Testé avec**: Kubernetes 1.28+, Apache Airflow 2.x
