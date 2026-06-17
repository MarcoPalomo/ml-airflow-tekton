# 🔧 Guide de Dépannage Tekton

## ❌ Problème: ImagePullBackOff pour TOUTES les Images Tekton

### Erreur
```
Warning  Failed     65s (x5 over 4m12s)   kubelet            Error: ErrImagePull
Failed to pull image "gcr.io/tekton-releases/...": Error response from daemon:
Get "https://gcr.io/v2/...": denied: Unauthenticated request.
Unauthenticated requests do not have permission "artifactregistry.repositories.downloadArtifacts"
```

### Cause Principale

**Google a changé sa politique GCR** - Les images Tekton dans GCR nécessitent maintenant une **authentification** pour être téléchargées.

Cela affecte:
- ❌ Tekton Pipelines Controller
- ❌ Tekton Pipelines Webhook
- ❌ Tekton Triggers Controller
- ❌ Tekton Triggers Webhook
- ❌ Tekton Dashboard
- ❌ Tous les composants Tekton

---

## ✅ Solutions Recommandées

### Solution 1: Utiliser un Autre Registry (RECOMMANDÉ)

Les images Tekton sont également disponibles sur **Docker Hub** et **Quay.io** sans authentification requise.

**À FAIRE**: Le projet devrait migrer vers Docker Hub ou créer un miroir local des images.

### Solution 2: Configurer l'Authentification GCR

Si vous devez utiliser GCR:

```bash
# 1. Créer un service account Google Cloud
# 2. Télécharger la clé JSON
# 3. Créer un secret Kubernetes
kubectl create secret docker-registry gcr-secret \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat key.json)" \
  -n tekton-pipelines

# 4. Patcher les ServiceAccounts
kubectl patch serviceaccount tekton-pipelines-controller \
  -n tekton-pipelines \
  -p '{"imagePullSecrets": [{"name": "gcr-secret"}]}'
```

### Solution 3: Utiliser une Version Plus Ancienne

Les versions plus anciennes de Tekton peuvent encore fonctionner sans authentification:

```makefile
# Dans le Makefile, changer:
TEKTON_PIPELINES_VERSION := v0.50.0  # Version plus ancienne
```

### Solution 4: Attendre et Réessayer

Parfois, l'erreur est temporaire. Réessayez dans quelques heures:

```bash
# Supprimer les pods en erreur
kubectl delete pods --all -n tekton-pipelines

# Kubernetes les recréera automatiquement
```

---

## ⚠️ STATUS ACTUEL

**Le Makefile ne peut PAS installer Tekton actuellement** à cause de ce problème GCR.

**Actions nécessaires**:
1. Le projet Tekton doit publier les images sur Docker Hub
2. OU vous devez configurer l'authentification GCR
3. OU utiliser une version plus ancienne de Tekton

---

### ❌ Solution Précédente (Ne Fonctionne Plus): Ignorer le Dashboard

**NOTE**: Ce n'est plus suffisant car TOUS les composants Tekton ont le même problème, pas seulement le Dashboard.
- ✅ Tekton Pipelines (installé)
- ✅ Tekton Triggers (installé)
- ❌ Tekton Dashboard (optionnel, UI seulement)

**Action**: Le Makefile a été mis à jour pour rendre le Dashboard optionnel.

```bash
# Vérifier que Pipelines et Triggers fonctionnent
kubectl get pods -n tekton-pipelines | grep -E "pipeline|trigger"

# Devrait afficher des pods Running comme:
# tekton-pipelines-controller-xxx    1/1   Running
# tekton-pipelines-webhook-xxx       1/1   Running
# tekton-triggers-controller-xxx     1/1   Running
```

Si ces pods sont en `Running`, **Tekton est fonctionnel** même sans Dashboard.

---

### ✅ Solution 2: Réessayer Plus Tard

Les limites de taux GCR se réinitialisent après un certain temps:

```bash
# Supprimer le pod en erreur
kubectl delete pod -n tekton-pipelines -l app.kubernetes.io/component=dashboard

# L'image sera re-téléchargée automatiquement
# Attendre 5-10 minutes et vérifier
kubectl get pods -n tekton-pipelines
```

---

### ✅ Solution 3: Utiliser un Mirror d'Images

Si GCR est bloqué, vous pouvez utiliser un mirror:

```bash
# Télécharger l'image localement
docker pull gcr.io/tekton-releases/github.com/tektoncd/dashboard/cmd/dashboard:v0.43.0

# La re-tagger vers votre registry privé
docker tag gcr.io/tekton-releases/github.com/tektoncd/dashboard/cmd/dashboard:v0.43.0 \
  your-registry.com/tekton-dashboard:v0.43.0

# Pousser vers votre registry
docker push your-registry.com/tekton-dashboard:v0.43.0

# Modifier le déploiement pour utiliser votre image
kubectl set image deployment/tekton-dashboard \
  tekton-dashboard=your-registry.com/tekton-dashboard:v0.43.0 \
  -n tekton-pipelines
```

