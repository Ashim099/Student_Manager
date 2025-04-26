# D:\StudentManager\start_services.ps1
Write-Host "Starting Django background task processor..."
Start-Job -ScriptBlock {
    Set-Location "D:\StudentManager"
    python manage.py process_tasks > process_tasks.log 2>&1
}

Write-Host "Starting Django server..."
python manage.py runserver 3369

#.\start_services.ps1         run this first to automatically run the project and server