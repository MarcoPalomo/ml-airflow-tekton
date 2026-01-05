#!/bin/bash
###############################################################################
# Script de Setup et Exécution des Tests
# Usage: ./setup_and_test.sh [options]
###############################################################################

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Se placer dans le bon répertoire
cd "$(dirname "$0")/model-code"

print_step "1. Vérification de l'environnement virtuel"
if [ ! -d "../venv" ]; then
    print_warning "Création de l'environnement virtuel..."
    cd ..
    python3 -m venv venv
    cd model-code
    print_success "Environnement virtuel créé"
else
    print_success "Environnement virtuel déjà présent"
fi

print_step "2. Activation de l'environnement virtuel"
source ../venv/bin/activate
print_success "Environnement virtuel activé"

print_step "3. Installation des dépendances"
pip install -q --upgrade pip
pip install -q -r requirements.txt
print_success "Dépendances installées"

print_step "4. Vérification de pytest"
pytest --version
print_success "pytest opérationnel"

print_step "5. Exécution des tests"
echo ""

# Passer tous les arguments au script de test
if [ $# -eq 0 ]; then
    # Pas d'arguments : exécuter tous les tests
    ./run_tests.sh
else
    # Avec arguments
    ./run_tests.sh "$@"
fi

print_step "Terminé !"
echo -e "${GREEN}Pour réutiliser l'environnement virtuel :${NC}"
echo "  source venv/bin/activate"
echo "  cd model-code"
echo "  ./run_tests.sh"
