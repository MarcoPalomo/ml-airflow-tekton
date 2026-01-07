# Guide de Sécurité - ML Airflow Tekton

## 🔒 Vue d'ensemble

Ce document décrit les bonnes pratiques de sécurité pour le déploiement et l'exploitation de la plateforme ML Airflow Tekton en production.

---

## ⚠️ Issues Critiques à Résoudre Avant Production

### 1. Gestion des Secrets

**Problème actuel**: Credentials hardcodées dans le code source

**Solutions recommandées**:

#### Option A: Kubernetes Secrets (Recommandé pour Kubernetes)

```bash
# Créer un secret pour Airflow
kubectl create secret generic airflow-secrets \
  --from-literal=aws-access-key-id='YOUR_KEY' \
  --from-literal=aws-secret-access-key='YOUR_SECRET' \
  --from-literal=trino-password='YOUR_PASSWORD' \
  -n airflow

# Créer un secret pour MLflow
kubectl create secret generic mlflow-secrets \
  --from-literal=postgres-password='YOUR_PASSWORD' \
  --from-literal=s3-access-key='YOUR_KEY' \
  -n mlflow
```

Référencer dans vos pods:
```yaml
env:
  - name: AWS_ACCESS_KEY_ID
    valueFrom:
      secretKeyRef:
        name: airflow-secrets
        key: aws-access-key-id
```

#### Option B: HashiCorp Vault (Recommandé pour Enterprise)

Configuration Airflow:
```ini
[secrets]
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {
  "url": "https://vault.example.com:8200",
  "token": "vault-token",
  "mount_point": "airflow",
  "connections_path": "connections",
  "variables_path": "variables"
}
```

#### Option C: AWS Secrets Manager

```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='eu-west-1')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise e
```

#### Option D: Variables d'environnement (Minimum viable)

```bash
# Dans votre système de déploiement
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="yyy"
export TRINO_PASSWORD="zzz"
```

**Action requise**: Choisir et implémenter une des options ci-dessus avant le déploiement en production.

---

### 2. Connexions Airflow

**⚠️ NE PAS** définir les connexions dans le code Python. Utiliser plutôt:

#### Via Airflow CLI:
```bash
airflow connections add 'starburst_trino' \
  --conn-type 'trino' \
  --conn-host 'starburst-coordinator.cluster.local' \
  --conn-port 8080 \
  --conn-login 'airflow-user' \
  --conn-password "${TRINO_PASSWORD}" \
  --conn-schema 'lakehouse'
```

#### Via Airflow UI:
1. Aller dans **Admin > Connections**
2. Cliquer sur **+** pour ajouter une connexion
3. Remplir les champs
4. Cliquer sur **Save**

#### Via variable d'environnement:
```bash
export AIRFLOW_CONN_STARBURST_TRINO='trino://user:password@host:8080/lakehouse'
```

---

### 3. Configuration Starburst/Trino

**Problème**: HTTP non-sécurisé activé dans [infrastructure/helm-charts/starburst/values.yaml:102](infrastructure/helm-charts/starburst/values.yaml#L102)

```yaml
# ❌ NE PAS utiliser en production
password.authentication.allow-insecure-http: "true"

# ✅ Utiliser à la place
password.authentication.allow-insecure-http: "false"
http-server.authentication.type: PASSWORD
http-server.https.enabled: true
http-server.https.port: 8443
http-server.https.keystore.path: /path/to/keystore.jks
http-server.https.keystore.key: keystore_password
```

**Action requise**:
1. Générer un certificat SSL/TLS
2. Configurer HTTPS
3. Désactiver HTTP non-sécurisé

---

### 4. API FastAPI - Authentification

**Problème**: Aucune authentification sur les endpoints de prédiction

**Solution**: Implémenter l'authentification JWT

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os

security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, user=Depends(verify_token)):
    # Votre code de prédiction...
    pass
```

**Dépendances à ajouter**:
```txt
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

---

## 🛡️ Checklist de Sécurité Pré-Production

### Infrastructure

- [ ] Tous les secrets sont stockés dans un gestionnaire de secrets (Vault, K8s Secrets, etc.)
- [ ] Aucune credential hardcodée dans le code ou les fichiers de configuration
- [ ] `.env` est bien dans `.gitignore`
- [ ] HTTPS/TLS activé pour tous les services exposés
- [ ] Certificats SSL valides et non auto-signés
- [ ] Network policies Kubernetes configurées
- [ ] RBAC Kubernetes configuré avec principe du moindre privilège
- [ ] Namespaces séparés pour dev/staging/prod
- [ ] Resource limits et requests définis pour tous les pods
- [ ] Pod Security Policies (PSP) ou Pod Security Standards (PSS) activés

### Airflow

- [ ] Authentification activée sur l'UI Airflow
- [ ] RBAC Airflow configuré
- [ ] Connexions stockées dans un secrets backend
- [ ] Variables sensibles chiffrées avec Fernet
- [ ] Logs ne contiennent pas de secrets
- [ ] KubernetesExecutor utilisé (pas LocalExecutor en prod)
- [ ] Webserver derrière un reverse proxy (nginx/traefik)
- [ ] Rate limiting configuré

