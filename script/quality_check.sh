#!/bin/bash

# Script de vérification de qualité de code "AAA"
# Standards: Black, Isort, Ruff, Flake8, Pydocstyle, Vulture, Pylint, Pytest
# Line length: 120

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR=".venv"
SRC_DIR="src"
ENTRY_POINT="main.py"
LINE_LENGTH=120
VULTURE_CONFIDENCE=65
PYLINT_SCORE=9.5
COVERAGE_TARGET=80

# Variables d'état pour le rapport
declare -A STATUS
STATUS[CLEANUP]="SKIPPED"
STATUS[REQUIREMENTS]="SKIPPED"
STATUS[BLACK]="SKIPPED"
STATUS[ISORT]="SKIPPED"
STATUS[RUFF]="SKIPPED"
STATUS[FLAKE8]="SKIPPED"
STATUS[PYDOCSTYLE]="SKIPPED"
STATUS[MYPY]="SKIPPED"
STATUS[VULTURE]="SKIPPED"
STATUS[PYLINT]="SKIPPED"
STATUS[PYTEST]="SKIPPED"

# Flags d'exécution
RUN_ALL=true
RUN_CLEANUP=false
RUN_REQUIREMENTS=false
RUN_BLACK=false
RUN_ISORT=false
RUN_RUFF=false
RUN_FLAKE8=false
RUN_PYDOCSTYLE=false
RUN_MYPY=false
RUN_VULTURE=false
RUN_PYLINT=false
RUN_PYTEST=false

# Fonction d'aide
usage() {
    echo -e "${BOLD}Usage:${NC} $0 [OPTIONS]"
    echo -e "Script de vérification de qualité de code AAA."
    echo -e "\n${BOLD}Options Générales:${NC}"
    echo -e "  -h, --help       Affiche ce message d'aide"
    echo -e "  --clean          Nettoie uniquement les fichiers de cache et quitte"
    echo -e "\n${BOLD}Options d'exécution ciblée (désactive l'exécution de tout par défaut):${NC}"
    echo -e "  --requirements   Vérifie les dépendances"
    echo -e "  --black          Exécute Black (Formatage)"
    echo -e "  --isort          Exécute Isort (Imports)"
    echo -e "  --ruff           Exécute Ruff (Linting rapide)"
    echo -e "  --flake8         Exécute Flake8 (Linting strict)"
    echo -e "  --pydocstyle     Exécute Pydocstyle (Docstrings)"
    echo -e "  --mypy           Exécute Mypy (Typage statique)"
    echo -e "  --vulture        Exécute Vulture (Code mort)"
    echo -e "  --pylint         Exécute Pylint (Analyse approfondie)"
    echo -e "  --pytest         Exécute Pytest (Tests & Couverture)"
    exit 0
}

# Fonction d'affichage améliorée
print_header() {
    local title="   $1"
    local target_width=67
    local visible_len=${#title}
    local pad_len=$((target_width - visible_len))
    local padding=""
    if [ $pad_len -gt 0 ]; then
        padding=$(printf '%*s' "$pad_len" "")
    fi
    
    echo -e "\n${MAGENTA}${BOLD}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}${BOLD}║${title}${padding}║${NC}"
    echo -e "${MAGENTA}${BOLD}╚═══════════════════════════════════════════════════════════════════╝${NC}"
}

print_info() {
    echo -e "${CYAN}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✔ $1${NC}"
}

print_error() {
    echo -e "${RED}✘ $1${NC}"
}

set_status() {
    if [ $2 -eq 0 ]; then
        STATUS[$1]="${GREEN}PASS${NC}"
    else
        STATUS[$1]="${RED}FAIL${NC}"
    fi
}

# Analyse des arguments
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

# Si des arguments spécifiques sont passés, on désactive le RUN_ALL
if [[ $# -gt 0 ]]; then
    RUN_ALL=false
    for arg in "$@"; do
        case $arg in
            --clean)        RUN_CLEANUP=true ;;
            --requirements) RUN_REQUIREMENTS=true ;;
            --black)        RUN_BLACK=true ;;
            --isort)        RUN_ISORT=true ;;
            --ruff)         RUN_RUFF=true ;;
            --flake8)       RUN_FLAKE8=true ;;
            --pydocstyle)   RUN_PYDOCSTYLE=true ;;
            --mypy)         RUN_MYPY=true ;;
            --vulture)      RUN_VULTURE=true ;;
            --pylint)       RUN_PYLINT=true ;;
            --pytest)       RUN_PYTEST=true ;;
            *)              echo -e "${RED}Option inconnue: $arg${NC}"; usage ;;
        esac
    done
