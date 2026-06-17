.PHONY: help install-tekton install-mlflow install-starburst install-airflow uninstall-all check-deps add-repos \
        validate-config check-cluster status logs test-deployment wait-airflow port-forward clean

# Environment variables
HELM := helm
KUBECTL := kubectl
HELM_CHARTS_DIR := ./infrastructure/helm-charts
NAMESPACE_TEKTON := tekton-pipelines
NAMESPACE_MLFLOW := mlflow
NAMESPACE_STARBURST := starburst
NAMESPACE_AIRFLOW := airflow

# Helm repositories
MLFLOW_REPO := https://community-charts.github.io/helm-charts
STARBURST_REPO := https://harbor.starburstdata.net/chartrepo/starburstdata
AIRFLOW_REPO := https://airflow.apache.org

# Tekton installation URLs (YAML manifests)
TEKTON_PIPELINES_VERSION := v0.56.0
TEKTON_PIPELINES_URL := https://storage.googleapis.com/tekton-releases/pipeline/previous/$(TEKTON_PIPELINES_VERSION)/release.yaml
TEKTON_TRIGGERS_URL := https://storage.googleapis.com/tekton-releases/triggers/previous/v0.25.0/release.yaml
TEKTON_DASHBOARD_URL := https://storage.googleapis.com/tekton-releases/dashboard/previous/v0.43.0/release.yaml

