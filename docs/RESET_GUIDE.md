# 🔄 Guide de Reset Complet de l'Environnement Python

Si vous rencontrez des problèmes avec pip ou des conflits de dépendances, ce guide vous permet de tout nettoyer et repartir de zéro.

---

## 🎯 Procédure Complète en 2 Étapes

### Étape 1 : Nettoyer Complètement

```bash
./clean_and_reset.sh
```

Ce script va :
- ✅ Supprimer l'ancien environnement virtuel
- ✅ Nettoyer tous les caches Python (`__pycache__`, `.pyc`, etc.)
- ✅ Créer un nouvel environnement virtuel propre
- ✅ Mettre à jour pip, setuptools, wheel

**Durée** : 10-20 secondes

---

### Étape 2 : Installer et Tester

**Option A : Tests basiques** (recommandé après reset)

```bash
./test_basic.sh
```

Installe uniquement 7 packages essentiels et teste juste le preprocessing.

**Option B : Installation minimale complète**

```bash
./minimal_test.sh
```

Installe plus de packages et teste tous les modules de base.

---

## 📋 Procédure Détaillée

### 1. Reset Complet

```bash
cd /home/lpmb45/Documents/data/ML/ml-airflow-tekton
./clean_and_reset.sh
```

**Sortie attendue :**
```
════════════════════════════════════════
  Nettoyage Complet Environnement Python
════════════════════════════════════════

▶ Suppression de l'ancien environnement virtuel...
✓ Ancien environnement supprimé
▶ Nettoyage des caches Python...
✓ Caches nettoyés
▶ Vérification de Python...
✓ Python 3.12.0 trouvé
▶ Création d'un nouvel environnement virtuel...
✓ Nouvel environnement créé
▶ Activation de l'environnement...
✓ Environnement activé
▶ Mise à jour de pip, setuptools, wheel...
✓ Outils de base mis à jour

════════════════════════════════════════
  Environnement Nettoyé et Réinitialisé !
════════════════════════════════════════
```

---

### 2. Tests Basiques

```bash
./test_basic.sh
```

**Ce qui sera installé :**
- numpy
- pandas
- scikit-learn
- joblib
- pytest
- pytest-cov
- pytest-mock

**Ce qui sera testé :**
- Seulement `test_preprocessing.py` (35 tests)

**Sortie attendue :**
```
═══════════════════════════════════════════
  Tests Basiques (Installation Ultra-Minimale)
═══════════════════════════════════════════

▶ Installation des packages de base...
  Installing numpy... ✓
  Installing pandas... ✓
  Installing scikit-learn... ✓
  Installing joblib... ✓
  Installing pytest... ✓
  Installing pytest-cov... ✓
  Installing pytest-mock... ✓

✓ Installation terminée

▶ Exécution des tests de preprocessing...

test_preprocessing.py::TestDataPreprocessor::test_init PASSED
test_preprocessing.py::TestDataPreprocessor::test_load_data_csv PASSED
...

╔═══════════════════════════════════════╗
║                                       ║
║     TESTS DE BASE RÉUSSIS ✓          ║
║                                       ║
╚═══════════════════════════════════════╝
```

---

## 🔧 Installation Manuelle (Alternative)

Si vous préférez contrôler manuellement :

### Nettoyer

```bash
# Supprimer venv
rm -rf venv

# Nettoyer caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
```

### Recréer

```bash
# Créer venv propre
python3 -m venv venv --clear

# Activer
source venv/bin/activate

# Mettre à jour pip
python -m pip install --upgrade pip setuptools wheel
```

### Installer Minimum

```bash
# Juste ce qu'il faut pour les tests
pip install numpy pandas scikit-learn joblib
pip install pytest pytest-cov pytest-mock
```

### Tester

```bash
cd model-code/
pytest tests/test_preprocessing.py -v
```

---

## 🆘 Problèmes Persistants ?

### Si Python 3 n'est pas trouvé

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip

# Vérifier
python3 --version
```

### Si `venv` échoue

```bash
# Installer le module venv
sudo apt install python3-venv python3-full
```

### Si pip est complètement cassé

```bash
# Réinstaller pip
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
```

### Problème de permissions

```bash
# S'assurer des bonnes permissions
chmod +x clean_and_reset.sh
chmod +x test_basic.sh
chmod +x minimal_test.sh
```

---

## 📊 Comparaison des Scripts

| Script | Nettoyage | Installation | Tests | Durée | Recommandé |
|--------|-----------|--------------|-------|-------|------------|
| `clean_and_reset.sh` | ✅ Complet | ❌ Non | ❌ Non | 20s | 1ère étape |
| `test_basic.sh` | ❌ Non | ✅ 7 packages | ✅ preprocessing | 2min | Après reset |
| `minimal_test.sh` | ❌ Non | ✅ 15 packages | ✅ Tous | 3min | Si test_basic OK |
| `setup_and_test.sh` | ❌ Non | ✅ Tous | ✅ Tous | 5min+ | Si vous voulez tout |

---

## 🎯 Workflow Recommandé

```bash
# 1. Nettoyer complètement
./clean_and_reset.sh

# 2. Tester avec le minimum
./test_basic.sh

# 3. Si OK, installer plus
./minimal_test.sh

# 4. Optionnel : tout installer
./setup_and_test.sh
```

---

## ✅ Vérifications

### Vérifier que venv est propre

```bash
source venv/bin/activate
pip list
```

Devrait montrer uniquement :
- pip
- setuptools
- wheel

### Vérifier Python

```bash
which python
# Devrait afficher: /path/to/ml-airflow-tekton/venv/bin/python

python --version
# Devrait afficher: Python 3.x.x
```

### Vérifier pip

```bash
pip --version
# Devrait afficher la version de pip dans venv

pip check
# Ne devrait montrer aucun conflit
```

---

## 📝 Ce Que Font les Scripts

### `clean_and_reset.sh`

```bash
1. rm -rf venv                    # Supprimer ancien venv
2. find . -name "__pycache__"     # Nettoyer caches
3. python3 -m venv venv --clear   # Créer nouveau venv
4. pip install --upgrade pip      # Mettre à jour pip
```

### `test_basic.sh`

```bash
1. source venv/bin/activate       # Activer venv
2. pip install numpy pandas ...   # 7 packages essentiels
3. pytest test_preprocessing.py   # Tests de base
```

### `minimal_test.sh`

```bash
1. source venv/bin/activate       # Activer venv
2. pip install [15 packages]      # Dépendances minimales
3. pytest tests/ -v               # Tous les tests de base
```

---

## 🔗 Liens Utiles

- Guide simple : [`RUN_TESTS.md`](RUN_TESTS.md)
- Démarrage : [`START_HERE.md`](START_HERE.md)
- Troubleshooting : [`TESTING_INSTRUCTIONS.md`](TESTING_INSTRUCTIONS.md)

---

**Dernière mise à jour** : 2026-01-05
