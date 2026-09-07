import pytest
import requests
import time
import uuid

BASE_URL = "https://qa-internship.avito.com"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def registered_user():
    """
    Создаёт случайного пользователя через /api/1/register
    и получает token через /api/1/autorize.
    """
    unique_username = f"autotest_user_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    password = "StrongPassword123!"

    # Регистрация
    reg_res = requests.post(
        f"{BASE_URL}/api/1/register",
        json={"username": unique_username, "password": password},
        headers={"Content-Type": "application/json"},
    )
    assert reg_res.status_code == 201, f"Не удалось зарегистрировать пользователя: {reg_res.text}"
    user_data = reg_res.json()
    user_id = user_data["id"]

    # Авторизация
    auth_res = requests.post(
        f"{BASE_URL}/api/1/autorize",
        json={"username": unique_username, "password": password},
        headers={"Content-Type": "application/json"},
    )
    assert auth_res.status_code == 200, f"Не удалось авторизоваться: {auth_res.text}"
    auth_data = auth_res.json()
    token = auth_data["accessToken"]

    return {
        "id": user_id,
        "username": unique_username,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    }


@pytest.fixture
def cleanup_items(registered_user):
    """
    Собирает id созданных объявлений и удаляет их после завершения теста.
    """
    item_ids_to_delete = []

    yield item_ids_to_delete

    # Очистка
    for item_id in item_ids_to_delete:
        try:
            requests.delete(f"{BASE_URL}/api/2/item/{item_id}", headers=registered_user["headers"])
        except Exception:
            pass
