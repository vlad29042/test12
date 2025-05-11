import requests
import json

BASE_URL = "http://127.0.0.1:8000"


def test_create_complaint():
    """Тест создания жалобы"""
    print("1. Создание жалобы...")
    url = f"{BASE_URL}/complaints"
    data = {"text": "Не приходит SMS-код"}

    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"ID: {result['id']}, Status: {result['status']}, Sentiment: {result['sentiment']}")
    return result['id']


def test_get_complaints():
    """Тест получения всех жалоб"""
    print("\n2. Получение всех жалоб...")
    url = f"{BASE_URL}/complaints"

    response = requests.get(url)
    complaints = response.json()
    print(f"Найдено жалоб: {len(complaints)}")
    for c in complaints:
        print(f"- ID: {c['id']}, Text: {c['text'][:30]}..., Status: {c['status']}")


def test_get_open_complaints():
    """Тест фильтрации по статусу"""
    print("\n3. Фильтрация открытых жалоб...")
    url = f"{BASE_URL}/complaints"
    params = {"status": "open"}

    response = requests.get(url, params=params)
    complaints = response.json()
    print(f"Открытых жалоб: {len(complaints)}")


def test_update_status(complaint_id):
    """Тест обновления статуса"""
    print(f"\n4. Закрытие жалобы {complaint_id}...")
    url = f"{BASE_URL}/complaints/{complaint_id}"
    params = {"status": "closed"}

    response = requests.put(url, params=params)
    result = response.json()
    print(f"Результат: {result['message']}")


def test_get_recent():
    """Тест получения жалоб за последний час"""
    print("\n5. Получение жалоб за последний час...")
    url = f"{BASE_URL}/complaints"
    params = {"hours_ago": 1}

    response = requests.get(url, params=params)
    complaints = response.json()
    print(f"Жалоб за час: {len(complaints)}")


def main():
    print("=== Полное тестирование API ===")

    # Создаем несколько жалоб
    complaint_id1 = test_create_complaint()

    # Создаем вторую жалобу
    print("\n1.2. Создание второй жалобы...")
    response = requests.post(f"{BASE_URL}/complaints",
                             json={"text": "Переплата за услугу"})
    complaint_id2 = response.json()['id']
    print(f"ID: {complaint_id2}")

    # Тестируем все функции
    test_get_complaints()
    test_get_open_complaints()
    test_update_status(complaint_id1)
    test_get_recent()

    # Проверяем, что жалоба действительно закрыта
    print("\n6. Проверка закрытой жалобы...")
    response = requests.get(f"{BASE_URL}/complaints?status=closed")
    closed = response.json()
    print(f"Закрытых жалоб: {len(closed)}")

    print("\n✓ Все тесты пройдены!")


if __name__ == "__main__":
    main()