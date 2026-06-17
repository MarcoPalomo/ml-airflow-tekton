# 🧪 Instructions pour Exécuter les Tests

Ce guide vous explique comment exécuter les tests du projet ML Airflow Tekton.

---

## ⚡ Méthode Rapide (Tout-en-Un)

Un script fait tout pour vous (création venv, installation, exécution) :

```bash
./setup_and_test.sh
```

C'est tout ! Le script va :
1. ✅ Créer l'environnement virtuel (si besoin)
2. ✅ Activer l'environnement
3. ✅ Installer toutes les dépendances
4. ✅ Exécuter les tests

### Options du script

```bash
./setup_and_test.sh                 # Tous les tests
./setup_and_test.sh --unit          # Tests unitaires seulement
./setup_and_test.sh --coverage      # Avec rapport de couverture
./setup_and_test.sh --verbose       # Mode verbeux
```

---

## 🔧 Méthode Manuelle (Étape par Étape)

### 1. Créer l'environnement virtuel

```bash
python3 -m venv venv
```

### 2. Activer l'environnement

```bash
source venv/bin/activate
```

Vous devriez voir `(venv)` apparaître dans votre prompt.

### 3. Installer les dépendances

```bash
cd model-code/
pip install -r requirements.txt
```

Cela va installer :
- pytest, pytest-cov, pytest-mock (tests)
- scikit-learn, pandas, numpy (ML)
- fastapi, uvicorn (API)
- mlflow (MLOps)
- Et toutes les autres dépendances

### 4. Exécuter les tests

```bash
./run_tests.sh
```

Ou avec des options :

```bash
./run_tests.sh --unit           # Tests unitaires seulement
./run_tests.sh --integration    # Tests d'intégration seulement
./run_tests.sh --coverage       # Avec rapport de couverture
./run_tests.sh --verbose        # Mode détaillé
./run_tests.sh --fail-fast      # Arrêter au premier échec
```

### 5. Voir le rapport de couverture

Après avoir exécuté avec `--coverage` :

```bash
# Dans le navigateur
firefox htmlcov/index.html
# ou
xdg-open htmlcov/index.html

# Dans le terminal
coverage report
```

---

## 📋 Exécution avec pytest Directement

Si vous préférez utiliser pytest directement :

```bash
# Activer l'environnement
source venv/bin/activate
cd model-code/

# Tous les tests
pytest tests/

# Un fichier spécifique
pytest tests/test_preprocessing.py

# Avec couverture
pytest --cov=src --cov-report=html tests/

# Mode verbeux
pytest -v tests/

# Stopper au premier échec
pytest -x tests/
```

---

## 🎯 Exemples de Sortie

### Succès ✅

```
========================================
Exécution des tests unitaires
========================================

test_preprocessing.py::TestDataPreprocessor::test_init PASSED
test_preprocessing.py::TestDataPreprocessor::test_load_data_csv PASSED
test_preprocessing.py::TestDataPreprocessor::test_clean_data PASSED
...
test_train.py::TestModelTrainer::test_train_random_forest PASSED
...

✓ Tests unitaires réussis

========================================
Exécution des tests d'intégration
========================================

test_api.py::TestHealthEndpoint::test_health_endpoint_with_model PASSED
test_api.py::TestPredictEndpoint::test_predict_with_model PASSED
...

✓ Tests d'intégration réussis

========================================
Résumé
========================================

╔════════════════════════════════════════╗
║                                        ║
║          TESTS RÉUSSIS ✓               ║
║                                        ║
╚════════════════════════════════════════╝
```

### Avec Couverture 📊

```
========================================
Rapport de couverture
========================================

ℹ Rapport HTML généré: htmlcov/index.html
ℹ Rapport XML généré: coverage.xml
ℹ Couverture totale: 85%

✓ La couverture est supérieure à 80%
```

---

## 🐛 Debugging

### Si les imports ne marchent pas

