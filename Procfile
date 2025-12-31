web: gunicorn shop.wsgi --log-file -
release: python manage.py makemigrations accounts
release: python manage.py makemigrations orders
release: python manage.py makemigrations catalog
release: python manage.py migrate