# Dev Password Organizer
Умный органайзер паролей для разработчиков. Группирует доступы (БД, SSH, API) по проектам.

## 🚀 Особенности
- Автоматическая группировка по проектам
- Шифрование AES-256
- Кроссплатформенный TUI-интерфейс

## 🛠️ Стек
Python 3.10+, cryptography, npyscreen

## ▶️ Запуск (позже)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
python src/main.py