@echo off
cd /d "%~dp0"
call venv\Scripts\activate
pip install django==5.0.6 django-crispy-forms==2.1 crispy-bootstrap5==0.7 whitenoise==6.7.0 python-decouple==3.8 -q
python manage.py runserver
pause