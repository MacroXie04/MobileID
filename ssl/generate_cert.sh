#!/bin/bash
# Generate a self-signed certificate for local development

# Create private key
openssl genrsa -out ssl/localhost.key 2048

# Create certificate signing request
openssl req -new -key ssl/localhost.key -out ssl/localhost.csr -subj "/CN=localhost"

# Create self-signed certificate
openssl x509 -req -days 365 -in ssl/localhost.csr -signkey ssl/localhost.key -out ssl/localhost.crt

echo "Self-signed certificate generated successfully."
echo "You can now run the development server with HTTPS."