@echo off
echo Running Django migrations...
C:\Users\btndb\Desktop\CodingProgramming\nodews\venv\Scripts\python.exe manage.py makemigrations
C:\Users\btndb\Desktop\CodingProgramming\nodews\venv\Scripts\python.exe manage.py migrate

echo Starting Daphne ASGI server...
C:\Users\btndb\Desktop\CodingProgramming\nodews\venv\Scripts\python.exe -m daphne -p 8000 nodews_project.asgi:application