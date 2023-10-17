#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Django and Django REST framework
pip install django djangorestframework

# Create a new Django project
django-admin startproject college_registration_system

# Navigate into the project directory
cd college_registration_system

# Create a new Django app
python manage.py startapp registration

# Deactivate the virtual environment
deactivate
