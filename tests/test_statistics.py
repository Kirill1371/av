import requests
import re
from conftest import BASE_URL


def test_get_statistics_v1_and_v2_success(registered_user, cleanup_items):
    """TC-STAT-001: Позитивный сценарий получения статистики v1 и v2"""
    item_payload = {
        "sellerID": registered_user["id"],
        "name": "Игровая приставка PlayStation 5",
        "price": 60000,
        "statistics": {"likes": 42, "viewCount": 350, "contacts": 15},
    }

    # Создаём объявление
    create_res = requests.post(f"{BASE_URL}/api/1/item", json=item_payload, headers=registered_user["headers"])
    assert create_res.status_code == 200
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        create_res.json().get("status", ""),
        re.I,
    )
    item_id = match.group(0)
    cleanup_items.append(item_id)

    # 1. Запрашиваем статистику v1
    stat1_res = requests.get(f"{BASE_URL}/api/1/statistic/{item_id}", headers=registered_user["headers"])
    assert stat1_res.status_code == 200, f"Ошибка при запросе статистики v1: {stat1_res.text}"
    stat1_data = stat1_res.json()
    assert isinstance(stat1_data, list) and len(stat1_data) == 1
    assert stat1_data[0]["likes"] == 42
    assert stat1_data[0]["viewCount"] == 350
    assert stat1_data[0]["contacts"] == 15

    # 2. Запрашиваем статистику v2
    stat2_res = requests.get(f"{BASE_URL}/api/2/statistic/{item_id}", headers=registered_user["headers"])
    assert stat2_res.status_code == 200, f"Ошибка при запросе статистики v2: {stat2_res.text}"
    stat2_data = stat2_res.json()
    assert isinstance(stat2_data, list) and len(stat2_data) == 1
    assert stat2_data[0]["likes"] == 42
    assert stat2_data[0]["viewCount"] == 350
    assert stat2_data[0]["contacts"] == 15


def test_statistic_v1_non_existent_item(registered_user):
    """TC-STAT-002: Негативный сценарий статистики v1 для ненайденного UUID"""
    fake_uuid = "815de268-1221-4835-9a27-ce8242b33857"
    response = requests.get(f"{BASE_URL}/api/1/statistic/{fake_uuid}", headers=registered_user["headers"])
    assert response.status_code == 404, f"Ожидался код 404, получен: {response.status_code}"
