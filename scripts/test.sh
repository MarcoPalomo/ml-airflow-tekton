#!/usr/bin/env bash
###############################################################################
# Script unique de test pour ml-airflow-tekton
#
# Remplace : setup_and_test.sh, quick_test.sh, minimal_test.sh,
#            test_basic.sh, clean_and_reset.sh
#
# Usage :
#   ./scripts/test.sh              # crée/réutilise le venv, installe, lance pytest
#   ./scripts/test.sh -m unit      # passe des arguments à pytest
#   ./scripts/test.sh --cov        # rapport de couverture
#   ./scripts/test.sh --clean      # supprime le venv et les caches
###############################################################################
set -euo pipefail

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
step()    { echo -e "\n${BLUE}▶ $1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $1${NC}"; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
MODEL_DIR="${ROOT_DIR}/model-code"

# --- Nettoyage ---------------------------------------------------------------
if [[ "${1:-}" == "--clean" ]]; then
    step "Nettoyage de l'environnement"
    rm -rf "${VENV_DIR}"
    find "${ROOT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${ROOT_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find "${ROOT_DIR}" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find "${ROOT_DIR}" -type f -name "*.py[co]" -delete 2>/dev/null || true
    rm -rf "${MODEL_DIR}/htmlcov" "${MODEL_DIR}/.coverage" 2>/dev/null || true
    success "Nettoyage terminé"
    exit 0
fi

# --- Préparation du venv -----------------------------------------------------
if [[ ! -d "${VENV_DIR}" ]]; then
    step "Création de l'environnement virtuel (.venv)"
    python3 -m venv "${VENV_DIR}"
    success "venv créé"
else
    success "venv déjà présent"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

step "Installation des dépendances de test"
python -m pip install --quiet --upgrade pip
pip install --quiet -r "${MODEL_DIR}/requirements-test.txt"
# mlflow est requis par les tests d'entraînement (train.py)
pip install --quiet "mlflow==2.17.2"
success "Dépendances installées"

# --- Exécution des tests -----------------------------------------------------
step "Exécution de la suite de tests"
cd "${MODEL_DIR}"

if [[ "${1:-}" == "--cov" ]]; then
    shift
    pytest tests/ --cov=src --cov-report=term-missing --cov-report=html "$@"
else
    pytest tests/ "$@"
fi
