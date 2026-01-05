# Infrastructure Terraform pour ML Pipeline

Ce dépôt contient les modules Terraform pour déployer une infrastructure de pipeline ML sur OpenStack avec MinIO pour le stockage d'objets.

## Modules

### 1. Module Network

Gère les ressources réseau dans OpenStack :
- Création d'un réseau virtuel et d'un sous-réseau
- Configuration d'un routeur avec connexion au réseau externe
- Groupes de sécurité avec règles pour SSH, accès interne et Kubernetes

**Variables d'entrée :**
- `environment` : Environnement de déploiement (dev, staging, prod)
- `network_cidr` : Plage CIDR pour le réseau (défaut: 10.0.0.0/24)
- `external_network_id` : ID du réseau externe OpenStack
- `dns_servers` : Liste des serveurs DNS (défaut: [8.8.8.8, 8.8.4.4])
- `admin_cidr` : Plage CIDR pour l'accès administratif (défaut: 0.0.0.0/0)

### 2. Module Storage (MinIO)

Configure un bucket MinIO pour le stockage des données ML :
- Création d'un bucket avec versionnement
- Configuration des politiques d'accès IAM
- Création d'un compte de service pour l'application

**Variables d'entrée :**
- `minio_endpoint` : URL du point de terminaison MinIO
- `minio_access_key` : Clé d'accès pour l'API MinIO
- `minio_secret_key` : Clé secrète pour l'API MinIO
- `ml_bucket_name` : Nom du bucket pour le stockage ML (défaut: ml-pipeline-bucket)
- `enable_versioning` : Activer le versionnement des objets (défaut: true)

### 3. Module Database (PostgreSQL)

Déploie une instance PostgreSQL sur OpenStack :
- Création d'une instance de calcul avec installation automatique de PostgreSQL
- Configuration des groupes de sécurité pour l'accès à la base de données
- Gestion des volumes de stockage

**Variables d'entrée :**
- `postgres_version` : Version de PostgreSQL à installer
- `db_name` : Nom de la base de données
- `db_user` : Nom d'utilisateur de la base de données
- `db_password` : Mot de passe de l'utilisateur de la base de données
- `volume_size` : Taille du volume en Go (défaut: 50)
- `allowed_cidrs` : Liste des plages CIDR autorisées à se connecter

### 4. Module Monitoring

Déploie une stack de monitoring avec :
- Prometheus pour la collecte de métriques
- Grafana pour la visualisation
- AlertManager pour les alertes

**Variables d'entrée :**
- `namespace` : Namespace Kubernetes pour les déploiements
- `storage_class` : Classe de stockage pour les volumes persistants
- `grafana_admin_password` : Mot de passe administrateur pour Grafana
- `prometheus_storage_size` : Taille du stockage pour Prometheus (défaut: 50Gi)
- `grafana_storage_size` : Taille du stockage pour Grafana (défaut: 10Gi)

## Utilisation

1. Initialiser Terraform :
   ```bash
   terraform init
   ```

2. Créer un fichier de variables (par exemple, `terraform.tfvars`) avec vos paramètres.

3. Vérifier le plan d'exécution :
   ```bash
   terraform plan
   ```

4. Appliquer les changements :
   ```bash
   terraform apply
   ```

## Sécurité

- Les identifiants sensibles (mots de passe, clés d'API) doivent être fournis via des variables d'environnement ou un gestionnaire de secrets
- Les règles de sécurité réseau sont configurées pour n'autoriser que les connexions nécessaires
- Les volumes de stockage sont chiffrés et sauvegardés selon les bonnes pratiques

## Maintenance

- Pour mettre à jour les modules, utilisez `terraform get -update`
- Sauvegardez régulièrement l'état Terraform dans un backend sécurisé
- Consultez les journaux des ressources OpenStack pour le dépannage

## Licence

MIT

