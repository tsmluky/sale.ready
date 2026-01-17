# Script para levantar TraderCopilot en Local (Backend + Frontend)

Write-Host "🚀 Iniciando TraderCopilot Local Environment..." -ForegroundColor Cyan

# 1. Iniciar Backend (Puerto 8000)
Write-Host "🔹 Lanzando Backend (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn main:app --reload --port 8000"

# Esperar unos segundos para que el backend arranque
Start-Sleep -Seconds 3

# 2. Iniciar Frontend (Puerto 5173 typically)
Write-Host "🔹 Lanzando Frontend (Vite)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web; npm run dev"

Write-Host "✅ Servicios iniciados." -ForegroundColor Green
Write-Host "👉 Backend: http://localhost:8000/docs"
Write-Host "👉 Frontend: http://localhost:5173"
