#!/bin/bash
# Script de mise à jour de la base de données McINT
# Ajoute les colonnes et index manquants au schéma
# Usage: ./scripts/update_db.sh

set -e

# Trouver le conteneur de la base de données
DB_CONTAINER=$(docker ps --filter "name=mcint-db" --filter "name=db" --format "{{.Names}}" | head -n1)

if [ -z "$DB_CONTAINER" ]; then
    # Essayer avec le nom du service docker-compose
    DB_CONTAINER=$(docker ps --filter "name=db" --format "{{.Names}}" | grep -E "(mcint.*db|db)" | head -n1)
fi

if [ -z "$DB_CONTAINER" ]; then
    echo "❌ Conteneur de base de données non trouvé!"
    echo "   Assurez-vous que docker-compose est lancé."
    echo "   Conteneurs disponibles:"
    docker ps --format "   - {{.Names}}"
    exit 1
fi

echo "🔧 Mise à jour de la base de données McINT..."
echo "   Conteneur: $DB_CONTAINER"
echo ""

# Fonction pour exécuter une commande SQL via docker exec
run_sql() {
    docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1" 2>/dev/null
}

# Fonction pour exécuter une requête SQL et obtenir le résultat
query_sql() {
    docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1" 2>/dev/null
}

# Charger les variables d'environnement
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Ignorer lignes vides et commentaires
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        # Nettoyer la clé
        key=$(echo "$key" | xargs)
        # Ignorer si la clé contient des espaces ou caractères invalides
        [[ "$key" =~ [[:space:]] ]] && continue
        # Nettoyer la valeur (enlever commentaires inline et guillemets)
        value="${value%%#*}"
        value="${value%\"}"
        value="${value#\"}"
        value=$(echo "$value" | xargs)
        # Exporter seulement si clé valide
        [[ "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] && export "$key=$value" 2>/dev/null || true
    done < "$ENV_FILE"
fi

POSTGRES_USER="${POSTGRES_USER:-user}"
POSTGRES_DB="${POSTGRES_DB:-mcint_db}"

# Test de connexion
echo "🔌 Test de connexion..."
if ! docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Impossible de se connecter à la base de données!"
    exit 1
fi
echo "✓ Connexion réussie"
echo ""

# Fonction pour ajouter une colonne si elle n'existe pas
add_column_if_not_exists() {
    local table="$1"
    local column="$2"
    local type="$3"
    local default="$4"
    
    echo -n "   $table.$column... "
    
    local result
    result=$(query_sql "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='$table' AND column_name='$column'")
    
    if [ "$result" = "1" ]; then
        echo "✓ existe"
    else
        if [ -n "$default" ]; then
            run_sql "ALTER TABLE $table ADD COLUMN IF NOT EXISTS $column $type DEFAULT $default;" > /dev/null 2>&1
        else
            run_sql "ALTER TABLE $table ADD COLUMN IF NOT EXISTS $column $type;" > /dev/null 2>&1
        fi
        echo "✓ ajouté"
    fi
}

# Fonction pour ajouter un index si il n'existe pas
add_index_if_not_exists() {
    local index_name="$1"
    local table="$2"
    local column="$3"
    
    echo -n "   $index_name... "
    
    local result
    result=$(query_sql "SELECT COUNT(*) FROM pg_indexes WHERE indexname='$index_name'")
    
    if [ "$result" = "1" ]; then
        echo "✓ existe"
    else
        run_sql "CREATE INDEX IF NOT EXISTS $index_name ON $table($column);" > /dev/null 2>&1
        echo "✓ créé"
    fi
}

echo "📦 Colonnes de la table 'users'..."

add_column_if_not_exists "users" "special_requests" "VARCHAR"
add_column_if_not_exists "users" "normalized_email" "VARCHAR"
add_column_if_not_exists "users" "prenom" "VARCHAR"
add_column_if_not_exists "users" "nom" "VARCHAR"
add_column_if_not_exists "users" "email_verified" "BOOLEAN" "false"
add_column_if_not_exists "users" "verification_code" "VARCHAR"
add_column_if_not_exists "users" "code_created_at" "TIMESTAMP"
add_column_if_not_exists "users" "is_cotisant" "BOOLEAN" "false"
add_column_if_not_exists "users" "cotisant_checked_at" "TIMESTAMP"
add_column_if_not_exists "users" "habite_residence" "BOOLEAN"
add_column_if_not_exists "users" "adresse_if_maisel" "VARCHAR"
add_column_if_not_exists "users" "numero_if_maisel" "INTEGER"
add_column_if_not_exists "users" "adresse" "VARCHAR"
add_column_if_not_exists "users" "phone" "VARCHAR"
add_column_if_not_exists "users" "total_amount" "FLOAT" "0.0"
add_column_if_not_exists "users" "payment_status" "VARCHAR" "'pending'"
add_column_if_not_exists "users" "payment_intent_id" "VARCHAR"
add_column_if_not_exists "users" "payment_date" "TIMESTAMP"
add_column_if_not_exists "users" "payment_attempts" "INTEGER" "0"
add_column_if_not_exists "users" "reservation_expires_at" "TIMESTAMP"
add_column_if_not_exists "users" "last_ip" "VARCHAR"
add_column_if_not_exists "users" "user_type" "VARCHAR"
add_column_if_not_exists "users" "status" "VARCHAR" "'confirmed'"
add_column_if_not_exists "users" "status_token" "VARCHAR"
add_column_if_not_exists "users" "menu_id" "VARCHAR"
add_column_if_not_exists "users" "boisson_id" "VARCHAR"
add_column_if_not_exists "users" "bonus_ids" "JSONB" "'[]'"
add_column_if_not_exists "users" "date_reservation" "DATE"
add_column_if_not_exists "users" "heure_reservation" "TIME"

# Migration: convertir bonus_id en bonus_ids si nécessaire
echo ""
echo "🔄 Migration bonus_id -> bonus_ids..."
BONUS_ID_EXISTS=$(query_sql "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='users' AND column_name='bonus_id'")
if [ "$BONUS_ID_EXISTS" = "1" ]; then
    echo "   Migration des données bonus_id existantes..."
    run_sql "UPDATE users SET bonus_ids = jsonb_build_array(bonus_id) WHERE bonus_id IS NOT NULL AND (bonus_ids IS NULL OR bonus_ids = '[]');" > /dev/null 2>&1
    echo "   ✓ Données migrées"
fi

echo ""
echo "📇 Index..."

add_index_if_not_exists "ix_users_status_token" "users" "status_token"
add_index_if_not_exists "ix_users_email" "users" "email"
add_index_if_not_exists "ix_users_normalized_email" "users" "normalized_email"
add_index_if_not_exists "ix_users_email_verified" "users" "email_verified"

echo ""
echo "✅ Mise à jour terminée !"
