web: gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --worker-class gthread --timeout 120 --preload --access-logfile - --error-logfile -