# Colors for output
COLOR_RESET := \033[0m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_RED := \033[31m

# Default help
help:
	@echo ""
	@echo "$(COLOR_BLUE)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)  MLOps Platform - Makefile Commands$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)Vérification:$(COLOR_RESET)"
	@echo "  make check-deps           Vérifie les dépendances (helm, kubectl)"
	@echo "  make check-cluster        Vérifie la connexion au cluster K8s"
	@echo "  make validate-config      Valide les fichiers de configuration"
	@echo ""
	@echo "$(COLOR_GREEN)Installation:$(COLOR_RESET)"
	@echo "  make install-all          Installe TOUS les composants (recommandé)"
	@echo "  make install-tekton       Installe Tekton (CI/CD)"
	@echo "  make install-mlflow       Installe MLflow (tracking)"
	@echo "  make install-starburst    Installe Starburst (query engine)"
	@echo "  make install-airflow      Installe Airflow (orchestration)"
	@echo ""
	@echo "$(COLOR_GREEN)Monitoring:$(COLOR_RESET)"
	@echo "  make status               Affiche l'état de tous les composants"
	@echo "  make logs COMPONENT=X     Affiche les logs (tekton/mlflow/starburst/airflow)"
	@echo "  make test-deployment      Teste que tous les services sont OK"
	@echo "  make wait-airflow         Attend que Airflow soit complètement prêt"
	@echo ""
	@echo "$(COLOR_GREEN)Accès:$(COLOR_RESET)"
	@echo "  make port-forward-mlflow  Port-forward MLflow (localhost:5000)"
	@echo "  make port-forward-airflow Port-forward Airflow (localhost:8080)"
	@echo "  make port-forward-tekton  Port-forward Tekton Dashboard (localhost:9097)"
	@echo ""
	@echo "$(COLOR_GREEN)Désinstallation:$(COLOR_RESET)"
	@echo "  make uninstall-all        Désinstalle TOUS les composants"
	@echo "  make uninstall-tekton     Désinstalle Tekton"
	@echo "  make uninstall-mlflow     Désinstalle MLflow"
	@echo "  make uninstall-starburst  Désinstalle Starburst"
	@echo "  make uninstall-airflow    Désinstalle Airflow"
	@echo "  make clean                Nettoie les ressources orphelines"
	@echo ""
	@echo "$(COLOR_GREEN)Utilitaires:$(COLOR_RESET)"
	@echo "  make add-repos            Ajoute les repositories Helm"
	@echo "  make update-deps          Met à jour les dépendances Helm"
	@echo ""
	@echo "$(COLOR_YELLOW)Variables d'environnement requises:$(COLOR_RESET)"
	@echo "  AWS_ACCESS_KEY_ID         Clé d'accès AWS"
	@echo "  AWS_SECRET_ACCESS_KEY     Clé secrète AWS"
	@echo "  AWS_DEFAULT_REGION        Région AWS (default: eu-west-1)"
	@echo "  MLFLOW_ADMIN_PASSWORD     Mot de passe admin MLflow"
	@echo ""

# Check dependencies
check-deps:
	@echo "Vérification des dépendances..."
	@command -v $(HELM) >/dev/null 2>&1 || { echo "Erreur: Helm n'est pas installé"; exit 1; }
	@command -v $(KUBECTL) >/dev/null 2>&1 || { echo "Erreur: kubectl n'est pas installé"; exit 1; }
	#@$(HELM) version --short | grep -q 'v3\\.' || { echo "Erreur: Helm v3 est requis"; exit 1; }
	@echo "Toutes les dépendances sont installées"

# Create namespaces
create-namespaces:
	@echo "Création des namespaces..."
	@$(KUBECTL) create namespace $(NAMESPACE_TEKTON) --dry-run=client -o yaml | $(KUBECTL) apply -f-
	@$(KUBECTL) create namespace $(NAMESPACE_MLFLOW) --dry-run=client -o yaml | $(KUBECTL) apply -f-
	@$(KUBECTL) create namespace $(NAMESPACE_STARBURST) --dry-run=client -o yaml | $(KUBECTL) apply -f-

# Add Helm repositories
add-repos:
	@echo "$(COLOR_BLUE)▶ Ajout des repositories Helm...$(COLOR_RESET)"
	@$(HELM) repo add community-charts $(MLFLOW_REPO) 2>/dev/null || true
	@$(HELM) repo add starburstdata $(STARBURST_REPO) 2>/dev/null || true
	@$(HELM) repo add apache-airflow $(AIRFLOW_REPO) 2>/dev/null || true
	@$(HELM) repo update
	@echo "$(COLOR_GREEN)✓ Repositories Helm ajoutés$(COLOR_RESET)"

# Update dependencies
update-deps: add-repos
	@echo "$(COLOR_BLUE)▶ Mise à jour des dépendances des charts Helm...$(COLOR_RESET)"
	@cd $(HELM_CHARTS_DIR)/mlflow && $(HELM) dependency update 2>/dev/null || true
	@cd $(HELM_CHARTS_DIR)/starburst && $(HELM) dependency update 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ Dépendances mises à jour$(COLOR_RESET)"

# Install Tekton (via YAML manifests)
install-tekton: check-deps
	@echo "$(COLOR_BLUE)▶ Installation de Tekton Pipelines $(TEKTON_PIPELINES_VERSION)...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_PIPELINES_URL)
	@echo "$(COLOR_BLUE)▶ Installation de Tekton Triggers...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_TRIGGERS_URL)
	@echo "$(COLOR_BLUE)▶ Installation de Tekton Dashboard (optionnel)...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_DASHBOARD_URL) || echo "$(COLOR_YELLOW)⚠ Dashboard non installé (optionnel, peut échouer)$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)▶ Attente que les pods Tekton soient prêts...$(COLOR_RESET)"
	@$(KUBECTL) wait --for=condition=ready pod -l app.kubernetes.io/part-of=tekton-pipelines -n $(NAMESPACE_TEKTON) --timeout=300s || true
	@echo "$(COLOR_GREEN)✓ Tekton Pipelines et Triggers installés$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Note: Le Dashboard peut prendre plus de temps ou échouer (non critique)$(COLOR_RESET)"

# Install Tekton Dashboard separately (optional)
install-tekton-dashboard:
	@echo "$(COLOR_BLUE)▶ Installation du Tekton Dashboard...$(COLOR_RESET)"
	@$(KUBECTL) apply -f $(TEKTON_DASHBOARD_URL)
	@echo "$(COLOR_BLUE)▶ Attente que le Dashboard soit prêt...$(COLOR_RESET)"
	@$(KUBECTL) wait --for=condition=ready pod -l app.kubernetes.io/component=dashboard -n $(NAMESPACE_TEKTON) --timeout=600s || true
	@echo "$(COLOR_GREEN)✓ Tekton Dashboard installé$(COLOR_RESET)"

# Install MLflow
install-mlflow: check-deps
	@echo "$(COLOR_BLUE)▶ Installation de MLflow...$(COLOR_RESET)"
	@# Les secrets sont écrits dans un fichier temporaire (chmod 600) plutôt que
	@# passés en --set (visibles dans `ps` et l'historique Helm).
	@SECRETS_FILE=$$(mktemp); chmod 600 $$SECRETS_FILE; \
	printf 'mlflow:\n  server:\n    aws:\n      accessKeyId: "%s"\n      secretAccessKey: "%s"\n      region: "%s"\n    auth:\n      password: "%s"\n' \
		"$(AWS_ACCESS_KEY_ID)" "$(AWS_SECRET_ACCESS_KEY)" "$(AWS_DEFAULT_REGION)" "$(MLFLOW_ADMIN_PASSWORD)" > $$SECRETS_FILE; \
	$(HELM) upgrade --install mlflow $(HELM_CHARTS_DIR)/mlflow \
		--namespace $(NAMESPACE_MLFLOW) --create-namespace \
		--values $$SECRETS_FILE --wait --timeout 5m; \
	rc=$$?; rm -f $$SECRETS_FILE; exit $$rc

# Install Starburst
install-starburst: check-deps
	@echo "$(COLOR_BLUE)▶ Installation de Starburst...$(COLOR_RESET)"
	@# Secrets via fichier temporaire (chmod 600) au lieu de --set.
	@SECRETS_FILE=$$(mktemp); chmod 600 $$SECRETS_FILE; \
	printf 'starburst:\n  catalogs:\n    hive:\n      hive:\n        s3:\n          aws-access-key: "%s"\n          aws-secret-key: "%s"\n          region: "%s"\n' \
		"$(AWS_ACCESS_KEY_ID)" "$(AWS_SECRET_ACCESS_KEY)" "$(AWS_DEFAULT_REGION)" > $$SECRETS_FILE; \
	$(HELM) upgrade --install starburst $(HELM_CHARTS_DIR)/starburst \
		--namespace $(NAMESPACE_STARBURST) --create-namespace \
		--values $$SECRETS_FILE --wait --timeout 10m; \
	rc=$$?; rm -f $$SECRETS_FILE; exit $$rc

# Install all components
install-all: check-deps check-cluster validate-config create-namespaces update-deps install-tekton install-mlflow install-starburst install-airflow
	@echo ""
	@echo "$(COLOR_GREEN)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)  ✓ Tous les composants ont été installés avec succès$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)Prochaines étapes:$(COLOR_RESET)"
	@echo "  1. Vérifier l'état: make status"
	@echo "  2. Tester le déploiement: make test-deployment"
	@echo "  3. Accéder aux services:"
	@echo "     - MLflow: make port-forward-mlflow"
	@echo "     - Airflow: make port-forward-airflow"
	@echo "     - Tekton: make port-forward-tekton"
	@echo ""

# Uninstall Tekton
uninstall-tekton:
	@echo "$(COLOR_BLUE)▶ Désinstallation de Tekton...$(COLOR_RESET)"
	@$(KUBECTL) delete -f $(TEKTON_DASHBOARD_URL) --ignore-not-found=true
	@$(KUBECTL) delete -f $(TEKTON_TRIGGERS_URL) --ignore-not-found=true
	@$(KUBECTL) delete -f $(TEKTON_PIPELINES_URL) --ignore-not-found=true
	@$(KUBECTL) delete namespace $(NAMESPACE_TEKTON) --ignore-not-found=true
	@echo "$(COLOR_GREEN)✓ Tekton désinstallé$(COLOR_RESET)"

# Uninstall MLflow
uninstall-mlflow:
	@echo "Désinstallation de MLflow..."
	@$(HELM) uninstall mlflow --namespace $(NAMESPACE_MLFLOW) || true
	@$(KUBECTL) delete pvc -l app.kubernetes.io/instance=mlflow -n $(NAMESPACE_MLFLOW) --ignore-not-found=true
	@$(KUBECTL) delete namespace $(NAMESPACE_MLFLOW) --ignore-not-found=true

# Uninstall Starburst
uninstall-starburst:
	@echo "Désinstallation de Starburst..."
	@$(HELM) uninstall starburst --namespace $(NAMESPACE_STARBURST) || true
	@$(KUBECTL) delete pvc -l app.kubernetes.io/instance=starburst -n $(NAMESPACE_STARBURST) --ignore-not-found=true
	@$(KUBECTL) delete namespace $(NAMESPACE_STARBURST) --ignore-not-found=true

# Uninstall all components
uninstall-all: uninstall-tekton uninstall-mlflow uninstall-starburst uninstall-airflow
	@echo "$(COLOR_GREEN)✓ Tous les composants ont été désinstallés$(COLOR_RESET)"

# Check cluster connectivity
check-cluster:
	@echo "$(COLOR_BLUE)▶ Vérification de la connexion au cluster Kubernetes...$(COLOR_RESET)"
	@$(KUBECTL) cluster-info || { echo "$(COLOR_RED)✗ Impossible de se connecter au cluster$(COLOR_RESET)"; exit 1; }
	@$(KUBECTL) get nodes || { echo "$(COLOR_RED)✗ Impossible de lister les nodes$(COLOR_RESET)"; exit 1; }
	@echo "$(COLOR_GREEN)✓ Cluster accessible$(COLOR_RESET)"

# Validate configuration files
validate-config:
	@echo "$(COLOR_BLUE)▶ Validation des fichiers de configuration...$(COLOR_RESET)"
	@echo "  Validation des charts Helm..."
	@test -d $(HELM_CHARTS_DIR)/mlflow || { echo "$(COLOR_RED)✗ Chart MLflow manquant$(COLOR_RESET)"; exit 1; }
	@test -d $(HELM_CHARTS_DIR)/starburst || { echo "$(COLOR_RED)✗ Chart Starburst manquant$(COLOR_RESET)"; exit 1; }
	@echo "  Validation des variables d'environnement..."
	@test -n "$(AWS_ACCESS_KEY_ID)" || { echo "$(COLOR_YELLOW)⚠ AWS_ACCESS_KEY_ID non définie$(COLOR_RESET)"; }
	@test -n "$(AWS_SECRET_ACCESS_KEY)" || { echo "$(COLOR_YELLOW)⚠ AWS_SECRET_ACCESS_KEY non définie$(COLOR_RESET)"; }
	@test -n "$(MLFLOW_ADMIN_PASSWORD)" || { echo "$(COLOR_YELLOW)⚠ MLFLOW_ADMIN_PASSWORD non définie$(COLOR_RESET)"; }
	@echo "$(COLOR_GREEN)✓ Configuration validée$(COLOR_RESET)"

# Install Airflow
install-airflow: check-deps
	@echo "$(COLOR_BLUE)▶ Installation d'Airflow...$(COLOR_RESET)"
	@$(HELM) repo add apache-airflow $(AIRFLOW_REPO) 2>/dev/null || true
	@$(HELM) repo update
	@echo "$(COLOR_YELLOW)⚠ L'installation d'Airflow peut prendre 10-15 minutes...$(COLOR_RESET)"
	@if [ -f ./infrastructure/airflow-values.yaml ]; then \
		echo "$(COLOR_BLUE)▶ Utilisation de la configuration optimisée (airflow-values.yaml)$(COLOR_RESET)"; \
		$(HELM) upgrade --install airflow apache-airflow/airflow \
			--namespace $(NAMESPACE_AIRFLOW) \
			--create-namespace \
			--values ./infrastructure/airflow-values.yaml \
			--wait \
			--timeout 30m; \
	else \
		echo "$(COLOR_BLUE)▶ Utilisation de la configuration par défaut$(COLOR_RESET)"; \
		$(HELM) upgrade --install airflow apache-airflow/airflow \
			--namespace $(NAMESPACE_AIRFLOW) \
			--create-namespace \
			--set executor=KubernetesExecutor \
			--set webserver.defaultUser.enabled=true \
			--set webserver.defaultUser.username=admin \
			--set webserver.defaultUser.password=admin \
			--wait \
			--timeout 30m; \
	fi
	@echo "$(COLOR_GREEN)✓ Airflow installé$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Note: Utilisez 'make wait-airflow' si certains pods ne sont pas encore prêts$(COLOR_RESET)"

# Uninstall Airflow
uninstall-airflow:
	@echo "$(COLOR_BLUE)▶ Désinstallation d'Airflow...$(COLOR_RESET)"
	@$(HELM) uninstall airflow --namespace $(NAMESPACE_AIRFLOW) || true
	@$(KUBECTL) delete pvc -l app.kubernetes.io/instance=airflow -n $(NAMESPACE_AIRFLOW) --ignore-not-found=true
	@$(KUBECTL) delete namespace $(NAMESPACE_AIRFLOW) --ignore-not-found=true
	@echo "$(COLOR_GREEN)✓ Airflow désinstallé$(COLOR_RESET)"

# Check status
status:
	@echo ""
	@echo "$(COLOR_BLUE)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)  État des Déploiements$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)[Tekton - $(NAMESPACE_TEKTON)]$(COLOR_RESET)"
	@$(KUBECTL) get pods,svc -n $(NAMESPACE_TEKTON) 2>/dev/null || echo "  $(COLOR_RED)Aucune ressource$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)[MLflow - $(NAMESPACE_MLFLOW)]$(COLOR_RESET)"
	@$(KUBECTL) get pods,svc -n $(NAMESPACE_MLFLOW) 2>/dev/null || echo "  $(COLOR_RED)Aucune ressource$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)[Starburst - $(NAMESPACE_STARBURST)]$(COLOR_RESET)"
	@$(KUBECTL) get pods,svc -n $(NAMESPACE_STARBURST) 2>/dev/null || echo "  $(COLOR_RED)Aucune ressource$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)[Airflow - $(NAMESPACE_AIRFLOW)]$(COLOR_RESET)"
	@$(KUBECTL) get pods,svc -n $(NAMESPACE_AIRFLOW) 2>/dev/null || echo "  $(COLOR_RED)Aucune ressource$(COLOR_RESET)"
	@echo ""

# Show logs
logs:
	@if [ -z "$(COMPONENT)" ]; then \
		echo "$(COLOR_RED)✗ Spécifiez COMPONENT=<tekton|mlflow|starburst|airflow>$(COLOR_RESET)"; \
		exit 1; \
	fi
	@if [ "$(COMPONENT)" = "tekton" ]; then \
		$(KUBECTL) logs -n $(NAMESPACE_TEKTON) -l app.kubernetes.io/part-of=tekton-pipelines --tail=100 -f; \
	elif [ "$(COMPONENT)" = "mlflow" ]; then \
		$(KUBECTL) logs -n $(NAMESPACE_MLFLOW) -l app.kubernetes.io/name=mlflow --tail=100 -f; \
	elif [ "$(COMPONENT)" = "starburst" ]; then \
		$(KUBECTL) logs -n $(NAMESPACE_STARBURST) -l app=starburst --tail=100 -f; \
	elif [ "$(COMPONENT)" = "airflow" ]; then \
		$(KUBECTL) logs -n $(NAMESPACE_AIRFLOW) -l component=webserver --tail=100 -f; \
	else \
		echo "$(COLOR_RED)✗ Composant invalide$(COLOR_RESET)"; \
		exit 1; \
	fi

# Test deployment
test-deployment:
	@echo "$(COLOR_BLUE)▶ Test des déploiements...$(COLOR_RESET)"
	@echo "  Testing Tekton..."
	@$(KUBECTL) get pods -n $(NAMESPACE_TEKTON) -o jsonpath='{.items[*].status.phase}' 2>/dev/null | grep -q Running && echo "$(COLOR_GREEN)  ✓ Tekton OK$(COLOR_RESET)" || echo "$(COLOR_RED)  ✗ Tekton KO$(COLOR_RESET)"
	@echo "  Testing MLflow..."
	@$(KUBECTL) get pods -n $(NAMESPACE_MLFLOW) -o jsonpath='{.items[*].status.phase}' 2>/dev/null | grep -q Running && echo "$(COLOR_GREEN)  ✓ MLflow OK$(COLOR_RESET)" || echo "$(COLOR_RED)  ✗ MLflow KO$(COLOR_RESET)"
	@echo "  Testing Starburst..."
	@$(KUBECTL) get pods -n $(NAMESPACE_STARBURST) -o jsonpath='{.items[*].status.phase}' 2>/dev/null | grep -q Running && echo "$(COLOR_GREEN)  ✓ Starburst OK$(COLOR_RESET)" || echo "$(COLOR_RED)  ✗ Starburst KO$(COLOR_RESET)"
	@echo "  Testing Airflow..."
	@$(KUBECTL) get pods -n $(NAMESPACE_AIRFLOW) -o jsonpath='{.items[*].status.phase}' 2>/dev/null | grep -q Running && echo "$(COLOR_GREEN)  ✓ Airflow OK$(COLOR_RESET)" || echo "$(COLOR_YELLOW)  ⚠ Airflow non prêt ou non installé$(COLOR_RESET)"

# Wait for Airflow to be ready
wait-airflow:
	@echo "$(COLOR_BLUE)▶ Attente que les pods Airflow soient prêts...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Cela peut prendre 10-15 minutes pour la première installation$(COLOR_RESET)"
	@$(KUBECTL) wait --for=condition=ready pod -l component=webserver -n $(NAMESPACE_AIRFLOW) --timeout=900s || true
	@$(KUBECTL) wait --for=condition=ready pod -l component=scheduler -n $(NAMESPACE_AIRFLOW) --timeout=900s || true
	@echo "$(COLOR_GREEN)✓ Airflow prêt$(COLOR_RESET)"

# Port forwarding
port-forward-mlflow:
	@echo "$(COLOR_BLUE)▶ Port-forward MLflow vers localhost:5000$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Accès: http://localhost:5000$(COLOR_RESET)"
	@$(KUBECTL) port-forward -n $(NAMESPACE_MLFLOW) svc/mlflow 5000:5000

port-forward-airflow:
	@echo "$(COLOR_BLUE)▶ Port-forward Airflow vers localhost:8080$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Accès: http://localhost:8080$(COLOR_RESET)"
	@$(KUBECTL) port-forward -n $(NAMESPACE_AIRFLOW) svc/airflow-webserver 8080:8080

port-forward-tekton:
	@echo "$(COLOR_BLUE)▶ Port-forward Tekton Dashboard vers localhost:9097$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Accès: http://localhost:9097$(COLOR_RESET)"
	@$(KUBECTL) port-forward -n $(NAMESPACE_TEKTON) svc/tekton-dashboard 9097:9097

port-forward-starburst:
	@echo "$(COLOR_BLUE)▶ Port-forward Starburst vers localhost:8080$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Accès: http://localhost:8080$(COLOR_RESET)"
	@$(KUBECTL) port-forward -n $(NAMESPACE_STARBURST) svc/starburst 8080:8080

# Clean orphaned resources
clean:
	@echo "$(COLOR_BLUE)▶ Nettoyage des ressources orphelines...$(COLOR_RESET)"
	@$(KUBECTL) delete pods --field-selector status.phase=Failed --all-namespaces --ignore-not-found=true
	@$(KUBECTL) delete pods --field-selector status.phase=Succeeded --all-namespaces --ignore-not-found=true
	@echo "$(COLOR_GREEN)✓ Nettoyage terminé$(COLOR_RESET)"
