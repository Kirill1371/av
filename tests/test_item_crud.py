import requests
import re
from conftest import BASE_URL


def test_create_and_get_item(registered_user, cleanup_items):
    """TC-ITEM-001 / TC-GET-001: Создание и последующее чтение объявления по UUID"""
    item_payload = {
        "sellerID": registered_user["id"],
        "name": "Игровой ноутбук ASUS ROG",
        "price": 150000,
        "statistics": {"likes": 12, "viewCount": 250, "contacts": 8},
    }

    # 1. Создание объявления
    create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    assert create_res.status_code == 200, f"Не удалось создать объявление: {create_res.text}"
    status_str = create_res.json().get("status", "")

    # Извлекаем UUID из строки ответа ("Сохранили объявление - <uuid>")
    match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", status_str, re.I)
    assert match is not None, f"UUID не найден в ответе сохранения: {status_str}"
    item_id = match.group(0)
    cleanup_items.append(item_id)

    # 2. Чтение объявления по ID
    get_res = requests.get(f"{BASE_URL}/api/1/item/{item_id}", headers=registered_user["headers"])
    assert get_res.status_code == 200, f"Не удалось получить объявление по ID: {get_res.text}"
    items = get_res.json()
    assert isinstance(items, list) and len(items) == 1, f"Ожидался массив из 1 элемента, получено: {items}"

    item = items[0]
    assert item["id"] == item_id, "UUID объявления не совпадает"
    assert item["name"] == item_payload["name"], "Название объявления не совпадает"
    assert item["price"] == item_payload["price"], "Цена не совпадает"
    assert item["statistics"]["likes"] == 12, "Счётчик лайков не совпадает"


def test_get_seller_items(registered_user, cleanup_items):
    """TC-GET-004: Получение всех объявлений продавца по sellerID"""
    # Создаём объявление
    item_payload = {
        "sellerID": registered_user["id"],
        "name": "Смартфон iPhone 15 Pro",
        "price": 100000,
        "statistics": {"likes": 5, "viewCount": 40, "contacts": 2},
    }
    create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    assert create_res.status_code == 200

    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        create_res.json().get("status", ""),
        re.I,
    )
    if match:
        cleanup_items.append(match.group(0))

    # Запрашиваем список всех товаров продавца
    get_res = requests.get(f"{BASE_URL}/api/1/{registered_user['id']}/item", headers=registered_user["headers"])
    assert get_res.status_code == 200, f"Не удалось получить список объявлений продавца: {get_res.text}"
    seller_items = get_res.json()
    assert isinstance(seller_items, list), "Ответ должен быть массивом"
    assert len(seller_items) >= 1, "В списке продавца должно быть минимум 1 объявление"


def test_delete_item_success(registered_user):
    """TC-DEL-001: Позитивное удаление объявления автором"""
    # 1. Создаём объявление
    item_payload = {
        "sellerID": registered_user["id"],
        "name": "Велосипед Mountain Bike",
        "price": 35000,
        "statistics": {"likes": 1, "viewCount": 10, "contacts": 1},
    }
    create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    assert create_res.status_code == 200
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        create_res.json().get("status", ""),
        re.I,
    )
    item_id = match.group(0)

    # 2. Удаляем объявление
    del_res = requests.delete(f"{BASE_URL}/api/2/item/{item_id}", headers=registered_user["headers"])
    assert del_res.status_code == 200, f"Не удалось удалить объявление: {del_res.text}"

    # 3. Проверяем, что объявление больше не существует (GET отдаёт 404)
    get_res = requests.get(f"{BASE_URL}/api/1/item/{item_id}", headers=registered_user["headers"])
    assert get_res.status_code == 404, f"Ожидался код 404 для удалённого объявления, получен: {get_res.status_code}"


def test_create_item_with_foreign_seller_id(registered_user):
    """TC-ITEM-002: Негативный сценарий — создание объявления с чужим sellerID"""
    foreign_seller_id = 999999
    item_payload = {
        "sellerID": foreign_seller_id,
        "name": "Чужой товар",
        "price": 5000,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }

    response = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])

    assert response.status_code == 400, f"Ожидался код 400, получен: {response.status_code}"
    data = response.json()
    msg = data.get("result", {}).get("message", "")
    assert "sellerID должен совпадать" in msg, f"Некорректный текст ошибки: {data}"


def test_get_non_existent_item(registered_user):
    """TC-GET-002: Негативный сценарий — запрос несуществующего UUID"""
    fake_uuid = "815de268-1221-4835-9a27-ce8242b33857"
    response = requests.get(f"{BASE_URL}/api/1/item/{fake_uuid}", headers=registered_user["headers"])

    assert response.status_code == 404, f"Ожидался код 404, получен: {response.status_code}"


def test_get_invalid_uuid_item(registered_user):
    """TC-GET-003: Негативный сценарий — невалидный формат UUID"""
    invalid_uuid = "not-a-valid-uuid-format"
    response = requests.get(f"{BASE_URL}/api/1/item/{invalid_uuid}", headers=registered_user["headers"])

    assert response.status_code == 400, f"Ожидался код 400, получен: {response.status_code}"