fi

# Si aucun argument spécifique n'est passé (ou juste --clean qui est géré à part si seul), on active tout
if [[ $RUN_ALL == true ]]; then
    RUN_CLEANUP=true
    RUN_REQUIREMENTS=true
    RUN_BLACK=true
    RUN_ISORT=true
    RUN_RUFF=true
    RUN_FLAKE8=true
    RUN_PYDOCSTYLE=true
    RUN_MYPY=true
    RUN_VULTURE=true
    RUN_PYLINT=true
    RUN_PYTEST=true
fi

# Si --clean est le seul argument, on quitte après
if [[ $# -eq 1 && "$1" == "--clean" ]]; then
    print_header "Nettoyage Rapide"
    print_info "Suppression des caches..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
    print_success "Nettoyage terminé."
    exit 0
fi

# Vérification de l'environnement virtuel
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Erreur: Environnement virtuel $VENV_DIR non trouvé.${NC}"
    exit 1
fi

# Activation de l'environnement
source "$VENV_DIR/bin/activate"

# --- EXÉCUTION DES TÂCHES ---

# Nettoyage
if [[ $RUN_CLEANUP == true ]]; then
    print_header "Nettoyage"
    print_info "Suppression des caches et fichiers temporaires..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
    if [ $? -eq 0 ]; then
        set_status "CLEANUP" 0
        print_success "Nettoyage terminé."
    else
        set_status "CLEANUP" 1
        print_error "Erreur lors du nettoyage."
    fi
fi

# Requirements
if [[ $RUN_REQUIREMENTS == true ]]; then
    print_header "Vérification des dépendances"
    MISSING_PKGS=0
    while read -r pkg; do
        [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue
        pkg_name=$(echo "$pkg" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/')
        if ! pip show "$pkg_name" > /dev/null 2>&1; then
            print_error "Manquant: $pkg_name"
            MISSING_PKGS=1
        else
            # echo -e "${GREEN}Installé: $pkg_name${NC}" # Trop verbeux pour le mode joli
            :
        fi
    done < requirements.txt

    if [ $MISSING_PKGS -eq 0 ]; then
        set_status "REQUIREMENTS" 0
        print_success "Toutes les dépendances sont installées."
    else
        set_status "REQUIREMENTS" 1
        print_error "Certaines dépendances sont manquantes."
        if [[ $RUN_ALL == true ]]; then exit 1; fi
    fi
fi

# Black
if [[ $RUN_BLACK == true ]]; then
    print_header "Formatage (Black)"
    print_info "Exécution de Black..."
    black --line-length $LINE_LENGTH "$SRC_DIR" "$ENTRY_POINT"
    set_status "BLACK" $?
fi

# Vulture (Code Mort) - Déplacé ici selon l'ordre demandé
if [[ $RUN_VULTURE == true ]]; then
    print_header "Code Mort (Vulture)"
    print_info "Exécution de Vulture (Confiance > $VULTURE_CONFIDENCE%)..."
    vulture "$SRC_DIR" "$ENTRY_POINT" --min-confidence $VULTURE_CONFIDENCE
    set_status "VULTURE" $?
fi

# Pydocstyle (Docstrings) - Déplacé ici selon l'ordre demandé
if [[ $RUN_PYDOCSTYLE == true ]]; then
    print_header "Docstrings (Pydocstyle)"
    print_info "Exécution de Pydocstyle..."
    pydocstyle "$SRC_DIR" "$ENTRY_POINT" --count
    set_status "PYDOCSTYLE" $?
fi

# Flake8 (Linting) - Déplacé ici selon l'ordre demandé
if [[ $RUN_FLAKE8 == true ]]; then
    print_header "Linting (Flake8)"
    print_info "Exécution de Flake8..."
    flake8 "$SRC_DIR" "$ENTRY_POINT" --max-line-length=$LINE_LENGTH --ignore=E203,W503
    set_status "FLAKE8" $?
fi

# Isort (Imports) - Déplacé ici selon l'ordre demandé
if [[ $RUN_ISORT == true ]]; then
    print_header "Imports (Isort)"
    print_info "Exécution de Isort..."
    isort --profile black --line-length $LINE_LENGTH "$SRC_DIR" "$ENTRY_POINT"
    set_status "ISORT" $?
fi

# Mypy (Typage) - Déplacé ici selon l'ordre demandé
if [[ $RUN_MYPY == true ]]; then
    print_header "Typage Statique (Mypy)"
    print_info "Exécution de Mypy..."
    mypy "$SRC_DIR" "$ENTRY_POINT"
    set_status "MYPY" $?
fi

# Ruff (Linting) - Déplacé ici selon l'ordre demandé
if [[ $RUN_RUFF == true ]]; then
    print_header "Linting (Ruff)"
    print_info "Exécution de Ruff..."
    ruff check "$SRC_DIR" "$ENTRY_POINT" --fix
    set_status "RUFF" $?
fi

# Pylint (Qualité) - Déplacé ici selon l'ordre demandé
if [[ $RUN_PYLINT == true ]]; then
    print_header "Qualité (Pylint)"
    print_info "Exécution de Pylint (Objectif: $PYLINT_SCORE/10)..."
    pylint "$SRC_DIR" "$ENTRY_POINT" --fail-under=$PYLINT_SCORE
    set_status "PYLINT" $?
fi

# Pytest (Tests) - Déplacé ici selon l'ordre demandé
if [[ $RUN_PYTEST == true ]]; then
    print_header "Tests & Couverture (Pytest)"
    print_info "Exécution de Pytest (Objectif couverture: $COVERAGE_TARGET%)..."
    pytest --cov="$SRC_DIR" --cov-report=term-missing:skip-covered --cov-report=xml --cov-report=html --cov-fail-under=$COVERAGE_TARGET
    set_status "PYTEST" $?
fi

# RAPPORT FINAL
echo -e "\n"
echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                  RAPPORT DE QUALITÉ (AAA)                         ║${NC}"
echo -e "${BOLD}╠═══════════════════════════════════════════════════════════════════╣${NC}"
printf "${BOLD}║ %-35s │ %-27s ║${NC}\n" "Outil" "Statut"
echo -e "${BOLD}╠─────────────────────────────────────┼─────────────────────────────╣${NC}"

# Fonction pour afficher une ligne du rapport si elle a été exécutée ou si tout a été exécuté
print_report_line() {
    local name=$1
    local key=$2
    local status_raw=${STATUS[$key]}
    
    # Calcul de la longueur visible du nom (gestion UTF-8)
    local name_len=$(echo -n "$name" | wc -m)
    local name_pad_len=$(( 35 - name_len ))
    local name_padding=""
    if [ $name_pad_len -gt 0 ]; then
        name_padding=$(printf '%*s' "$name_pad_len" "")
    fi

    # Nettoyer les codes couleurs pour calculer la longueur visible du statut
    local status_clean=$(echo -e "$status_raw" | sed 's/\x1b\[[0-9;]*m//g')
    
    # Calculer le padding nécessaire pour atteindre 27 caractères pour le statut
    local visible_len=${#status_clean}
    local pad_len=$(( 27 - visible_len ))
    local padding=""
    if [ $pad_len -gt 0 ]; then
        padding=$(printf '%*s' "$pad_len" "")
    fi
    
    printf "║ %s%s │ %b%s ║\n" "$name" "$name_padding" "$status_raw" "$padding"
}

print_report_line "Nettoyage (Cache)" "CLEANUP"
print_report_line "Dependances (Requirements)" "REQUIREMENTS"
print_report_line "Formatage (Black)" "BLACK"
print_report_line "Code Mort (Vulture)" "VULTURE"
print_report_line "Docstrings (Pydocstyle)" "PYDOCSTYLE"
print_report_line "Linting (Flake8)" "FLAKE8"
print_report_line "Imports (Isort)" "ISORT"
print_report_line "Typage (Mypy)" "MYPY"
print_report_line "Linting (Ruff)" "RUFF"
print_report_line "Qualité (Pylint)" "PYLINT"
print_report_line "Tests & Couverture (Pytest)" "PYTEST"

echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════════╝${NC}"

# Code de sortie global
# Si un seul test exécuté a échoué, le script retourne 1
GLOBAL_EXIT=0
for key in "${!STATUS[@]}"; do
    if [[ "${STATUS[$key]}" == *FAIL* ]]; then
        GLOBAL_EXIT=1
        break
    fi
done

if [ $GLOBAL_EXIT -eq 1 ]; then
    echo -e "\n${RED}${BOLD}❌ ÉCHEC : Certains critères de qualité ne sont pas respectés.${NC}"
    exit 1
else
    echo -e "\n${GREEN}${BOLD}✅ SUCCÈS : Tous les contrôles exécutés sont valides.${NC}"
    exit 0
fi
