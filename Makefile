.PHONY: help install-tekton install-mlflow install-starburst uninstall-all check-deps

# Environment variables
HELM := helm
KUBECTL := kubectl
HELM_CHARTS_DIR := ./infrastructure/helm-charts
NAMESPACE_TEKTON := tekton-pipelines
NAMESPACE_MLFLOW := mlflow
NAMESPACE_STARBURST := starburst

# Default help
help:
	@echo "\nCommandes disponibles :"
	@echo "  make help                 Affiche ce message d'aide"
	@echo "  make check-deps           Vérifie les dépendances requises"
	@echo "  make install-tekton       Installe Tekton"
	@echo "  make install-mlflow       Installe MLflow"
	@echo "  make install-starburst    Installe Starburst"
	@echo "  make install-all          Installe tous les composants"
	@echo "  make uninstall-tekton     Désinstalle Tekton"
	@echo "  make uninstall-mlflow     Désinstalle MLflow"
	@echo "  make uninstall-starburst  Désinstalle Starburst"
	@echo "  make uninstall-all        Désinstalle tous les composants"
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

# Update dependencies
update-deps:
	@echo "Mise à jour des dépendances des charts Helm..."
	@cd $(HELM_CHARTS_DIR)/tekton && $(HELM) dependency update
	@cd $(HELM_CHARTS_DIR)/mlflow && $(HELM) dependency update
	@cd $(HELM_CHARTS_DIR)/starburst && $(HELM) dependency update

# Install Tekton
install-tekton: check-deps
	@echo "Installation de Tekton..."
	@$(HELM) upgrade --install tekton $(HELM_CHARTS_DIR)/tekton \
		--namespace $(NAMESPACE_TEKTON) \
		--create-namespace \
		--wait \
		--timeout 5m

# Install MLflow
install-mlflow: check-deps
	@echo "Installation de MLflow..."
	@$(HELM) upgrade --install mlflow $(HELM_CHARTS_DIR)/mlflow \
		--namespace $(NAMESPACE_MLFLOW} \
		--create-namespace \
		--set mlflow.server.aws.accessKeyId=$(AWS_ACCESS_KEY_ID) \
		--set mlflow.server.aws.secretAccessKey=$(AWS_SECRET_ACCESS_KEY) \
		--set mlflow.server.aws.region=$(AWS_DEFAULT_REGION) \
		--set mlflow.server.auth.password=$(MLFLOW_ADMIN_PASSWORD) \
		--wait \
		--timeout 5m

# Install Starburst
install-starburst: check-deps
	@echo "Installation de Starburst..."
	@$(HELM) upgrade --install starburst $(HELM_CHARTS_DIR)/starburst \
		--namespace $(NAMESPACE_STARBURST} \
		--create-namespace \
		--set starburst.catalogs.hive.hive.s3.aws-access-key=$(AWS_ACCESS_KEY_ID) \
		--set starburst.catalogs.hive.hive.s3.aws-secret-key=$(AWS_SECRET_ACCESS_KEY) \
		--set starburst.catalogs.hive.hive.s3.region=$(AWS_DEFAULT_REGION) \
		--wait \
		--timeout 10m

# Install all components
install-all: check-deps create-namespaces update-deps install-tekton install-mlflow install-starburst
	@echo "Tous les composants ont été installés avec succès"

# Uninstall Tekton
uninstall-tekton:
	@echo "Désinstallation de Tekton..."
	@$(HELM) uninstall tekton --namespace $(NAMESPACE_TEKTON) || true
	@$(KUBECTL) delete namespace $(NAMESPACE_TEKTON) --ignore-not-found=true

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
uninstall-all: uninstall-tekton uninstall-mlflow uninstall-starburst
	@echo "Tous les composants ont été désinstallés"

# Check status
status:
	@echo "\n=== État des déploiements ==="
	@echo "\n[$(NAMESPACE_TEKTON)]"
	@$(KUBECTL) get pods,svc,ingress -n $(NAMESPACE_TEKTON) 2>/dev/null || echo "Aucune ressource trouvée dans $(NAMESPACE_TEKTON)"
	@echo "\n[$(NAMESPACE_MLFLOW)]"
	@$(KUBECTL) get pods,svc,ingress -n $(NAMESPACE_MLFLOW) 2>/dev/null || echo "Aucune ressource trouvée dans $(NAMESPACE_MLFLOW)"
	@echo "\n[$(NAMESPACE_STARBURST)]"
	@$(KUBECTL) get pods,svc,ingress -n $(NAMESPACE_STARBURST) 2>/dev/null || echo "Aucune ressource trouvée dans $(NAMESPACE_STARBURST)"
