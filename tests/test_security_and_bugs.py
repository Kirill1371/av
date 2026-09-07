import requests
import re
import time
from conftest import BASE_URL


def test_unauthenticated_protected_routes():
    """TC-SEC-001: Защита эндпоинтов — попытка вызова без Bearer токена"""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # POST item без токена
    res_post = requests.post(f"{BASE_URL}/api/1/item", json={"sellerID": 123, "name": "test", "price": 100})
    assert res_post.status_code == 401, f"Ожидался код 401 Unauthorized, получен: {res_post.status_code}"
    assert res_post.json().get("error") == "valid bearer token is required"

    # GET item без токена
    res_get = requests.get(f"{BASE_URL}/api/1/item/{fake_uuid}")
    assert res_get.status_code == 401

    # DELETE item без токена
    res_del = requests.delete(f"{BASE_URL}/api/2/item/{fake_uuid}")
    assert res_del.status_code == 401


def test_idor_delete_other_user_item(registered_user, cleanup_items):
    """TC-DEL-002: Уязвимость IDOR / Broken Access Control в DELETE /api/2/item/:id [BUG-01]"""
    # 1. UserA создаёт объявление
    item_payload = {
        "sellerID": registered_user["id"],
        "name": "Личный ноутбук UserA",
        "price": 80000,
        "statistics": {"likes": 10, "viewCount": 100, "contacts": 5},
    }
    create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    assert create_res.status_code == 200
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        create_res.json().get("status", ""),
        re.I,
    )
    item_id = match.group(0)
    cleanup_items.append(item_id)

    # 2. Регистрируем пользователя UserB
    user_b_name = f"user_b_{int(time.time() * 1000)}"
    requests.post(f"{BASE_URL}/api/1/register", json={"username": user_b_name, "password": "Password123!"})
    auth_b_res = requests.post(f"{BASE_URL}/api/1/autorize", json={"username": user_b_name, "password": "Password123!"})
    token_b = auth_b_res.json()["accessToken"]

    # 3. UserB пытается удалить объявление UserA
    del_res = requests.delete(f"{BASE_URL}/api/2/item/{item_id}", headers={"Authorization": f"Bearer {token_b}"})

    # Должен возвращаться код 403 Forbidden
    msg = f"[BUG-01 CRITICAL] Сервер разрешил UserB удалить объявление UserA! Статус: {del_res.status_code}"
    assert del_res.status_code in [403, 401], msg


def test_zero_values_validation_bug(registered_user, cleanup_items):
    """TC-ITEM-003 / TC-ITEM-005: Валидация нулевых значений (price=0, likes=0) [BUG-02]"""
    payload_zero_price = {
        "sellerID": registered_user["id"],
        "name": "Бесплатный диван",
        "price": 0,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }

    res_price = requests.post(f"{BASE_URL}/api/1/item", json=payload_zero_price, headers=registered_user["headers"])

    # Ожидается успешное создание 200 OK для цены = 0
    msg = f"[BUG-02 HIGH] Сервер отклонил объявление price=0! Статус: {res_price.status_code}, Ответ: {res_price.text}"
    assert res_price.status_code == 200, msg

    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        res_price.json().get("status", ""),
        re.I,
    )
    if match:
        cleanup_items.append(match.group(0))


def test_negative_statistics_bug(registered_user, cleanup_items):
    """TC-ITEM-006: Запрет отрицательных значений в статистике (likes = -10) [BUG-03]"""
    payload_neg_stats = {
        "sellerID": registered_user["id"],
        "name": "Товар с невалидной статистикой",
        "price": 1000,
        "statistics": {"likes": -10, "viewCount": -5, "contacts": -1},
    }

    res = requests.post(f"{BASE_URL}/api/1/item", json=payload_neg_stats, headers=registered_user["headers"])

    # Должна возвращаться ошибка 400 Bad Request
    msg = f"[BUG-03 HIGH] Сервер успешно сохранил объявление с отрицательными лайками! Статус: {res.status_code}"
    assert res.status_code == 400, msg


def test_delete_non_existent_item_response_code(registered_user):
    """TC-DEL-003: Проверка ответа при DELETE ненайденного объекта [BUG-04]"""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
    res = requests.delete(f"{BASE_URL}/api/2/item/{fake_uuid}", headers=registered_user["headers"])

    assert res.status_code == 404
    data = res.json()
    msg = f"[BUG-04 MEDIUM] Несоответствие: HTTP заголовок 404, а статус в JSON '{data.get('status')}' (ожидался '404')"
    assert data.get("status") == "404", msg


def test_statistic_v2_invalid_uuid_status_mismatch(registered_user):
    """TC-STAT-002: Проверка ответа v2 статистики для невалидного UUID [BUG-06]"""
    invalid_uuid = "not-a-uuid"
    res = requests.get(f"{BASE_URL}/api/2/statistic/{invalid_uuid}", headers=registered_user["headers"])

    msg = f"[BUG-06 MEDIUM] v2 статистики при невалидном UUID отдаёт HTTP статус {res.status_code} вместо 400"
    assert res.status_code == 400, msg


def test_string_price_validation_message_bug(registered_user):
    """Некорректный текст ошибки при передаче нечислового значения в price [BUG-08 / API-06]"""
    payload = {
        "sellerID": registered_user["id"],
        "name": "Бесплатный велик",
        "price": "free",
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }
    res = requests.post(f"{BASE_URL}/api/1/item", json=payload, headers=registered_user["headers"])
    assert res.status_code == 400
    status_msg = res.json().get("status", "")
    msg = f"[BUG-08 LOW] Некорректный текст ошибки при некорректном типе price: '{status_msg}'"
    assert status_msg != "не передано тело объявления", msg


def test_stored_xss_in_item_name_bug(registered_user, cleanup_items):
    """Potential Stored XSS — Отсутствие санитизации HTML/JS тегов в name [BUG-09 / API-09]"""
    xss_payload = "<script>alert('XSS')</script>"
    item_payload = {
        "sellerID": registered_user["id"],
        "name": xss_payload,
        "price": 100,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
    }
    create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    assert create_res.status_code == 200
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        create_res.json().get("status", ""),
        re.I,
    )
    item_id = match.group(0)
    cleanup_items.append(item_id)

    get_res = requests.get(f"{BASE_URL}/api/1/item/{item_id}", headers=registered_user["headers"])
    item_name = get_res.json()[0]["name"]
    msg = f"[BUG-09 MEDIUM] Имя объявления содержит несанитизированный HTML/JS сценарий XSS: '{item_name}'"
    assert xss_payload not in item_name, msg


def test_mass_assignment_item_creation_bug(registered_user, cleanup_items):
    """Mass Assignment — Нестрогая схема десериализации DTO [BUG-10 / API-10]"""
    item_payload = {
        "sellerID": registered_user["id"],
        "name": "Товар с лишними полями",
        "price": 500,
        "statistics": {"likes": 1, "viewCount": 1, "contacts": 1},
        "is_admin": True,
        "role": "admin",
    }
    res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    msg = f"[BUG-10 MEDIUM] Сервер принял нестрогий JSON DTO с посторонними полями! Статус: {res.status_code}"
    assert res.status_code == 400, msg
