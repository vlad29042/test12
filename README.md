# Система обработки жалоб клиентов

Автоматизированная система для обработки и категоризации жалоб клиентов с интеграцией API и n8n.

## Функционал

1. **API для приема жалоб** - FastAPI backend
2. **Анализ тональности** - через Sentiment Analysis by APILayer
3. **AI категоризация** - через OpenAI GPT-3.5
4. **Автоматизация n8n** - для обработки и уведомлений
   - Telegram уведомления для технических жалоб
   - Google Sheets для жалоб об оплате
   - Автоматическое закрытие обработанных жалоб

## Архитектура

```
Клиент → FastAPI (Sentiment Analysis) → Webhook
                                          ↓
                                     n8n Workflow
                                          ↓
                                  Respond to Webhook
                                          ↓
                                     Edit Fields
                                          ↓
                          ┌─── AI Agent (OpenAI GPT-3.5) ───┐
                          │     определение категории       │
                          └──────────────┬──────────────────┘
                                         ↓
                              Structured Output Parser
                                         ↓
                                    Edit Fields1
                                         ↓
                             HTTP Request (update category)
                                         ↓
                              Switch (техническая/оплата)
                                         ↓
              ┌──────────────────────────┴──────────────────────────┐
              │                                                     │
    Route: техническая                                    Route: оплата
              ↓                                                     ↓
        Telegram Bot                                          Google Sheets
              ↓                                                     ↓
    HTTP Request (close)                                   HTTP Request (close)
              │                                                     │
              └──────────────────┐         ┌──────────────────────┘
                                 ↓         ↓
                              Fallback → Stop and Error
```

### Детали реализации workflow

1. **Webhook** - получает данные от FastAPI после создания жалобы
2. **Respond to Webhook** - отправляет подтверждение о получении
3. **Edit Fields** - извлекает необходимые поля из webhook
4. **AI Agent + Structured Output Parser** - определяет категорию жалобы через OpenAI
5. **HTTP Request** - обновляет категорию в базе данных
6. **Switch** - маршрутизирует по категориям:
   - **Технические** → Telegram Bot → Закрытие жалобы
   - **Оплата** → Google Sheets → Закрытие жалобы
   - **Fallback** → Stop and Error

## Установка

### 1. Backend API

```bash
# Клонирование репозитория
git clone <repository-url>
cd TestP

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
cp .env.example .env
```

### 2. Настройка .env

```env
# Sentiment Analysis API (APILayer)
SENTIMENT_API_KEY=your_sentiment_api_key

# n8n webhook URL
N8N_WEBHOOK_URL=https://your-n8n-domain.com/webhook/complaint-categorize

# Настройки сервера
HOST=127.0.0.1
PORT=8000
```

### 3. Запуск сервера

```bash
# Запуск с ngrok для внешнего доступа
ngrok http 8000

# В другом терминале
uvicorn main:app --reload
```

### 4. n8n Workflow

![n8n Workflow](docs/n8n-workflow-screenshot.png)

Импортируйте workflow из файла `n8n-workflow.json` или создайте вручную:

1. **Webhook Node** - прием данных от backend
2. **Respond to Webhook** - подтверждение получения  
3. **Edit Fields Node** - извлечение данных из webhook
4. **AI Agent + Structured Output Parser** - категоризация через OpenAI
5. **HTTP Request Node** - обновление категории в БД
6. **Switch Node** - маршрутизация по категориям
7. **Telegram Node** - уведомления для технических
8. **Google Sheets Node** - запись для оплаты
9. **HTTP Request Nodes** - закрытие жалоб после обработки

## API Эндпоинты

### POST /complaints
Создание новой жалобы

```bash
curl -X POST "http://localhost:8000/complaints" \
  -H "Content-Type: application/json" \
  -d '{"text": "Не приходит SMS-код"}'
```

Ответ:
```json
{
  "id": 1,
  "status": "open",
  "sentiment": "negative",
  "category": "другое"
}
```

### GET /complaints
Получение списка жалоб

```bash
# Все жалобы
curl "http://localhost:8000/complaints"

# Только открытые
curl "http://localhost:8000/complaints?status=open"

# За последний час
curl "http://localhost:8000/complaints?hours_ago=1"
```

### PUT /complaints/{id}
Обновление жалобы

```bash
# Изменить статус
curl -X PUT "http://localhost:8000/complaints/1?status=closed"

# Изменить категорию
curl -X PUT "http://localhost:8000/complaints/1?category=техническая"
```

## Настройка внешних сервисов

### Sentiment Analysis API
1. Зарегистрируйтесь на [APILayer](https://apilayer.com/marketplace/sentiment-api)
2. Получите API ключ
3. Добавьте в .env: `SENTIMENT_API_KEY=your_key`

### OpenAI API
1. Получите ключ на [OpenAI](https://platform.openai.com/api-keys)
2. Добавьте в n8n credentials

### Telegram Bot
1. Создайте бота через @BotFather
2. Получите токен бота
3. Добавьте в n8n Telegram node

### Google Sheets
1. Создайте проект в Google Cloud Console
2. Включите Google Sheets API и Google Drive API
3. Создайте OAuth 2.0 credentials
4. Настройте в n8n

## Структура проекта

```
TestP/
├── main.py              # FastAPI приложение
├── database.py          # SQLite операции
├── test_api.py         # Тесты API
├── .env.example        # Пример настроек
├── requirements.txt    # Зависимости
├── complaints.db       # База данных
└── README.md          # Документация
```

## Тестирование

```bash
# Запуск тестов
python test_api.py

# Создание тестовой жалобы
curl -X POST "http://localhost:8000/complaints" \
  -H "Content-Type: application/json" \
  -d '{"text": "Тестовая жалоба"}'
```

## Особенности реализации

1. **Анализ тональности** происходит сразу при создании жалобы
2. **Категоризация** выполняется в n8n через OpenAI
3. **Обработка** зависит от категории:
   - Технические → Telegram
   - Оплата → Google Sheets
   - Другое → только закрытие
4. **Все жалобы** автоматически закрываются после обработки

## Примечания

- API ключ для Sentiment Analysis может возвращать 403 ошибку, тогда устанавливается sentiment: "unknown"
- Google Sheets требует OAuth настройки и может потребовать добавления тестовых пользователей
- n8n workflow должен иметь доступ к backend API (используйте ngrok для локальной разработки)

## Лицензия

MIT