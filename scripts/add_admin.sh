#!/bin/bash
# Script pour ajouter un administrateur McINT
# Usage: ./scripts/add_admin.sh email@example.com
#        ./scripts/add_admin.sh --list           (lister les admins)
#        ./scripts/add_admin.sh --remove email   (retirer les droits admin)

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Charger les variables d'environnement
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value || [ -n "$key" ]; do
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        key=$(echo "$key" | xargs)
        [[ "$key" =~ [[:space:]] ]] && continue
        value="${value%%#*}"
        value="${value%\"}"
        value="${value#\"}"
        value=$(echo "$value" | xargs)
        [[ "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] && export "$key=$value" 2>/dev/null || true
    done < "$ENV_FILE"
fi

POSTGRES_USER="${POSTGRES_USER:-user}"
POSTGRES_DB="${POSTGRES_DB:-mcint_db}"

# Trouver le conteneur de la base de données
find_db_container() {
    local container
    container=$(docker ps --filter "name=mcint-db" --filter "name=db" --format "{{.Names}}" | head -n1)

    if [ -z "$container" ]; then
        container=$(docker ps --filter "name=db" --format "{{.Names}}" | grep -E "(mcint.*db|db)" | head -n1)
    fi

    echo "$container"
}

DB_CONTAINER=$(find_db_container)

if [ -z "$DB_CONTAINER" ]; then
    echo -e "${RED}Erreur: Conteneur de base de donnees non trouve!${NC}"
    echo "Assurez-vous que docker-compose est lance."
    echo "Conteneurs disponibles:"
    docker ps --format "  - {{.Names}}"
    exit 1
fi

# Fonctions SQL
run_sql() {
    docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"
}

query_sql() {
    docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1" 2>/dev/null
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 <email> | --list | --remove <email>"
    echo ""
    echo "Options:"
    echo "  <email>           Ajouter un email comme administrateur"
    echo "  --list, -l        Lister tous les administrateurs"
    echo "  --remove, -r      Retirer les droits admin d'un email"
    echo "  --help, -h        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 admin@example.com"
    echo "  $0 --list"
    echo "  $0 --remove ancien.admin@example.com"
}

# Lister les admins
list_admins() {
    echo -e "${YELLOW}Administrateurs McINT:${NC}"
    echo ""
    local admins
    admins=$(query_sql "SELECT email FROM users WHERE user_type = 'admin' ORDER BY email;")

    if [ -z "$admins" ]; then
        echo "  (aucun administrateur)"
    else
        echo "$admins" | while read -r email; do
            echo -e "  ${GREEN}*${NC} $email"
        done
    fi
    echo ""
}

# Retirer les droits admin
remove_admin() {
    local email="$1"
    local normalized_email
    normalized_email=$(echo "$email" | tr '[:upper:]' '[:lower:]')

    # Verifier si l'utilisateur existe et est admin
    local current_type
    current_type=$(query_sql "SELECT user_type FROM users WHERE normalized_email = '$normalized_email';")

    if [ -z "$current_type" ]; then
        echo -e "${RED}Erreur: Utilisateur '$email' non trouve.${NC}"
        exit 1
    fi

    if [ "$current_type" != "admin" ]; then
        echo -e "${YELLOW}L'utilisateur '$email' n'est pas administrateur.${NC}"
        exit 0
    fi

    # Retirer les droits admin
    run_sql "UPDATE users SET user_type = NULL WHERE normalized_email = '$normalized_email';" > /dev/null
    echo -e "${GREEN}Droits admin retires pour '$email'.${NC}"
}

# Ajouter un admin
add_admin() {
    local email="$1"
    local normalized_email
    normalized_email=$(echo "$email" | tr '[:upper:]' '[:lower:]')

    # Validation basique de l'email
    if [[ ! "$email" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
        echo -e "${RED}Erreur: '$email' n'est pas une adresse email valide.${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Ajout de l'administrateur: $email${NC}"
    echo "  Conteneur: $DB_CONTAINER"
    echo ""

    # Verifier si l'utilisateur existe deja
    local existing
    existing=$(query_sql "SELECT user_type FROM users WHERE normalized_email = '$normalized_email';")

    if [ -n "$existing" ]; then
        if [ "$existing" = "admin" ]; then
            echo -e "${GREEN}L'utilisateur '$email' est deja administrateur.${NC}"
            exit 0
        fi

        # Mettre a jour l'utilisateur existant
        run_sql "UPDATE users SET user_type = 'admin' WHERE normalized_email = '$normalized_email';" > /dev/null
        echo -e "${GREEN}Utilisateur '$email' promu administrateur.${NC}"
    else
        # Creer un nouvel utilisateur admin
        run_sql "INSERT INTO users (email, normalized_email, user_type, email_verified, is_cotisant, created_at, updated_at, total_amount)
                 VALUES ('$email', '$normalized_email', 'admin', true, true, NOW(), NOW(), 0);" > /dev/null
        echo -e "${GREEN}Nouvel administrateur '$email' cree.${NC}"
    fi

    echo ""
    echo "L'utilisateur peut maintenant acceder a /admin"
}

# Main
case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --list|-l)
        list_admins
        ;;
    --remove|-r)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Erreur: Email requis pour --remove${NC}"
            show_help
            exit 1
        fi
        remove_admin "$2"
        ;;
    "")
        echo -e "${RED}Erreur: Email requis${NC}"
        echo ""
        show_help
        exit 1
        ;;
    *)
        add_admin "$1"
        ;;
esac
