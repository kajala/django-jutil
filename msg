python manage.py makemessages -i venv -i data
cd jutil/locale
python ../../manage.py compilemessages
cd ../..
