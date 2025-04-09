gunicorn ucm_barcode.wsgi:application --bind unix:/tmp/ucmerced.sock --workers 3 --daemon --access-logfile /var/log/gunicorn_access.log --error-logfile /var/log/gunicorn_error.log