---

### ✅ Solution 4: Désactiver Complètement le Dashboard

Si vous ne voulez pas du Dashboard:

```bash
# Supprimer le Dashboard
kubectl delete deployment tekton-dashboard -n tekton-pipelines
kubectl delete service tekton-dashboard -n tekton-pipelines

# Ou désinstaller complètement
kubectl delete -f https://storage.googleapis.com/tekton-releases/dashboard/previous/v0.43.0/release.yaml
```

Puis installer Tekton sans Dashboard:
```bash
# Le Makefile essaiera d'installer le Dashboard mais ignorera les erreurs
make install-tekton
```

---

## 🔍 Diagnostic

### Vérifier les Pods Tekton

```bash
kubectl get pods -n tekton-pipelines
```

**Sortie attendue** (Dashboard peut être en ImagePullBackOff):
```
NAME                                           READY   STATUS
tekton-pipelines-controller-xxx                1/1     Running
tekton-pipelines-webhook-xxx                   1/1     Running
tekton-triggers-controller-xxx                 1/1     Running
tekton-triggers-core-interceptors-xxx          1/1     Running
tekton-triggers-webhook-xxx                    1/1     Running
tekton-dashboard-xxx                           0/1     ImagePullBackOff  ⚠️ NON CRITIQUE
```

### Voir les Détails de l'Erreur

```bash
# Décrire le pod
kubectl describe pod -n tekton-pipelines -l app.kubernetes.io/component=dashboard

# Voir les événements
kubectl get events -n tekton-pipelines --sort-by='.lastTimestamp' | grep dashboard
```

### Tester Tekton Sans Dashboard

```bash
# Créer un simple pipeline de test
cat <<EOF | kubectl apply -f -
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: hello-pipeline
  namespace: tekton-pipelines
spec:
  tasks:
    - name: hello
      taskSpec:
        steps:
          - name: echo
            image: ubuntu
            script: |
              #!/bin/bash
              echo "Hello from Tekton!"
EOF

# Créer un PipelineRun
kubectl create -f - <<EOF
apiVersion: tekton.dev/v1beta1
kind:PipelineRun
metadata:
  name: hello-run
  namespace: tekton-pipelines
spec:
  pipelineRef:
    name: hello-pipeline
EOF

# Voir les logs
kubectl logs -n tekton-pipelines -l tekton.dev/pipelineRun=hello-run --tail=100
```

Si cette commande fonctionne, **Tekton est opérationnel** sans Dashboard!

---

## 🌐 Alternatives au Tekton Dashboard

Si vous avez besoin d'une UI:

### 1. **Tekton CLI (`tkn`)**

```bash
# Installer tkn
curl -LO https://github.com/tektoncd/cli/releases/download/v0.32.0/tkn_0.32.0_Linux_x86_64.tar.gz
tar xvzf tkn_0.32.0_Linux_x86_64.tar.gz
sudo mv tkn /usr/local/bin/

# Utiliser
tkn pipeline list
tkn pipelinerun list
tkn pipelinerun logs <run-name> -f
```

### 2. **Kubernetes Dashboard**

Installer le Dashboard Kubernetes général:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Port-forward
kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443

# Accéder: https://localhost:8443
```

### 3. **kubectl avec watch**

```bash
# Surveiller les PipelineRuns
watch kubectl get pipelineruns -A

# Voir les logs en temps réel
kubectl logs -f -n <namespace> <pod-name>
```

---

## 📊 Vérification Post-Installation

### Checklist Tekton Fonctionnel (Sans Dashboard)

- [x] tekton-pipelines-controller en Running
- [x] tekton-pipelines-webhook en Running
- [x] tekton-triggers-controller en Running
- [ ] tekton-dashboard en Running (OPTIONNEL)

**Si les 3 premiers sont OK, Tekton fonctionne!**

---

## 🔄 Réinstaller Proprement

Si vous voulez tout recommencer:

```bash
# Désinstaller complètement
make uninstall-tekton

# Attendre quelques secondes
sleep 5

# Réinstaller
make install-tekton
```

---

## 💡 Recommandations

1. **Ne pas bloquer** sur le Dashboard - il n'est pas critique
2. **Utiliser `tkn` CLI** pour l'interface en ligne de commande
3. **Vérifier les 3 pods essentiels** (controller, webhook, triggers)
4. **Tester avec un pipeline simple** pour valider le fonctionnement

---

## 📚 Ressources

- **Documentation Tekton**: https://tekton.dev/docs/
- **Tekton CLI**: https://github.com/tektoncd/cli
- **Exemples de Pipelines**: https://github.com/tektoncd/catalog
- **Dashboard Repository**: https://github.com/tektoncd/dashboard

---

**Important**: Le Makefile a été mis à jour pour que le Dashboard soit optionnel. L'installation de Tekton réussira même si le Dashboard échoue.

**Date**: 2026-01-06
