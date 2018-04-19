# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


reqs = parse_requirements('requirements.txt', session=False)
install_requires = [str(ir.req) for ir in reqs if str(ir.req) != 'None']

setup(
    name='django-jutil',
    version='1.1.6',
    author=u'Jani Kajala',
    author_email='kajala@gmail.com',
    packages=find_packages(exclude=['project', 'venv']),
    include_package_data=True,
    url='https://github.com/kajala/django-jutil',
    license='MIT licence, see LICENCE.txt',
    description='Collection of small utilities for Django and Django REST framework projects',
    long_description=open('README.md').read(),
    zip_safe=True,
    install_requires=install_requires
)
