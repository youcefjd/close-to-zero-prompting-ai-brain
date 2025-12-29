#!/bin/bash
# Secure script to add secrets to .env file
# Prompts for secret value with masked input

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <ENV_VAR_NAME>"
    echo "Example: $0 COOKIDOO_API_KEY"
    exit 1
fi

ENV_VAR_NAME=$1
ENV_FILE=".env"

# Check if .env exists, create if not
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
    echo "# Environment variables" >> "$ENV_FILE"
fi

# Check if variable already exists
if grep -q "^${ENV_VAR_NAME}=" "$ENV_FILE"; then
    echo "⚠️  ${ENV_VAR_NAME} already exists in .env"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove existing line
    sed -i.bak "/^${ENV_VAR_NAME}=/d" "$ENV_FILE"
fi

# Prompt for secret value (masked)
echo "Enter value for ${ENV_VAR_NAME} (input will be hidden):"
read -s SECRET_VALUE

if [ -z "$SECRET_VALUE" ]; then
    echo "❌ Empty value provided. Cancelled."
    exit 1
fi

# Add to .env file
echo "${ENV_VAR_NAME}=${SECRET_VALUE}" >> "$ENV_FILE"

echo "✅ ${ENV_VAR_NAME} added to .env file"
echo "⚠️  Remember to add .env to .gitignore if not already present"

