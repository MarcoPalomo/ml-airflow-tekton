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

- Kubernetes 1.20+
- Tekton Pipelines 0.30.0+
- Airflow 2.3.0+
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
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  generateName: ml-pipeline-run-
spec:
  pipelineRef:
    name: ml-model-pipeline
  params:
    - name: git-repo
      value: https://github.com/votre-org/ml-airflow-tekton.git
    - name: model-name
      value: mon-modele
    - name: target-env
      value: staging
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
python -m venv venv
source venv/bin/activate  # Sur Windows: .\venv\Scripts\activate

# Installer les dépendances de développement
pip install -r requirements-dev.txt
```

### Exécution des tests

```bash
# Exécuter les tests unitaires
pytest model-code/tests/unit

# Exécuter les tests d'intégration
pytest model-code/tests/integration
```

### Linting et formatage

```bash
# Vérifier le style de code
flake8 model-code/

# Formater le code
black model-code/
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

Le projet dispose d'une suite de tests complète avec plus de 140 tests couvrant tous les modules.

### Exécution Rapide

```bash
# Premier lancement (setup complet)
./setup_and_test.sh

# Lancements suivants (rapide)
./quick_test.sh

# Avec couverture de code
./setup_and_test.sh --coverage
```

### Statistiques des Tests

- **Total** : 140+ tests
- **Couverture** : ~85%
- **Temps d'exécution** : ~30 secondes

### Documentation

- **Guide simple** : [`RUN_TESTS.md`](RUN_TESTS.md)
- **Guide complet** : [`TESTING_INSTRUCTIONS.md`](TESTING_INSTRUCTIONS.md)
- **Aide-mémoire** : [`QUICK_TEST_GUIDE.md`](QUICK_TEST_GUIDE.md)

## 🔒 Sécurité

Des efforts importants ont été faits pour sécuriser ce projet :

- ✅ Variables d'environnement pour les credentials (`.env.example` fourni)
- ✅ `.gitignore` complet pour éviter les commits de secrets
- ✅ Guide de sécurité complet ([`SECURITY.md`](SECURITY.md))
- ✅ Checklist pré-production (Infrastructure, Airflow, MLflow, Tekton, API)

⚠️ **Important** : Consultez [`SECURITY.md`](SECURITY.md) avant le déploiement en production.

## 📝 Documentation

- [`README.md`](README.md) - Ce fichier (vue d'ensemble)
- [`CORRECTIONS.md`](CORRECTIONS.md) - Rapport détaillé des corrections effectuées
- [`SECURITY.md`](SECURITY.md) - Guide de sécurité complet (400+ lignes)
- [`RUN_TESTS.md`](RUN_TESTS.md) - Comment exécuter les tests
- [`model-code/tests/README.md`](model-code/tests/README.md) - Documentation technique des tests

## Contributions

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-nouvelle-fonctionnalite`)
3. **Exécutez les tests** (`./setup_and_test.sh --coverage`)
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
