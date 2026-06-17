# Pipeline MLOps avec Airflow et Tekton

Ce dépôt contient une implémentation d'un pipeline MLOps complet utilisant Airflow pour l'orchestration des workflows et Tekton pour l'intégration et le déploiement continus.

## Table des matières

- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Structure du Projet](#-structure-du-projet)
- [Développement](#-développement)
- [Déploiement](#-déploiement)
- [Maintenance](#-maintenance)
- [Contributions](#-contributions)
- [Licence](#-licence)

## Architecture

Le projet suit une architecture modulaire avec les composants principaux suivants :

- **Airflow** : Orchestration des workflows de données et d'entraînement des modèles
- **Tekton** : Pipeline CI/CD pour la construction, le test et le déploiement des modèles
- **Kubernetes** : Exécution des charges de travail conteneurisées
- **Trino/Starburst** : Requêtage fédéré des données
- **MLflow** : Suivi des expériences et gestion des modèles

## Prérequis

- Kubernetes 1.28+
- Tekton Pipelines 0.56.0+ (API `tekton.dev/v1`)
- Airflow 3.0+
- Python 3.12+
- Helm 3.0+
- kubectl configuré avec accès au cluster

## Installation

### 1. Configuration de l'environnement

```bash
# Cloner le dépôt
git clone [URL_DU_REPO]
cd ml-airflow-tekton

# Créer un namespace dédié
kubectl create namespace ml-workloads
```

### 2. Installation des dépendances

```bash
# Installer Tekton
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Installer les tâches Tekton
kubectl apply -f tekton/tasks/

# Installer le pipeline Tekton
kubectl apply -f tekton/pipeline.yaml
```

### 3. Déploiement d'Airflow

```bash
# Ajouter le dépôt Helm d'Airflow
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Installer Airflow
helm install airflow apache-airflow/airflow -n airflow --create-namespace \
  --set executor=KubernetesExecutor \
  --set dags.gitSync.enabled=true \
  --set dags.gitSync.repo=https://github.com/votre-org/ml-airflow-tekton.git \
  --set dags.gitSync.branch=main
```

## Utilisation

### Exécution du pipeline de re-entraînement

Le pipeline de re-entraînement s'exécute automatiquement selon la planification définie dans le DAG (par défaut, tous les jours à 2h du matin).

Pour déclencher manuellement un re-entraînement :

```bash
# Lancer le DAG via l'interface web d'Airflow
# ou via la CLI :
kubectl exec -n airflow deploy/airflow-webserver -- airflow dags trigger ml_model_retraining
```

### Exécution du pipeline CI/CD Tekton

```bash
# Créer un PipelineRun
cat <<EOF | kubectl apply -f -
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: ml-pipeline-run-
spec:
  pipelineRef:
    name: ml-model-pipeline
  params:
    - name: git-repo
      value: https://github.com/votre-org/ml-airflow-tekton.git
    - name: git-revision
      value: main
    - name: model-name
      value: mon-modele
    - name: target-env
      value: staging
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 1Gi
EOF
```

## Structure du Projet

```
.
├── airflow/                    # Configuration et DAGs Airflow
│   ├── config/                # Fichiers de configuration
│   └── dags/                  # DAGs Airflow
│       └── utils/             # Utilitaires partagés
├── infrastructure/            # Infrastructure as Code
│   ├── helm-charts/          # Charts Helm personnalisés
│   └── terraform/            # Configuration Terraform
├── model-code/                # Code du modèle ML
│   ├── src/                  # Code source
│   │   ├── api/              # API de service
│   │   ├── data/             # Traitement des données
│   │   └── models/           # Définition des modèles
│   └── tests/                # Tests unitaires et d'intégration
└── tekton/                   # Pipelines CI/CD
    ├── tasks/                # Tâches Tekton
    ├── triggers/             # Déclencheurs d'événements
    └── pipeline.yaml         # Définition du pipeline principal
```

## Développement

### Configuration de l'environnement de développement

```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .\.venv\Scripts\activate

# Installer les dépendances (modèle + tests)
pip install -r model-code/requirements.txt

# Installer les hooks pre-commit (ruff, fin de fichier, yaml)
pip install pre-commit && pre-commit install
```

### Exécution des tests

```bash
# Script unique (venv + install + pytest)
./scripts/test.sh

# Ou directement avec pytest
pytest model-code/tests/
pytest model-code/tests/ -m unit       # filtrer par marqueur
```

### Linting et formatage

```bash
# Lint
ruff check .

# Formatage
ruff format .
```

## Déploiement

### Environnement de Staging

Le déploiement en staging est automatique après validation des tests.

### Environnement de Production

Le déploiement en production nécessite une approbation manuelle :

1. Créer une release GitHub
2. Déclencher le pipeline avec le paramètre `target-env=production`
3. Valider le déploiement via l'interface de monitoring

## Maintenance

### Surveillance

- **Airflow** : Tableau de bord disponible sur `http://airflow.example.com`
- **Prometheus/Grafana** : Métriques des applications
- **MLflow** : Suivi des expériences sur `http://mlflow.example.com`

### Journaux

```bash
# Voir les logs d'Airflow
kubectl logs -n airflow deploy/airflow-webserver

# Voir les logs des tâches Tekton
tkn pipelinerun logs -f
```

## 🧪 Tests

La suite de tests (61 tests) couvre l'API, le preprocessing, l'entraînement et les fonctions Airflow.

### Exécution

```bash
# Crée/réutilise le venv, installe les dépendances de test et lance pytest
./scripts/test.sh

# Avec couverture de code (rapport terminal + HTML)
./scripts/test.sh --cov

# Filtrer par marqueur pytest
./scripts/test.sh -m unit

# Nettoyer le venv et les caches
./scripts/test.sh --clean
```

La CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) exécute Ruff (lint + format) et la suite pytest à chaque push/PR.

### Documentation des tests

- **Guides détaillés** : voir le dossier [`docs/`](docs/) (`RUN_TESTS.md`, `TESTING_INSTRUCTIONS.md`, `QUICK_TEST_GUIDE.md`)
- **Documentation technique** : [`model-code/tests/README.md`](model-code/tests/README.md)

## 🔒 Sécurité

Des efforts importants ont été faits pour sécuriser ce projet :

- ✅ Variables d'environnement pour les credentials (`.env.example` fourni)
- ✅ `.gitignore` complet pour éviter les commits de secrets
- ✅ Guide de sécurité complet ([`SECURITY.md`](SECURITY.md))
- ✅ Checklist pré-production (Infrastructure, Airflow, MLflow, Tekton, API)

⚠️ **Important** : Consultez [`SECURITY.md`](SECURITY.md) avant le déploiement en production.

## 📝 Documentation

- [`README.md`](README.md) - Ce fichier (vue d'ensemble)
- [`SECURITY.md`](SECURITY.md) - Guide de sécurité complet
- [`docs/`](docs/) - Guides détaillés (installation Airflow, Makefile, dépannage Tekton, tests, etc.)
- [`model-code/tests/README.md`](model-code/tests/README.md) - Documentation technique des tests

## Contributions

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-nouvelle-fonctionnalite`)
3. **Exécutez les tests** (`./scripts/test.sh --cov`)
4. **Vérifiez la couverture** (≥ 80%)
5. Committez vos changements (`git commit -am 'Ajouter une nouvelle fonctionnalité'`)
6. Poussez vers la branche (`git push origin feature/ma-nouvelle-fonctionnalite`)
7. Créez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

<div align="center">
  <p>Développé avec ❤️ par l'équipe Data Science de CNaaS IT</p>
</div>
