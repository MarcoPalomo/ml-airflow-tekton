# 🚀 Guide d'Utilisation du Makefile - Infrastructure MLOps

Ce guide explique comment utiliser le Makefile pour déployer et gérer l'infrastructure MLOps sur Kubernetes.

---

## 📋 Prérequis

### Outils Requis

- **kubectl** : CLI Kubernetes
- **helm** : Gestionnaire de packages Kubernetes (v3+)
- **make** : Outil de build

Vérifier l'installation :
```bash
kubectl version --client
helm version
make --version
```

### Connexion au Cluster

Assurez-vous d'être connecté à votre cluster Kubernetes :
```bash
kubectl cluster-info
kubectl get nodes
```

### Variables d'Environnement

Définir les variables requises :
```bash
export AWS_ACCESS_KEY_ID="votre_access_key"
export AWS_SECRET_ACCESS_KEY="votre_secret_key"
export AWS_DEFAULT_REGION="eu-west-1"
export MLFLOW_ADMIN_PASSWORD="password_securise"
```

Ou créer un fichier `.env` :
```bash
# Copier le template
cp .env.example .env

# Éditer avec vos vraies valeurs
vim .env

# Charger les variables
source .env
```

---

## 🎯 Installation Complète (Recommandé)

### Une Seule Commande

```bash
make install-all
```

Cette commande va :
1. ✅ Vérifier les dépendances (helm, kubectl)
2. ✅ Vérifier la connexion au cluster
3. ✅ Valider la configuration
4. ✅ Créer les namespaces
5. ✅ Mettre à jour les dépendances Helm
6. ✅ Installer Tekton (CI/CD)
7. ✅ Installer MLflow (tracking)
8. ✅ Installer Starburst (query engine)
9. ✅ Installer Airflow (orchestration)

**Durée estimée** : 15-20 minutes

---

## 🔧 Installation Sélective

### Installer un Seul Composant

```bash
# Tekton seulement
make install-tekton

# MLflow seulement
make install-mlflow

# Starburst seulement
make install-starburst

# Airflow seulement
make install-airflow
```

### Installation Progressive

```bash
# 1. Vérifications préalables
make check-deps
make check-cluster
make validate-config

# 2. Préparer l'infrastructure
make create-namespaces
make add-repos
make update-deps

# 3. Installer composant par composant
make install-tekton
make install-mlflow
make install-starburst
make install-airflow
```

---

## 📊 Monitoring et Status

### Vérifier l'État Général

```bash
make status
```

**Sortie** :
```
═══════════════════════════════════════════════════════
  État des Déploiements
═══════════════════════════════════════════════════════

[Tekton - tekton-pipelines]
NAME                                     READY   STATUS
tekton-pipelines-controller-xxx          1/1     Running
tekton-pipelines-webhook-xxx             1/1     Running

[MLflow - mlflow]
NAME                      READY   STATUS
mlflow-server-xxx         1/1     Running
mlflow-postgresql-xxx     1/1     Running

[Starburst - starburst]
NAME                           READY   STATUS
starburst-coordinator-xxx      1/1     Running
starburst-worker-xxx          2/2     Running

[Airflow - airflow]
NAME                           READY   STATUS
airflow-webserver-xxx          1/1     Running
airflow-scheduler-xxx          1/1     Running
```

### Tester les Déploiements

```bash
make test-deployment
```

**Sortie** :
```
▶ Test des déploiements...
  Testing Tekton...
  ✓ Tekton OK
  Testing MLflow...
  ✓ MLflow OK
  Testing Starburst...
  ✓ Starburst OK
  Testing Airflow...
  ✓ Airflow OK
```

---

## 📝 Logs

### Voir les Logs en Temps Réel

```bash
# Logs Tekton
make logs COMPONENT=tekton

# Logs MLflow
make logs COMPONENT=mlflow

# Logs Starburst
make logs COMPONENT=starburst

# Logs Airflow
make logs COMPONENT=airflow
```

**Raccourci** : Utiliser `Ctrl+C` pour arrêter

---

## 🌐 Accès aux Services

### Port Forwarding

#### MLflow (localhost:5000)

```bash
make port-forward-mlflow
```

Accéder à : http://localhost:5000

#### Airflow (localhost:8080)

```bash
make port-forward-airflow
```

Accéder à : http://localhost:8080

#### Tekton Dashboard (localhost:9097)

```bash
make port-forward-tekton
```

Accéder à : http://localhost:9097

#### Starburst (localhost:8080)

```bash
make port-forward-starburst
```

Accéder à : http://localhost:8080

### Credentials par Défaut

**MLflow** :
- Username : `admin`
- Password : `$MLFLOW_ADMIN_PASSWORD`

**Airflow** :
- Username : `admin`
- Password : Récupérer avec :
  ```bash
  kubectl get secret airflow-webserver-secret -n airflow -o jsonpath='{.data.webserver-secret-key}' | base64 -d
  ```

---

## 🗑️ Désinstallation

### Tout Désinstaller

```bash
make uninstall-all
```

**Attention** : Supprime tous les composants ET les données !

### Désinstallation Sélective

```bash
# Désinstaller un seul composant
make uninstall-tekton
make uninstall-mlflow
make uninstall-starburst
make uninstall-airflow
```

### Nettoyer les Ressources Orphelines

```bash
make clean
```

Supprime :
- Pods en état `Failed`
- Pods en état `Succeeded`

---

## ⏱️ Attendre qu'Airflow soit Prêt

Airflow peut prendre 15-20 minutes pour s'initialiser complètement. Utilisez cette commande pour attendre:

```bash
make wait-airflow
```

Cette commande attend que:
- Le webserver soit prêt (UI)
- Le scheduler soit prêt (orchestration)