```bash
# Ajouter src au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Si pytest n'est pas trouvé

```bash
# Vérifier que l'environnement virtuel est activé
which python
# Devrait afficher: .../venv/bin/python

# Sinon, réactiver
source venv/bin/activate
```

### Afficher plus de détails

```bash
pytest -vv -s tests/
```

---

## 📁 Structure des Tests

```
model-code/
├── tests/
│   ├── conftest.py              # Fixtures communes
│   ├── test_preprocessing.py    # 35 tests
│   ├── test_train.py           # 25 tests
│   ├── test_api.py             # 40 tests
│   └── README.md               # Doc détaillée
├── run_tests.sh                # Script d'exécution
├── pytest.ini                  # Configuration pytest
└── requirements.txt            # Dépendances

airflow/
└── tests/
    └── test_functions.py       # 25 tests Airflow
```

---

## 📈 Statistiques

| Métrique | Valeur |
|----------|--------|
| **Total de tests** | 140+ |
| **Couverture visée** | ≥ 80% |
| **Temps d'exécution** | ~30 secondes |
| **Tests unitaires** | 85 tests |
| **Tests d'intégration** | 40 tests |
| **Tests Airflow** | 25 tests |

---

## 🔄 Workflow Typique

### Pendant le Développement

```bash
# 1. Activer l'environnement (une fois par session)
source venv/bin/activate

# 2. Travailler sur le code
# ... éditer les fichiers ...

# 3. Tester rapidement
cd model-code/
pytest tests/test_preprocessing.py -v

# 4. Tester en mode fail-fast
pytest -x tests/

# 5. Avant de commiter
./run_tests.sh --coverage
```

### Avant un Commit

```bash
# Test complet avec couverture
./setup_and_test.sh --coverage

# Vérifier la couverture
coverage report --fail-under=80

# Si OK, commiter
git add .
git commit -m "feat: add new feature"
```

---

## 🚀 CI/CD

Les tests peuvent être intégrés dans votre pipeline Tekton :

```yaml
- name: run-tests
  image: python:3.9-slim
  script: |
    cd /workspace/source
    python3 -m venv venv
    source venv/bin/activate
    cd model-code
    pip install -r requirements.txt
    ./run_tests.sh --coverage
    coverage report --fail-under=80
```

---

## 📚 Documentation Complète

- **Guide rapide** : [`QUICK_TEST_GUIDE.md`](QUICK_TEST_GUIDE.md)
- **Documentation détaillée** : [`model-code/tests/README.md`](model-code/tests/README.md)
- **Corrections effectuées** : [`CORRECTIONS.md`](CORRECTIONS.md)
- **Sécurité** : [`SECURITY.md`](SECURITY.md)

---

## 🆘 Besoin d'Aide ?

### Commandes utiles

```bash
pytest --help                    # Aide pytest
pytest --version                 # Version
pytest --fixtures tests/         # Voir les fixtures
pytest --markers                 # Voir les marqueurs
pytest --collect-only tests/     # Voir les tests collectés
```

### Problèmes fréquents

| Problème | Solution |
|----------|----------|
| `pytest: command not found` | Activer venv : `source venv/bin/activate` |
| `ModuleNotFoundError` | Installer deps : `pip install -r requirements.txt` |
| `ImportError` | Ajouter au PATH : `export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"` |
| Tests lents | Paralléliser : `pip install pytest-xdist && pytest -n auto tests/` |

---

## ✅ Checklist

Avant de considérer les tests comme validés :

- [ ] L'environnement virtuel est créé et activé
- [ ] Toutes les dépendances sont installées
- [ ] Tous les tests passent (140+ tests)
- [ ] La couverture est ≥ 80%
- [ ] Aucune erreur ou warning critique
- [ ] Le rapport de couverture HTML est généré

Pour vérifier :

```bash
./setup_and_test.sh --coverage
coverage report | grep TOTAL
# Devrait afficher: TOTAL ... 85%
```

---

**Dernière mise à jour** : 2026-01-05
**Version** : 1.0.0
