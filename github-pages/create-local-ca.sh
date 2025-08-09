#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Creating Local Certificate Authority for Development${NC}"

# Create directories
mkdir -p certificates/ca

# Step 1: Generate CA private key
echo -e "${GREEN}1. Generating CA private key...${NC}"
openssl genrsa -out certificates/ca/ca-key.pem 4096

# Step 2: Generate CA certificate
echo -e "${GREEN}2. Generating CA certificate...${NC}"
openssl req -new -x509 -days 365 -key certificates/ca/ca-key.pem \
    -out certificates/ca/ca-cert.pem \
    -subj "/C=US/ST=State/L=City/O=Local Development CA/CN=Local Dev CA"

# Step 3: Generate server private key
echo -e "${GREEN}3. Generating server private key...${NC}"
openssl genrsa -out certificates/localhost-key.pem 2048

# Step 4: Generate certificate signing request with config
echo -e "${GREEN}4. Generating certificate signing request...${NC}"
cat > certificates/server.conf <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Local Development
CN = localhost

[v3_req]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = 127.0.0.1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

openssl req -new -key certificates/localhost-key.pem \
    -out certificates/localhost.csr \
    -config certificates/server.conf

# Step 5: Sign the certificate with our CA
echo -e "${GREEN}5. Signing certificate with CA...${NC}"
openssl x509 -req -days 365 \
    -in certificates/localhost.csr \
    -CA certificates/ca/ca-cert.pem \
    -CAkey certificates/ca/ca-key.pem \
    -CAcreateserial \
    -out certificates/localhost.pem \
    -extensions v3_req \
    -extfile certificates/server.conf

# Clean up
rm certificates/localhost.csr
rm certificates/server.conf

echo -e "${BLUE}Certificates created successfully!${NC}"
echo
echo -e "${GREEN}To trust the CA on macOS:${NC}"
echo "1. Run: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certificates/ca/ca-cert.pem"
echo "2. Or double-click certificates/ca/ca-cert.pem and add to System keychain as 'Always Trust'"
echo
echo -e "${GREEN}Files created:${NC}"
echo "  - certificates/ca/ca-cert.pem (Certificate Authority)"
echo "  - certificates/ca/ca-key.pem (CA private key - keep secure!)"
echo "  - certificates/localhost.pem (Server certificate)"
echo "  - certificates/localhost-key.pem (Server private key)" 