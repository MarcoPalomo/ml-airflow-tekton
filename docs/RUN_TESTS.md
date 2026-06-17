# 🚀 Comment Exécuter les Tests - Guide Ultra-Simple

## ⚡ Option 1 : Installation Minimale (Recommandé si problèmes)

Si vous avez des **problèmes d'installation** ou voulez juste **tester rapidement** :

```bash
./minimal_test.sh
```

✅ Ce script installe **uniquement** les dépendances essentielles :
- Évite les problèmes de dépendances complexes (MLflow, Trino, etc.)
- Plus rapide et plus fiable
- Suffisant pour la plupart des tests

**Temps estimé** : 1-2 minutes

---

## 📦 Option 2 : Setup Complet

Si vous voulez **toutes les dépendances** :

```bash
./setup_and_test.sh
```

✅ Ce script fait **TOUT** :
- Crée l'environnement virtuel
- Installe TOUTES les dépendances
- Exécute les tests

**Temps estimé** : 3-5 minutes (peut avoir des erreurs sur certaines dépendances)

---

## 🚀 Option 3 : Lancement Rapide (Déjà Configuré)

Si vous avez **déjà exécuté** le setup une fois :

```bash
./quick_test.sh
```

✅ Plus rapide (environnement déjà prêt)

**Temps estimé** : 30 secondes

---

## 🎛️ Option 4 : Avec Options

### Setup complet avec options

```bash
./setup_and_test.sh --coverage      # Avec rapport de couverture
./setup_and_test.sh --unit          # Tests unitaires seulement
./setup_and_test.sh --verbose       # Mode détaillé
```

### Test rapide avec pytest direct

```bash
./quick_test.sh                     # Mode simple
source venv/bin/activate           # Activer l'environnement
cd model-code/
pytest tests/ -v                    # Pytest directement
```

---

## 📊 Voir le Rapport de Couverture

```bash
# 1. Exécuter avec couverture
./setup_and_test.sh --coverage

# 2. Ouvrir le rapport
firefox htmlcov/index.html
# ou
xdg-open htmlcov/index.html
```

---

## ❓ Problèmes ?

### 🔴 Erreurs d'installation de dépendances (MLflow, great-expectations, etc.)

**Solution** : Utilisez le script minimal qui installe seulement l'essentiel :

```bash
./minimal_test.sh
```

Ce script évite les dépendances problématiques et installe uniquement :
- numpy, pandas, scikit-learn (ML de base)
- pytest (tests)
- fastapi (API)

### "pytest: command not found"
```bash
# Réexécuter le setup minimal
./minimal_test.sh
```

### "Permission denied"
```bash
chmod +x minimal_test.sh
chmod +x setup_and_test.sh
chmod +x quick_test.sh
```

### Erreur "subprocess-exited-with-error" ou "Getting requirements to build wheel"

**Cause** : Conflit de dépendances (souvent MLflow ou great-expectations)

**Solution 1** : Utiliser le script minimal
```bash
./minimal_test.sh
```

**Solution 2** : Installation manuelle ciblée
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install numpy pandas scikit-learn joblib
pip install pytest pytest-cov pytest-mock httpx
pip install fastapi pydantic
cd model-code/
pytest tests/ -v
```

### Les tests échouent avec des imports manquants

**Normal si vous utilisez minimal_test.sh** : Certains tests (Airflow, MLflow) peuvent échouer. Les tests de base (preprocessing, train, API) devraient passer.

Pour ignorer les tests qui nécessitent des dépendances optionnelles :
```bash
source venv/bin/activate
cd model-code/
pytest tests/test_preprocessing.py tests/test_train.py tests/test_api.py -v
```

---

## 📁 Scripts Disponibles

| Script | Usage | Quand l'utiliser |
|--------|-------|------------------|
| `minimal_test.sh` | ⭐ **Setup minimal + tests** | **RECOMMANDÉ** - Évite les problèmes de dépendances |
| `setup_and_test.sh` | Setup complet + tests | Si vous voulez TOUTES les dépendances |
| `quick_test.sh` | Tests rapides | Quand l'environnement est déjà configuré |
| `model-code/run_tests.sh` | Tests avec options avancées | Pour plus de contrôle |

---

## 📚 Documentation Complète

- **Ce fichier** : Guide ultra-simple (vous êtes ici !)
- [`TESTING_INSTRUCTIONS.md`](TESTING_INSTRUCTIONS.md) : Guide détaillé complet
- [`QUICK_TEST_GUIDE.md`](QUICK_TEST_GUIDE.md) : Aide-mémoire des commandes
- [`model-code/tests/README.md`](model-code/tests/README.md) : Documentation technique

---

## ✅ Checklist Rapide

- [ ] Première exécution : `./setup_and_test.sh`
- [ ] Voir si les tests passent (140+ tests)
- [ ] Vérifier la couverture (≥ 80%)
- [ ] Pour les fois suivantes : `./quick_test.sh`

---

**C'est tout !** 🎉

Pour plus de détails, consultez [`TESTING_INSTRUCTIONS.md`](TESTING_INSTRUCTIONS.md)

---

**Dernière mise à jour** : 2026-01-05
