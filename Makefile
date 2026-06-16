.PHONY: help install install-frontend install-backend dev frontend backend clean

help:
	@echo "Uso: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  make install        Instala dependencias del frontend y backend"
	@echo "  make dev            Inicia el servidor de desarrollo (frontend en :3000)"
	@echo "  make frontend       Inicia solo el frontend (Next.js dev server)"
	@echo "  make backend        Instala dependencias Python del backend"
	@echo "  make clean          Limpia node_modules, __pycache__, .venv"

install: install-backend install-frontend

install-frontend:
	@echo "Instalando dependencias del frontend..."
	cd frontend && npm install

install-backend:
	@echo "Instalando dependencias del backend..."
	cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

dev: frontend

frontend:
	@echo "Iniciando frontend en http://localhost:3000..."
	cd frontend && npm run dev

backend:
	@echo "Verifica que backend/.env este configurado. Ejemplo:"
	@echo "  cp backend/.env.example backend/.env"
	@echo "Luego instala dependencias con: make install-backend"
	@echo ""
	@echo "El backend se ejecuta automaticamente desde el frontend"
	@echo "via subprocess al enviar un mensaje en el chat."

clean:
	rm -rf frontend/node_modules frontend/.next
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/venv
	@echo "Limpieza completada."
