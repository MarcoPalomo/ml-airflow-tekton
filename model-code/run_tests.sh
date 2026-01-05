#!/bin/bash
###############################################################################
# Script d'exécution des tests pour le pipeline Tekton
# Usage: ./run_tests.sh [options]
#
# Options:
#   --unit           Exécuter uniquement les tests unitaires
#   --integration    Exécuter uniquement les tests d'intégration
#   --coverage       Générer un rapport de couverture
#   --verbose        Mode verbeux
#   --fail-fast      Arrêter au premier échec
###############################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
TEST_DIR="$PROJECT_ROOT/tests"
SRC_DIR="$PROJECT_ROOT/src"

# Options par défaut
RUN_UNIT=true
RUN_INTEGRATION=true
GENERATE_COVERAGE=false
VERBOSE=false
FAIL_FAST=false

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            shift
            ;;
        --integration)
            RUN_UNIT=false
            RUN_INTEGRATION=true
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        *)
            echo -e "${RED}Option inconnue: $1${NC}"
            exit 1
            ;;
    esac
done

###############################################################################
# Fonctions utilitaires
###############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

###############################################################################
# Vérifications préalables
###############################################################################

print_header "Vérifications préalables"

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 n'est pas installé"
    exit 1
fi
print_success "Python 3 trouvé: $(python3 --version)"

# Vérifier que pytest est installé
if ! python3 -m pytest --version &> /dev/null; then
    print_error "pytest n'est pas installé"
    print_info "Installation: pip install pytest pytest-cov pytest-mock"
    exit 1
fi
print_success "pytest trouvé: $(python3 -m pytest --version)"

# Vérifier la structure des répertoires
if [ ! -d "$TEST_DIR" ]; then
    print_error "Répertoire de tests non trouvé: $TEST_DIR"
    exit 1
fi
print_success "Répertoire de tests trouvé"

if [ ! -d "$SRC_DIR" ]; then
    print_error "Répertoire source non trouvé: $SRC_DIR"
    exit 1
fi
print_success "Répertoire source trouvé"

###############################################################################
# Configuration pytest
###############################################################################

PYTEST_ARGS=""

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
else
    PYTEST_ARGS="$PYTEST_ARGS -q"
fi

if [ "$FAIL_FAST" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -x"
fi

if [ "$GENERATE_COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=$SRC_DIR --cov-report=html --cov-report=term --cov-report=xml"
fi

###############################################################################
# Exécution des tests
###############################################################################

cd "$PROJECT_ROOT"

EXIT_CODE=0

# Tests unitaires
if [ "$RUN_UNIT" = true ]; then
    print_header "Exécution des tests unitaires"

    python3 -m pytest $PYTEST_ARGS \
        "$TEST_DIR/test_preprocessing.py" \
        "$TEST_DIR/test_train.py" \
        2>&1 | tee /tmp/unit_tests.log

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Tests unitaires réussis"
    else
        print_error "Tests unitaires échoués"
        EXIT_CODE=1
    fi
fi

# Tests d'intégration
if [ "$RUN_INTEGRATION" = true ]; then
    print_header "Exécution des tests d'intégration"

    python3 -m pytest $PYTEST_ARGS \
        "$TEST_DIR/test_api.py" \
        2>&1 | tee /tmp/integration_tests.log

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Tests d'intégration réussis"
    else
        print_error "Tests d'intégration échoués"
        EXIT_CODE=1
    fi
fi

###############################################################################
# Rapport de couverture
###############################################################################

if [ "$GENERATE_COVERAGE" = true ]; then
    print_header "Rapport de couverture"

    if [ -f "htmlcov/index.html" ]; then
        print_info "Rapport HTML généré: htmlcov/index.html"
    fi

    if [ -f "coverage.xml" ]; then
        print_info "Rapport XML généré: coverage.xml"
    fi

    # Extraire le pourcentage de couverture
    if command -v coverage &> /dev/null; then
        COVERAGE_PERCENT=$(coverage report | tail -1 | awk '{print $4}')
        print_info "Couverture totale: $COVERAGE_PERCENT"

        # Vérifier le seuil minimum (80%)
        COVERAGE_NUM=${COVERAGE_PERCENT%\%}
        if (( $(echo "$COVERAGE_NUM < 80" | bc -l) )); then
            print_warning "La couverture est inférieure à 80%"
        else
            print_success "La couverture est supérieure à 80%"
        fi
    fi
fi

###############################################################################
# Résumé
###############################################################################

print_header "Résumé"

if [ $EXIT_CODE -eq 0 ]; then
    print_success "Tous les tests sont passés avec succès!"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                        ║${NC}"
    echo -e "${GREEN}║          TESTS RÉUSSIS ✓               ║${NC}"
    echo -e "${GREEN}║                                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
else
    print_error "Certains tests ont échoué"
    echo ""
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                        ║${NC}"
    echo -e "${RED}║          TESTS ÉCHOUÉS ✗               ║${NC}"
    echo -e "${RED}║                                        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"

    print_info "Consultez les logs pour plus de détails:"
    if [ "$RUN_UNIT" = true ]; then
        echo "  - Tests unitaires: /tmp/unit_tests.log"
    fi
    if [ "$RUN_INTEGRATION" = true ]; then
        echo "  - Tests d'intégration: /tmp/integration_tests.log"
    fi
fi

echo ""
exit $EXIT_CODE
