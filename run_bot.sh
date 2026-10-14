#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

if [ -z "$BOT_TOKEN" ]; then
  echo "ОШИБКА: Переменная BOT_TOKEN не найдена в .env"
  echo "Добавьте строку: BOT_TOKEN=ваш_токен в файл .env"
  exit 1
fi

echo "Запуск Telegram-бота Базы Знаний..."
python3 bot.py
