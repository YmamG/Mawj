# Create project folder
$project_folder = Read-Host "Enter your folder name"
mkdir $project_folder
cd $project_folder

# Setup virtual environment
python -m venv venv
.\venv\Scripts\activate.ps1

# Install Django
python -m pip install django
django-admin --version
python -m pip freeze > requirements.txt

# Create Django project
$project = Read-Host "Enter your project name"
django-admin startproject $project
cd $project

# Create Django app
$app = Read-Host "Enter your app name"
python manage.py startapp $app
