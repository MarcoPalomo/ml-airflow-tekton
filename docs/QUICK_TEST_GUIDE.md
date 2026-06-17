# Guide Rapide - Exécution des Tests

## 🚀 Démarrage Rapide

### Installation (une seule fois)
```bash
cd model-code/
pip install -r requirements.txt
```

### Exécution
```bash
# Tous les tests
./run_tests.sh

# Avec couverture
./run_tests.sh --coverage

# Tests unitaires seulement
./run_tests.sh --unit
```

---

## 📝 Commandes Fréquentes

### Avec le script (recommandé)
```bash
./run_tests.sh                    # Tous les tests
./run_tests.sh --unit             # Tests unitaires
./run_tests.sh --integration      # Tests d'intégration
./run_tests.sh --coverage         # Avec couverture
./run_tests.sh --verbose          # Mode verbeux
./run_tests.sh --fail-fast        # Stopper au 1er échec
```

### Avec pytest directement
```bash
pytest tests/                                    # Tous
pytest tests/test_preprocessing.py               # Un fichier
pytest tests/test_api.py::TestHealthEndpoint     # Une classe
pytest -v tests/                                 # Verbeux
pytest -x tests/                                 # Stopper au 1er échec
pytest -s tests/                                 # Afficher les prints
pytest --cov=src tests/                          # Avec couverture
```

---

## 🎯 Cas d'Usage

### Développement
```bash
# Tester rapidement un module
pytest tests/test_preprocessing.py -v

# Tester en continu (watch mode - nécessite pytest-watch)
pip install pytest-watch
ptw tests/
```

### Avant un commit
```bash
# Tests + couverture + vérifier le seuil
./run_tests.sh --coverage
coverage report --fail-under=80
```

### CI/CD
```bash
# Format pour CI avec rapport XML
pytest --cov=src --cov-report=xml --junitxml=junit.xml tests/
```

### Debugging
```bash
# Avec debugger
pytest --pdb tests/

# Très verbeux avec variables locales
pytest -vv -l tests/

# Un seul test en debug
pytest tests/test_api.py::test_health_endpoint --pdb
```

---

## 📊 Rapport de Couverture

```bash
# Générer le rapport HTML
pytest --cov=src --cov-report=html tests/

# Ouvrir le rapport
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # macOS

# Voir dans le terminal
coverage report

# Vérifier le seuil
coverage report --fail-under=80
```

---

## 🔍 Filtrage

### Par marqueur
```bash
pytest -m unit tests/           # Tests unitaires
pytest -m integration tests/    # Tests d'intégration
pytest -m api tests/            # Tests API
pytest -m "not slow" tests/     # Exclure les tests lents
```

### Par nom
```bash
pytest -k "test_load" tests/              # Tests contenant "load"
pytest -k "preprocessing or train" tests/ # preprocessing OU train
pytest -k "not api" tests/                # Exclure les tests API
```

---

## ⚡ Performance

### Tests en parallèle
```bash
pip install pytest-xdist
pytest -n auto tests/              # Auto-détection CPU
pytest -n 4 tests/                 # 4 workers
```

### Tests les plus lents
```bash
pytest --durations=10 tests/       # Top 10
pytest --durations=0 tests/        # Tous
```

---

## 🐛 Troubleshooting

### Import Error
```bash
# Ajouter src au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Fixtures non trouvées
```bash
# Lister les fixtures disponibles
pytest --fixtures tests/
```

### Voir la configuration
```bash
pytest --version              # Version pytest
pytest --markers              # Marqueurs disponibles
pytest --collect-only tests/  # Tests qui seront collectés
```

---

## 📁 Structure

```
model-code/
├── src/                    # Code source
│   ├── api/
│   ├── data/
│   └── models/
├── tests/                  # Tests
│   ├── conftest.py        # Fixtures
│   ├── test_preprocessing.py
│   ├── test_train.py
│   └── test_api.py
├── pytest.ini             # Config pytest
├── run_tests.sh          # Script automatisé
└── requirements.txt      # Dépendances
```

---

## 🎓 Best Practices

1. **Exécuter les tests avant chaque commit**
   ```bash
   ./run_tests.sh --coverage
   ```

2. **Maintenir une couverture ≥ 80%**
   ```bash
   coverage report --fail-under=80
   ```

3. **Utiliser les marqueurs pour filtrer**
   ```bash
   pytest -m "unit and not slow" tests/
   ```

4. **Tester en mode fail-fast pendant le dev**
   ```bash
   pytest -x tests/
   ```

5. **Vérifier les fixtures disponibles**
   ```bash
   pytest --fixtures tests/
   ```

---

## 📚 Documentation Complète

- Tests: `tests/README.md`
- Sécurité: `SECURITY.md`
- Corrections: `CORRECTIONS.md`

---

## 🆘 Aide

```bash
pytest --help                    # Aide pytest
./run_tests.sh --help           # Aide script (si implémenté)
pytest --markers                 # Marqueurs disponibles
pytest --fixtures tests/         # Fixtures disponibles
```

---

**Dernière mise à jour**: 2026-01-05
