python manage.py makemessages -i venv -i data
pushd jutil
python ../manage.py compilemessages
popd

