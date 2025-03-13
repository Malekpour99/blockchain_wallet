#!/bin/bash

# Generate a 32-byte random encryptio key and encode it in base64
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Check if .env file exists, if not, create it
if [ ! -f .env ]; then
    touch .env
fi

# Remove any existing ENCRYPTION_KEY entry and append the new key
sed -i '/^ENCRYPTION_KEY=/d' .env
echo "ENCRYPTION_KEY=\"$ENCRYPTION_KEY\"" >> .env

echo "Encryption key generated and stored in .env"
