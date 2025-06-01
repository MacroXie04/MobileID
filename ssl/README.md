# HTTPS for Local Development

This directory contains files needed to enable HTTPS on localhost for development.

## How it Works

The Django development server has been configured to automatically use HTTPS when you run:

```bash
python manage.py runserver
```

The system will:
1. Check if SSL certificates exist in this directory
2. Generate self-signed certificates if they don't exist
3. Start the development server with HTTPS support

## Manual Certificate Generation

If you need to regenerate the certificates, you can run:

```bash
./ssl/generate_cert.sh
```

This will create:
- `localhost.key`: The private key
- `localhost.csr`: The certificate signing request
- `localhost.crt`: The self-signed certificate

## Browser Security Warnings

Since these are self-signed certificates, your browser will show a security warning when accessing the site. This is normal for local development. You can proceed by accepting the risk in your browser.

## Troubleshooting

If you encounter issues:
1. Make sure the SSL certificates exist in the `ssl` directory
2. Ensure the `generate_cert.sh` script is executable (`chmod +x ssl/generate_cert.sh`)
3. Try regenerating the certificates manually