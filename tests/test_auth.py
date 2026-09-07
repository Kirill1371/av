import requests
import time
import uuid
from conftest import BASE_URL


def test_register_success():
    """Регистрация нового пользователя с валидными данными"""
    username = f"user_reg_{int(time.time() * 1000)}_{uuid.uuid4().hex[:4]}"
    password = "TestPassword123!"

    response = requests.post(f"{BASE_URL}/api/1/register", json={"username": username, "password": password})

    assert response.status_code == 201, f"Не удалось зарегистрировать пользователя: {response.text}"
    data = response.json()
    assert "id" in data, "В ответе нет поля id"
    assert isinstance(data["id"], int), "Поле id должно быть числом"
    assert data["username"] == username, "Логин в ответе не совпадает с отправленным"


def test_register_duplicate_username(registered_user):
    """Попытка регистрации уже существующего логина"""
    response = requests.post(
        f"{BASE_URL}/api/1/register",
        json={"username": registered_user["username"], "password": "Password123!"},
    )

    assert response.status_code == 409, f"Ожидался код 409 Conflict, получен {response.status_code}"
    data = response.json()
    assert data.get("error") == "username is already registered", f"Неверный текст ошибки: {data}"


def test_register_empty_body():
    """Регистрация с пустым телом запроса"""
    response = requests.post(
        f"{BASE_URL}/api/1/register",
        headers={"Content-Type": "application/json"},
        data="",
    )

    assert response.status_code == 400, f"Ожидался код 400 Bad Request, получен {response.status_code}"


def test_register_boundary_username_length():
    """Проверка допустимых границ длины логина (3 и 64 символа)"""
    username_min = f"u{uuid.uuid4().hex[:2]}"
    username_max = "u" * 50 + uuid.uuid4().hex[:14]
    valid_password = "Password123!"

    res_min = requests.post(f"{BASE_URL}/api/1/register", json={"username": username_min, "password": valid_password})
    assert res_min.status_code == 201, f"Не удалось зарегистрировать логин из 3 символов: {res_min.text}"

    res_max = requests.post(f"{BASE_URL}/api/1/register", json={"username": username_max, "password": valid_password})
    assert res_max.status_code == 201, f"Не удалось зарегистрировать логин из 64 символов: {res_max.text}"


def test_register_invalid_length_username():
    """Проверка невалидной длины логина из 2 символов [BUG-07]"""
    short_username = "ab"
    valid_password = "Password123!"
    response = requests.post(
        f"{BASE_URL}/api/1/register",
        json={"username": short_username, "password": valid_password},
    )

    assert response.status_code == 400, f"Ожидался код 400, получен {response.status_code}"
    data = response.json()
    msg = "[BUG-07] Сервер возвращает 'invalid JSON body' вместо понятной ошибки длины логина"
    assert data.get("error") != "invalid JSON body", msg


def test_autorize_success(registered_user):
    """Успешная авторизация и получение токена"""
    response = requests.post(
        f"{BASE_URL}/api/1/autorize",
        json={"username": registered_user["username"], "password": registered_user["password"]},
    )

    assert response.status_code == 200, f"Ожидался статус 200 OK, получен {response.status_code}"
    data = response.json()
    assert "accessToken" in data, "В ответе нет accessToken"
    assert data.get("tokenType") == "Bearer", "Неверный tokenType"
    assert len(data["accessToken"]) > 10, "Токен пустой"


def test_autorize_wrong_password(registered_user):
    """Авторизация с некорректным паролем"""
    response = requests.post(
        f"{BASE_URL}/api/1/autorize",
        json={"username": registered_user["username"], "password": "WrongPassword123!"},
    )

    assert response.status_code in [400, 401], f"Ожидался код 400/401, получен {response.status_code}"
