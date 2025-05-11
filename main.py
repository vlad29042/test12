from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import os
from dotenv import load_dotenv
from database import init_db, create_complaint, get_complaints, update_complaint_status

# Загружаем переменные
load_dotenv()

app = FastAPI()
init_db()


# Модели
class ComplaintRequest(BaseModel):
    text: str


class ComplaintResponse(BaseModel):
    id: int
    status: str
    sentiment: str
    category: str


# API для тональности
SENTIMENT_API_KEY = os.getenv("SENTIMENT_API_KEY")


def analyze_sentiment(text: str) -> str:
    """Анализ тональности через APILayer с отладкой"""
    print(f"Начало анализа тональности для: {text}")
    print(f"API ключ: {'найден' if SENTIMENT_API_KEY else 'НЕ найден'}")

    if not SENTIMENT_API_KEY:
        print("SENTIMENT_API_KEY не установлен в .env")
        return "unknown"

    try:
        headers = {"apikey": SENTIMENT_API_KEY}
        url = "https://api.apilayer.com/sentiment/predict"

        print(f"Отправка запроса на {url}")
        print(f"Headers: {headers}")
        print(f"Data: {text}")

        response = requests.post(url, headers=headers, data=text, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            sentiment = result.get("sentiment", "").lower()
            print(f"Parsed sentiment: {sentiment}")

            # Преобразуем в нужный формат
            if "positive" in sentiment:
                return "positive"
            elif "negative" in sentiment:
                return "negative"
            else:
                return "neutral"
        else:
            print(f"APILayer error: {response.status_code} - {response.text}")
            return "unknown"
    except Exception as e:
        print(f"Exception в analyze_sentiment: {e}")
        import traceback
        traceback.print_exc()
        return "unknown"


@app.post("/complaints", response_model=ComplaintResponse)
async def create_complaint_endpoint(complaint: ComplaintRequest):
    """Создание жалобы"""
    try:
        print(f"\nПолучен POST-запрос: {complaint.text}")
        sentiment = analyze_sentiment(complaint.text)
        print(f"Определен sentiment: {sentiment}")

        complaint_id = create_complaint(complaint.text, sentiment)
        print(f"Создана жалоба с ID: {complaint_id}")

        # Отправляем webhook в n8n
        webhook_url = os.getenv("N8N_WEBHOOK_URL")
        if webhook_url:
            webhook_data = {
                "id": complaint_id,
                "text": complaint.text,
                "sentiment": sentiment,
                "status": "open",
                "category": "другое"
            }
            try:
                print(f"Отправка webhook на {webhook_url}")
                requests.post(webhook_url, json=webhook_data, timeout=5)
                print("Webhook отправлен успешно")
            except Exception as e:
                print(f"Ошибка при отправке webhook: {e}")
                # Продолжаем работу даже если webhook не отправился

        return ComplaintResponse(
            id=complaint_id,
            status="open",
            sentiment=sentiment,
            category="другое"
        )
    except Exception as e:
        print(f"Exception в create_complaint_endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/complaints")
async def get_complaints_endpoint(
        status: Optional[str] = None,
        hours_ago: Optional[int] = None
):
    """Получение жалоб с фильтрами"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if hours_ago:
            from datetime import datetime, timedelta
            filters["since"] = datetime.now() - timedelta(hours=hours_ago)

        return get_complaints(filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/complaints/{complaint_id}")
async def update_complaint_endpoint(complaint_id: int, status: Optional[str] = None, category: Optional[str] = None):
    """Обновление статуса и/или категории жалобы"""
    try:
        if not status and not category:
            raise HTTPException(status_code=400, detail="Provide either status or category")

        if status:
            success = update_complaint_status(complaint_id, status)
            if not success:
                raise HTTPException(status_code=404, detail="Complaint not found")

        if category:
            # Импортируем функцию из database.py
            from database import update_complaint_category
            success = update_complaint_category(complaint_id, category)
            if not success:
                raise HTTPException(status_code=404, detail="Complaint not found")

        return {"message": "Complaint updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Простая проверка
@app.get("/")
async def root():
    return {"message": "API ready"}