### MLflow

- [ ] Authentification activée (Basic Auth minimum)
- [ ] PostgreSQL backend avec SSL
- [ ] Artifacts stockés sur S3 avec encryption at rest
- [ ] Credentials S3 via IAM Roles (pas access keys)
- [ ] UI MLflow derrière authentification
- [ ] Backup régulier de la base de données

### Tekton

- [ ] Service accounts avec permissions minimales
- [ ] Image pull secrets configurés pour registry privée
- [ ] Pas d'images avec tag `latest` en production
- [ ] Scan de vulnérabilités des images Docker
- [ ] Secrets injectés via Kubernetes Secrets
- [ ] Webhooks sécurisés avec secrets

### API Model

- [ ] Authentification JWT implémentée
- [ ] Rate limiting configuré
- [ ] CORS configuré proprement
- [ ] Validation des inputs (Pydantic)
- [ ] Logging des requêtes (sans données sensibles)
- [ ] Health checks configurés
- [ ] Timeout configurés
- [ ] Monitoring et alerting activés

### Base de données

- [ ] Connexions SSL/TLS uniquement
- [ ] Passwords forts et rotatés régulièrement
- [ ] Backups automatiques configurés
- [ ] Principe du moindre privilège pour les utilisateurs DB
- [ ] Encryption at rest activée
- [ ] Logs d'audit activés

### Réseau

- [ ] Segmentation réseau (VPC/subnets)
- [ ] Security groups restrictifs
- [ ] Pas d'exposition publique des bases de données
- [ ] Firewall configuré
- [ ] VPN ou bastion host pour accès admin
- [ ] DDoS protection activée

---

## 🔐 Rotation des Secrets

### Fréquence Recommandée

- **Passwords humains**: Tous les 90 jours
- **API keys**: Tous les 180 jours
- **Service account tokens**: Tous les 365 jours
- **Certificats SSL**: Avant expiration (automation recommandée)

### Procédure de Rotation

1. **Créer le nouveau secret**
   ```bash
   kubectl create secret generic airflow-secrets-v2 \
     --from-literal=aws-access-key-id='NEW_KEY' \
     -n airflow
   ```

2. **Mettre à jour les références**
   ```bash
   kubectl set env deployment/airflow-webserver \
     --from=secret/airflow-secrets-v2 \
     -n airflow
   ```

3. **Vérifier le fonctionnement**
   ```bash
   kubectl rollout status deployment/airflow-webserver -n airflow
   ```

4. **Supprimer l'ancien secret**
   ```bash
   kubectl delete secret airflow-secrets -n airflow
   ```

---

## 📊 Monitoring de Sécurité

### Alertes Recommandées

1. **Échecs d'authentification répétés**
   ```promql
   rate(http_requests_total{status="401"}[5m]) > 10
   ```

2. **Accès non autorisés**
   ```promql
   rate(http_requests_total{status="403"}[5m]) > 5
   ```

3. **Certificats expirant bientôt**
   ```promql
   (ssl_certificate_expiry_seconds - time()) / 86400 < 30
   ```

4. **Pods redémarrant fréquemment**
   ```promql
   rate(kube_pod_container_status_restarts_total[1h]) > 5
   ```

### Logs à Surveiller

- Tentatives de connexion échouées
- Modifications de configuration
- Accès aux secrets
- Erreurs d'autorisation
- Changements de rôles/permissions

---

## 🚨 Réponse aux Incidents

### En cas de compromission de credentials:

1. **Révoquer immédiatement** les credentials compromises
2. **Auditer les logs** pour identifier l'étendue de l'accès
3. **Créer de nouvelles credentials** et les déployer
4. **Analyser** comment la compromission s'est produite
5. **Documenter** l'incident et les actions correctrices
6. **Mettre à jour** les procédures de sécurité

### Contacts

- **Security Team**: security@example.com
- **On-call Engineer**: oncall@example.com
- **Incident Hotline**: +1-XXX-XXX-XXXX

---

## 📚 Ressources Additionnelles

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [Airflow Security](https://airflow.apache.org/docs/apache-airflow/stable/security/)
- [MLflow Security](https://mlflow.org/docs/latest/auth/index.html)
- [Tekton Security](https://tekton.dev/docs/pipelines/install/#customizing-the-pipelines-controller-behavior)

---

## 📝 Changelog de Sécurité

| Date | Action | Responsable |
|------|--------|-------------|
| 2026-01-05 | Création du document | Claude |
| TBD | Implémentation secrets manager | TBD |
| TBD | Configuration HTTPS Starburst | TBD |
| TBD | Ajout authentification API | TBD |

---

**Dernière mise à jour**: 2026-01-05
**Version**: 1.0.0
**Propriétaire**: ML Platform Team
