#!/bin/bash

# Create certificates directory
mkdir -p certificates

# Generate a private key
openssl genrsa -out certificates/localhost-key.pem 2048

# Generate a certificate signing request
openssl req -new -key certificates/localhost-key.pem \
    -out certificates/localhost.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate a self-signed certificate with proper extensions
openssl x509 -req -days 365 \
    -in certificates/localhost.csr \
    -signkey certificates/localhost-key.pem \
    -out certificates/localhost.pem \
    -extensions v3_req \
    -extfile <(cat <<EOF
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost
DNS.2 = 127.0.0.1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)

# Clean up CSR file
rm certificates/localhost.csr

echo "Certificates generated successfully in ./certificates/"
echo "Files created:"
echo "  - certificates/localhost-key.pem (private key)"
echo "  - certificates/localhost.pem (certificate)" 