**Note**: L'installation d'Airflow est maintenant non-bloquante. Vous pouvez continuer avec d'autres tâches pendant l'initialisation.

---

## 🛠️ Utilitaires

### Vérifier les Dépendances

```bash
make check-deps
```

### Valider la Configuration

```bash
make validate-config
```

### Ajouter les Repositories Helm

```bash
make add-repos
```

### Mettre à Jour les Dépendances

```bash
make update-deps
```

---

## 📖 Workflow Complet

### Déploiement Initial

```bash
# 1. Configurer les variables d'environnement
source .env

# 2. Vérifier les prérequis
make check-deps
make check-cluster

# 3. Installer tout
make install-all

# 4. Vérifier le déploiement
make status
make test-deployment

# 5. Accéder aux services
make port-forward-mlflow  # Dans un terminal
make port-forward-airflow  # Dans un autre terminal
```

### Mise à Jour

```bash
# Mettre à jour les charts Helm
make update-deps

# Réinstaller (upgrade)
make install-all
```

### Debugging

```bash
# 1. Vérifier l'état
make status

# 2. Tester les déploiements
make test-deployment

# 3. Voir les logs du composant problématique
make logs COMPONENT=mlflow

# 4. Inspecter avec kubectl
kubectl describe pod <pod-name> -n mlflow
kubectl get events -n mlflow --sort-by='.lastTimestamp'
```

---

## ⚙️ Configuration Avancée

### Personnaliser les Namespaces

Modifier dans le Makefile :
```makefile
NAMESPACE_TEKTON := mon-tekton
NAMESPACE_MLFLOW := mon-mlflow
NAMESPACE_STARBURST := mon-starburst
NAMESPACE_AIRFLOW := mon-airflow
```

### Personnaliser les Charts Helm

Modifier les fichiers values :
- `infrastructure/helm-charts/tekton/values.yaml`
- `infrastructure/helm-charts/mlflow/values.yaml`
- `infrastructure/helm-charts/starburst/values.yaml`

### Passer des Valeurs Custom

```bash
# Exemple pour MLflow
make install-mlflow \
  AWS_ACCESS_KEY_ID=xxx \
  AWS_SECRET_ACCESS_KEY=yyy \
  MLFLOW_ADMIN_PASSWORD=zzz
```

---

## 🐛 Troubleshooting

### Erreur : "Helm n'est pas installé"

```bash
# Installer Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Erreur : "kubectl n'est pas installé"

```bash
# Ubuntu/Debian
sudo apt install kubectl

# macOS
brew install kubectl
```

### Erreur : "Impossible de se connecter au cluster"

```bash
# Vérifier le contexte
kubectl config current-context

# Lister les contextes
kubectl config get-contexts

# Changer de contexte
kubectl config use-context <context-name>
```

### Pods en état "CrashLoopBackOff"

```bash
# Voir les logs
make logs COMPONENT=mlflow

# Décrire le pod
kubectl describe pod <pod-name> -n mlflow

# Vérifier les events
kubectl get events -n mlflow
```

### Timeout pendant l'installation d'Airflow

**Erreur**: `Error: context deadline exceeded` lors de `make install-airflow`

**Cause**: Airflow est très lourd et prend 15-20 minutes pour s'initialiser

**Solution**: Le Makefile a été mis à jour avec un timeout de 20 minutes et une installation non-bloquante

```bash
# Installer Airflow (non-bloquant)
make install-airflow

# Vérifier l'état pendant l'installation
kubectl get pods -n airflow -w

# Attendre que tout soit prêt
make wait-airflow
```

**Guide complet**: Voir [AIRFLOW_INSTALL_GUIDE.md](AIRFLOW_INSTALL_GUIDE.md)

### Timeout pendant l'installation (autres composants)

```bash
# Augmenter le timeout dans le Makefile
--timeout 10m  # Changer à 15m ou 20m
```

### Erreur de variables d'environnement

```bash
# Vérifier qu'elles sont définies
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $MLFLOW_ADMIN_PASSWORD

# Les définir si nécessaire
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="yyy"
export MLFLOW_ADMIN_PASSWORD="zzz"
```

---

## 📚 Références

### Commandes Make Disponibles

```bash
# Afficher l'aide
make help

# ou simplement
make
```

### Documentation des Composants

- **Tekton** : https://tekton.dev/docs/
- **MLflow** : https://mlflow.org/docs/latest/
- **Starburst** : https://docs.starburst.io/
- **Airflow** : https://airflow.apache.org/docs/

### Notes d'Installation

**Tekton** : Installé via manifests YAML officiels (pas de Helm chart)
- Tekton Pipelines v0.56.0
- Tekton Triggers v0.25.0
- Tekton Dashboard v0.43.0

**Autres composants** : Installés via Helm charts
- MLflow : community-charts/mlflow
- Starburst : starburstdata/starburst
- Airflow : apache-airflow/airflow

### Fichiers Importants

| Fichier | Description |
|---------|-------------|
| `Makefile` | Fichier principal avec toutes les commandes |
| `.env.example` | Template des variables d'environnement |
| `infrastructure/helm-charts/` | Charts Helm personnalisés |
| `SECURITY.md` | Guide de sécurité |

---

## ✅ Checklist Post-Installation

- [ ] Tous les pods sont en état `Running` (`make status`)
- [ ] Test de déploiement réussi (`make test-deployment`)
- [ ] Accès MLflow via port-forward
- [ ] Accès Airflow via port-forward
- [ ] Accès Tekton Dashboard via port-forward
- [ ] Variables d'environnement configurées
- [ ] Secrets Kubernetes créés si nécessaire
- [ ] Documentation de sécurité lue ([SECURITY.md](SECURITY.md))

---

**Dernière mise à jour** : 2026-01-06
**Version** : 2.0.0
