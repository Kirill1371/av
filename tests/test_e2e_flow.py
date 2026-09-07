import requests
import json
import time
import re
import uuid
import allure
from conftest import BASE_URL


@allure.epic("QA Internship API")
@allure.feature("E2E")
@allure.story("Полный цикл работы с объявлением")
@allure.severity(allure.severity_level.CRITICAL)
def test_e2e_full_lifecycle():
    """
    E2E тест:
    Регистрация -> Авторизация -> Создание объявления -> Чтение -> Статистика -> Удаление -> Проверка 404.
    """
    unique_username = f"e2e_user_{int(time.time() * 1000)}_{uuid.uuid4().hex[:4]}"
    password = "StrongE2EPassword123!"

    # 1. Регистрация
    with allure.step("1. Регистрация нового пользователя"):
        reg_payload = {"username": unique_username, "password": password}
        allure.attach(
            json.dumps(reg_payload, indent=2),
            name="Register Request Payload",
            attachment_type=allure.attachment_type.JSON,
        )

        reg_res = requests.post(
            f"{BASE_URL}/api/1/register",
            json=reg_payload,
            headers={"Content-Type": "application/json"},
        )
        allure.attach(
            f"Status: {reg_res.status_code}\nBody: {reg_res.text}",
            name="Register Response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert reg_res.status_code == 201, f"Не удалось зарегистрировать пользователя: {reg_res.text}"
        user_id = reg_res.json()["id"]

    # 2. Авторизация
    with allure.step("2. Авторизация и получение токена"):
        auth_payload = {"username": unique_username, "password": password}
        allure.attach(
            json.dumps(auth_payload, indent=2),
            name="Auth Request Payload",
            attachment_type=allure.attachment_type.JSON,
        )

        auth_res = requests.post(
            f"{BASE_URL}/api/1/autorize",
            json=auth_payload,
            headers={"Content-Type": "application/json"},
        )
        allure.attach(
            f"Status: {auth_res.status_code}\nBody: {auth_res.text}",
            name="Auth Response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert auth_res.status_code == 200, f"Ошибка авторизации: {auth_res.text}"
        token = auth_res.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 3. Создание объявления
    with allure.step("3. Создание объявления"):
        item_payload = {
            "sellerID": user_id,
            "name": "Игровой монитор 27 дюймов 144 Гц",
            "price": 25000,
            "statistics": {"likes": 5, "viewCount": 80, "contacts": 3},
        }
        allure.attach(
            json.dumps(item_payload, indent=2),
            name="Create Item Payload",
            attachment_type=allure.attachment_type.JSON,
        )

        create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=headers)
        allure.attach(
            f"Status: {create_res.status_code}\nBody: {create_res.text}",
            name="Create Item Response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert create_res.status_code == 200, f"Ошибка создания объявления: {create_res.text}"

        status_str = create_res.json().get("status", "")
        match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", status_str, re.I)
        assert match is not None, f"UUID не найден в статусе: {status_str}"
        item_id = match.group(0)

    # 4. Чтение по ID
    with allure.step("4. Чтение объявления по ID"):
        get_res = requests.get(f"{BASE_URL}/api/1/item/{item_id}", headers=headers)
        allure.attach(
            f"Status: {get_res.status_code}\nBody: {get_res.text}",
            name="Get Item Response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert get_res.status_code == 200, f"Ошибка чтения объявления: {get_res.text}"

        items = get_res.json()
        item = items[0]
        assert item["id"] == item_id
        assert item["name"] == item_payload["name"]
        assert item["price"] == item_payload["price"]

    # 5. Статистика
    with allure.step("5. Запрос статистики v1 и v2"):
        stat1_res = requests.get(f"{BASE_URL}/api/1/statistic/{item_id}", headers=headers)
        assert stat1_res.status_code == 200, f"Ошибка v1 статистики: {stat1_res.text}"
        allure.attach(stat1_res.text, name="Statistic v1 Response", attachment_type=allure.attachment_type.JSON)

        stat2_res = requests.get(f"{BASE_URL}/api/2/statistic/{item_id}", headers=headers)
        assert stat2_res.status_code == 200, f"Ошибка v2 статистики: {stat2_res.text}"
        allure.attach(stat2_res.text, name="Statistic v2 Response", attachment_type=allure.attachment_type.JSON)

        assert stat1_res.json()[0]["likes"] == 5
        assert stat2_res.json()[0]["viewCount"] == 80

    # 6. Удаление
    with allure.step("6. Удаление объявления"):
        del_res = requests.delete(f"{BASE_URL}/api/2/item/{item_id}", headers=headers)
        allure.attach(
            f"Status: {del_res.status_code}", name="Delete Response", attachment_type=allure.attachment_type.TEXT
        )
        assert del_res.status_code == 200, f"Ошибка удаления: {del_res.text}"

    # 7. Проверка 404
    with allure.step("7. Проверка отсутствия объявления после удаления (404)"):
        check_res = requests.get(f"{BASE_URL}/api/1/item/{item_id}", headers=headers)
        allure.attach(
            f"Status: {check_res.status_code}\nBody: {check_res.text}",
            name="Check Deleted Response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert check_res.status_code == 404, f"Ожидался 404 Not Found, получен: {check_res.status_code}"
