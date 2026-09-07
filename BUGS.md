# Найдено багов и дефектов в API (qa-internship)

Список дефектов, выявленных при тестировании сервиса объявлений `https://qa-internship.avito.com`.

---

### BUG-01 [CRITICAL]: Уязвимость IDOR при удалении объявлений
- **Компонент**: `DELETE /api/2/item/:id`
- **Тест**: `tests/test_security_and_bugs.py::test_idor_delete_other_user_item`
- **Шаги воспроизведения**:
  1. Зарегистрировать и авторизовать Пользователя А, получить `TokenA`.
  2. Создать объявление под Пользователем А, получить `itemId`.
  3. Зарегистрировать и авторизовать Пользователя Б, получить `TokenB`.
  4. Отправить `DELETE /api/2/item/{itemId}` с заголовком `Authorization: Bearer TokenB`.
- **Фактический результат**: HTTP 200 OK. Объявление Пользователя А успешно удаляется чужим токеном.
- **Ожидаемый результат**: HTTP 403 Forbidden. Пользователь может удалять только свои объявления.

---

### BUG-02 [HIGH]: Ошибка валидации нулевых значений (price = 0, likes = 0)
- **Компонент**: `POST /api/1/item`
- **Тест**: `tests/test_security_and_bugs.py::test_zero_values_validation_bug`
- **Шаги воспроизведения**:
  1. Отправить `POST /api/1/item` с `"price": 0` или нулевой статистикой (`likes: 0`).
- **Фактический результат**: HTTP 400 Bad Request, `"message": "поле price обязательно"`.
- **Ожидаемый результат**: HTTP 200 OK. Число 0 является валидным значением цены/счетчиков.

---

### BUG-03 [HIGH]: Сохранение отрицательных значений в статистике
- **Компонент**: `POST /api/1/item`
- **Тест**: `tests/test_security_and_bugs.py::test_negative_statistics_bug`
- **Шаги воспроизведения**:
  1. Отправить `POST /api/1/item` с `"statistics": {"likes": -10, "viewCount": -5, "contacts": -1}`.
- **Фактический результат**: HTTP 200 OK. Объявление успешно сохраняется.
- **Ожидаемый результат**: HTTP 400 Bad Request. Значения счетчиков не могут быть отрицательными.

---

### BUG-04 [MEDIUM]: Несоответствие HTTP статуса (404) и поля status ("500") при удалении несуществующего объекта
- **Компонент**: `DELETE /api/2/item/:id`
- **Тест**: `tests/test_security_and_bugs.py::test_delete_non_existent_item_response_code`
- **Шаги воспроизведения**:
  1. Выполнить `DELETE /api/2/item/{fake_uuid}`.
- **Фактический результат**: В заголовках возвращается HTTP 404, но в JSON тела статус `"500"`.
- **Ожидаемый результат**: HTTP 404 и статус `"404"` в теле ответа.

---

### BUG-05 [MEDIUM]: Несоответствие регистра названия поля sellerID при создании и получении
- **Компонент**: `POST /api/1/item` и `GET /api/1/item/:id`
- **Тест**: `tests/test_item_crud.py::test_create_and_get_item`
- **Шаги воспроизведения**:
  1. Создать объявление с полем `"sellerID": 123`.
  2. Запросить объявление по ID.
- **Фактический результат**: В теле GET возвращается поле `"sellerId"` с маленькой буквой d.
- **Ожидаемый результат**: Единый регистр наименования полей в контракте API (`sellerID`).

---

### BUG-06 [MEDIUM]: Рассогласование кода ответа при невалидном UUID в v2 статистики
- **Компонент**: `GET /api/2/statistic/:id`
- **Тест**: `tests/test_security_and_bugs.py::test_statistic_v2_invalid_uuid_status_mismatch`
- **Шаги воспроизведения**:
  1. Запросить `GET /api/2/statistic/invalid-uuid`.
- **Фактический результат**: Возвращает HTTP status 404, хотя в теле указан статус `"400"`.
- **Ожидаемый результат**: HTTP status 400 Bad Request.

---

### BUG-07 [LOW]: Ошибка "invalid JSON body" при слишком коротком логине
- **Компонент**: `POST /api/1/register`
- **Тест**: `tests/test_auth.py::test_register_invalid_length_username`
- **Шаги воспроизведения**:
  1. Отправить `POST /api/1/register` с логином из 2 символов: `{"username": "ab", "password": "Password123!"}`.
- **Фактический результат**: HTTP 400 с текстом `"error": "invalid JSON body"`.
- **Ожидаемый результат**: Сообщение с понятным описанием ошибки длины логина.

---

### BUG-08 [LOW]: Некорректное сообщение ошибки при нечисловой цене
- **Компонент**: `POST /api/1/item`
- **Тест**: `tests/test_security_and_bugs.py::test_string_price_validation_message_bug`
- **Шаги воспроизведения**:
  1. Отправить `POST /api/1/item` с `"price": "free"`.
- **Фактический результат**: HTTP 400 с текстом `"status": "не передано тело объявления"`.
- **Ожидаемый результат**: Понятное сообщение об ошибке типа данных поля `price`.

---

### BUG-09 [MEDIUM]: Отсутствие фильтрации/экранирования HTML-тегов в названии (Stored XSS)
- **Компонент**: `POST /api/1/item`, `GET /api/1/item/:id`
- **Тест**: `tests/test_security_and_bugs.py::test_stored_xss_in_item_name_bug`
- **Шаги воспроизведения**:
  1. Создать объявление с `"name": "<script>alert('XSS')</script>"`.
  2. Запросить этот объект по ID.
- **Фактический результат**: В названии возвращается сырой скриптовый тег.
- **Ожидаемый результат**: Экранирование или очистка HTML-тегов при сохранении/выгрузке.

---

### BUG-10 [MEDIUM]: Прием нестрогих полей в JSON (Mass Assignment)
- **Компонент**: `POST /api/1/item`
- **Тест**: `tests/test_security_and_bugs.py::test_mass_assignment_item_creation_bug`
- **Шаги воспроизведения**:
  1. Отправить `POST /api/1/item` с дополнительными полями `"is_admin": true`.
- **Фактический результат**: HTTP 200 OK. Сервер игнорирует нестрогость схемы DTO.
- **Ожидаемый результат**: HTTP 400 Bad Request при нарушении схемы входных данных.
