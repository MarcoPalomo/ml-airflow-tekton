# 🎯 COMMENCEZ ICI

Bienvenue dans le projet ML Airflow Tekton ! Ce fichier vous guide en 2 minutes.

---

## ✅ Pour Exécuter les Tests (C'est Simple !)

### ⭐ Recommandé : Installation Minimale

```bash
./minimal_test.sh
```

**Le plus simple et le plus fiable !** Évite les problèmes de dépendances complexes.
⏱️ Temps : 1-2 minutes

### Alternative : Installation Complète

```bash
./setup_and_test.sh
```

Installe toutes les dépendances (peut avoir des erreurs sur MLflow/Trino).
⏱️ Temps : 3-5 minutes

---

## 📚 Documentation Disponible

Choisissez selon votre besoin :

| Document | Quand l'utiliser |
|----------|------------------|
| **[RUN_TESTS.md](RUN_TESTS.md)** | 🚀 **Commencez ici** - Guide ultra-simple pour les tests |
| [TESTING_INSTRUCTIONS.md](TESTING_INSTRUCTIONS.md) | Guide complet avec troubleshooting |
| [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) | Aide-mémoire des commandes |
| [CORRECTIONS.md](CORRECTIONS.md) | Rapport détaillé de toutes les corrections |
| [SECURITY.md](SECURITY.md) | Guide de sécurité pour la production |
| [README.md](README.md) | Vue d'ensemble du projet |

---

## 🎯 Actions Rapides

### Tests
```bash
./minimal_test.sh                # ⭐ RECOMMANDÉ - Installation minimale
./setup_and_test.sh              # Installation complète (peut avoir des erreurs)
./quick_test.sh                  # Lancements suivants (si déjà configuré)
```

### Voir le Rapport de Couverture
```bash
./setup_and_test.sh --coverage
firefox htmlcov/index.html
```

### Installation Manuelle (si problème)
```bash
python3 -m venv venv
source venv/bin/activate
pip install pytest pytest-cov pytest-mock
cd model-code/
pytest tests/ -v
```

---

## 📊 Ce Qui a Été Fait

### ✅ Corrections Critiques
- ✅ Fonctions manquantes dans Airflow implémentées
- ✅ Commande Kaniko corrigée
- ✅ Type mismatch dans l'API résolu
- ✅ Sécurité renforcée (variables d'environnement)

### ✅ Tests Créés
- ✅ 140+ tests (unitaires + intégration)
- ✅ ~85% de couverture de code
- ✅ Scripts d'exécution automatisés
- ✅ Documentation complète

### ✅ Sécurité
- ✅ `.env.example` créé
- ✅ `.gitignore` complet
- ✅ Guide de sécurité (400+ lignes)
- ✅ Avertissements dans le code

---

## 🆘 Besoin d'Aide ?

### Problème avec les tests ?
➡️ Consultez [RUN_TESTS.md](RUN_TESTS.md)

### Questions de sécurité ?
➡️ Consultez [SECURITY.md](SECURITY.md)

### Détails techniques ?
➡️ Consultez [CORRECTIONS.md](CORRECTIONS.md)

---

## 🚀 Prochaines Étapes Recommandées

1. ✅ **Exécuter les tests** : `./setup_and_test.sh`
2. ✅ **Vérifier la couverture** : Ouvrir `htmlcov/index.html`
3. ⚠️ **Sécurité** : Lire [SECURITY.md](SECURITY.md) avant production
4. 📝 **Créer votre .env** : `cp .env.example .env` et remplir

---

**Questions ?** Consultez la documentation ci-dessus ou créez une issue !

**Dernière mise à jour** : 2026-01-05
