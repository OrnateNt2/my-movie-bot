# Используем официальный образ Python 3.11-slim
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код проекта
COPY . .

# Указываем переменные окружения через .env (они будут переданы при запуске)
# Если хотите использовать Docker Secrets, см. предыдущие примеры

# Команда для запуска бота
CMD ["python", "main.py"]
