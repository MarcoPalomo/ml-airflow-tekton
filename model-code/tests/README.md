# Tests - ML Airflow Tekton

Ce répertoire contient tous les tests pour le projet ML Airflow Tekton.

## Structure des Tests

```
tests/
├── conftest.py              # Fixtures communes à tous les tests
├── test_preprocessing.py    # Tests du module de preprocessing
├── test_train.py           # Tests du module de training
├── test_api.py             # Tests de l'API FastAPI
└── __init__.py
```

## Installation des Dépendances de Test

```bash
pip install -r requirements.txt
```

Packages de test requis :
- `pytest` - Framework de test
- `pytest-cov` - Couverture de code
- `pytest-mock` - Mocking avancé
- `requests-mock` - Mock des requêtes HTTP

## Exécution des Tests

### Tous les tests

```bash
# Depuis le répertoire model-code/
./run_tests.sh
```

### Tests unitaires uniquement

```bash
./run_tests.sh --unit
```

### Tests d'intégration uniquement

```bash
./run_tests.sh --integration
```

### Avec couverture de code

```bash
./run_tests.sh --coverage
```

### Mode verbeux

```bash
./run_tests.sh --verbose
```

### Arrêter au premier échec

```bash
./run_tests.sh --fail-fast
```

## Exécution avec pytest directement

### Tous les tests

```bash
pytest tests/
```

### Tests spécifiques

```bash
# Tests de preprocessing
pytest tests/test_preprocessing.py

# Tests de training
pytest tests/test_train.py

# Tests de l'API
pytest tests/test_api.py
```

### Avec couverture

```bash
pytest --cov=src --cov-report=html tests/
```

Le rapport HTML sera généré dans `htmlcov/index.html`

### Par marqueur

```bash
# Tests unitaires seulement
pytest -m unit

# Tests d'intégration seulement
pytest -m integration

# Tests de l'API
pytest -m api
```

### Tests en parallèle

```bash
# Installer pytest-xdist
pip install pytest-xdist

# Exécuter en parallèle
pytest -n auto tests/
```

## Organisation des Tests

### 1. Tests Unitaires (`test_preprocessing.py`, `test_train.py`)

Tests rapides qui testent des composants isolés :
- Fonctions individuelles
- Classes et méthodes
- Logique métier
- Pas de dépendances externes

**Exemples :**
- Test de chargement de données
- Test de nettoyage de données
- Test de création de modèle
- Test de calcul de métriques

### 2. Tests d'Intégration (`test_api.py`)

Tests qui vérifient l'interaction entre composants :
- Endpoints API
- Flux complets
- Intégration de plusieurs modules

**Exemples :**
- Test des endpoints FastAPI
- Test du flow complet de prédiction
- Test de l'authentification (à venir)

### 3. Fixtures (`conftest.py`)

Fixtures réutilisables pour tous les tests :
- `sample_dataframe` - DataFrame de test
- `preprocessor_config` - Configuration du preprocessor
- `trained_model` - Modèle pré-entraîné
- `api_test_request` - Requête API de test
- `mock_mlflow_run` - Mock MLflow

## Couverture de Code

### Objectif

Maintenir une couverture de code **≥ 80%** pour tous les modules critiques.

### Vérifier la couverture

```bash
pytest --cov=src --cov-report=term-missing tests/
```

### Rapport HTML

```bash
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html
```

### Par module

```bash
pytest --cov=src/data --cov-report=term tests/test_preprocessing.py
pytest --cov=src/models --cov-report=term tests/test_train.py
pytest --cov=src/api --cov-report=term tests/test_api.py
```

## Bonnes Pratiques

### 1. Nomenclature

- Fichiers de test : `test_*.py`
- Classes de test : `Test*`
- Fonctions de test : `test_*`

### 2. Structure d'un test

```python
def test_function_name():
    # Arrange (Préparer)
    input_data = create_test_data()

    # Act (Agir)
    result = function_to_test(input_data)

    # Assert (Vérifier)
    assert result == expected_value
```

### 3. Utilisation des fixtures

```python
def test_with_fixture(sample_dataframe):
    # sample_dataframe est automatiquement injecté
    assert len(sample_dataframe) > 0
```

### 4. Tests paramétrés

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6)
])
def test_multiple_cases(input, expected):
    assert double(input) == expected
```

### 5. Mocking

```python
def test_with_mock(monkeypatch):
    def mock_function():
        return "mocked value"

    monkeypatch.setattr(module, 'function', mock_function)
    result = module.function()
    assert result == "mocked value"
```

## CI/CD avec Tekton

Les tests sont automatiquement exécutés dans le pipeline Tekton :

```yaml
# tekton/tasks/test-model.yaml
- name: run-tests
  image: python:3.9
  script: |
    cd /workspace/source
    pip install -r requirements.txt
    ./run_tests.sh --coverage
```

### Critères de succès

- ✅ Tous les tests doivent passer (exit code 0)
- ✅ Couverture ≥ 80%
- ✅ Pas d'erreurs de linting (si configuré)

## Debugging des Tests

### Afficher les prints

```bash
pytest -s tests/
```

### Mode verbeux

```bash
pytest -vv tests/
```

### Stopper au premier échec

```bash
pytest -x tests/
```

### Lancer un test spécifique

```bash
pytest tests/test_preprocessing.py::TestDataPreprocessor::test_load_data_csv
```

### Debugger avec pdb

```python
def test_something():
    import pdb; pdb.set_trace()
    # Le test s'arrêtera ici
    assert True
```

Ou avec pytest :

```bash
pytest --pdb tests/
```

## Tests de Performance

Pour ajouter des tests de performance (optionnel) :

```bash
pip install pytest-benchmark

# Dans vos tests
def test_performance(benchmark):
    result = benchmark(function_to_test, arg1, arg2)
    assert result == expected
```

## Rapports de Test

### Format JUnit (pour CI/CD)

```bash
pytest --junitxml=junit.xml tests/
```

### Format JSON

```bash
pip install pytest-json-report
pytest --json-report --json-report-file=report.json tests/
```

## Troubleshooting

### Import Errors

Si vous avez des erreurs d'import :

```bash
# Ajouter le répertoire src au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Fixtures non trouvées

Vérifier que `conftest.py` est dans le bon répertoire et que pytest le détecte :

```bash
pytest --fixtures tests/
```

### Tests lents

Identifier les tests lents :

```bash
pytest --durations=10 tests/
```

## Ressources

- [Documentation pytest](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## TODO

- [ ] Ajouter des tests de performance
- [ ] Ajouter des tests de charge pour l'API
- [ ] Implémenter des tests de sécurité
- [ ] Ajouter des tests end-to-end complets
- [ ] Configurer les tests de mutation (mutpy)
