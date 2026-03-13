web: gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --worker-class gthread --timeout 120 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile -
