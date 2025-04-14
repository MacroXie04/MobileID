## Installation using django test server (test only for development)

### 1. Clone the repository

```bash
   git clone https://github.com/MacroXie04/UCMerced-Barcode.git
```

### 2. Create a virtual environment

```bash
   python3 -m venv venv
```

### 3. Activate the virtual environment

```bash
   source venv/bin/activate
```

### 4. Install the required packages

```bash
   pip install -r requirements.txt
```

### 5. Migrate the database

```bash
   python manage.py makemigrations mobileid
```

```bash
   python manage.py makemigrations
```

```bash
   python manage.py migrate
```

### 6. Collect static files
- 

```bash
   python manage.py collectstatic
```

### 7. Create a superuser

```bash
   python manage.py createsuperuser
```

### 8. Run the server

```bash
   python manage.py runserver
```

---

## Installation using Gunicorn and Nginx

### 1. Install Gunicorn

```bash
   pip install gunicorn
```

### 2. Install Nginx

```bash
   sudo apt install nginx
```

### 3. Configure Nginx
- Create a new configuration file for your site in `/etc/nginx/sites-available/`:

```bash
   sudo nano /etc/nginx/sites-available/ucm_barcode
```

- Add the following configuration:

```nginx
server {
    listen 80;
    # add your domain or IP address to allow host in django settings
    server_name your_domain_or_IP;
    
    location /static/ {
        root /path/to/your/project;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/tmp/ucmerced.sock;
    }
}

    
```

- Create a symbolic link to enable the site:

```bash
   sudo ln -s /etc/nginx/sites-available/ucm_barcode /etc/nginx/sites-enabled
```

- Test the Nginx configuration:

```bash
   sudo nginx -t
```

- Restart Nginx:

```bash
   sudo systemctl restart nginx
```

### 4. Start Gunicorn
- Navigate to your project directory:

```bash
   cd /path/to/your/project
```

- Start Gunicorn with the following command:

```bash
   gunicorn ucm_barcode.wsgi:application --bind unix:/tmp/ucmerced.sock --workers 3 --daemon --access-logfile /var/log/gunicorn_access.log --error-logfile /var/log/gunicorn_error.log
```


---

## Installation using Docker
### 1. Install Docker
- Follow the official Docker installation guide for your operating system: [Docker Installation](https://docs.docker.com/get-docker/)

### 2. Build the Docker image by using dockerfile
```bash
   docker build -t ucm_barcode .
```

### 3. Run the Docker container
```bash
   docker run -d -p 8000:8000 ucm_barcode
```

### 4. Stop the Docker container
```bash
   docker stop <container_id>
```



