```markdown
# Business Club QR Backend

Backend-сервис для начисления бонусных баллов пользователям через одноразовые QR-коды и Telegram-бота.

Пользователь сканирует QR-код, переходит по Telegram deep link и получает указанное количество баллов. Каждый QR-код может быть использован только один раз.

## Возможности

- создание одноразовых QR-кодов;
- генерация QR-кода в формате PNG;
- Telegram deep links;
- автоматическое создание пользователя при первом начислении;
- начисление бонусных баллов;
- просмотр текущего баланса через Telegram;
- защита от повторного использования QR-кода;
- защита от race condition при одновременном использовании одного QR;
- хранение данных в PostgreSQL;
- миграции базы данных через Alembic;
- запуск проекта через Docker Compose;
- автоматические тесты бизнес-логики и HTTP API.

## Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- asyncpg
- Alembic
- aiogram
- Pydantic Settings
- pytest
- pytest-asyncio
- httpx
- Docker
- Docker Compose

## Архитектура

```text
                 ┌─────────────────┐
                 │   Telegram Bot  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Business Logic  │
                 │    Services     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   SQLAlchemy    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   PostgreSQL    │
                 └─────────────────┘

FastAPI ───────► Business Logic
```

## Структура проекта

```text
app/
├── api/
│   └── routes/
│       ├── health.py
│       └── qr.py
│
├── bot/
│   ├── bot.py
│   └── handlers.py
│
├── core/
│   └── config.py
│
├── db/
│   ├── base.py
│   ├── database.py
│   └── models.py
│
├── schemas/
│   └── qr.py
│
├── services/
│   ├── qr_service.py
│   └── qr_image_service.py
│
└── main.py

alembic/
tests/

Dockerfile
docker-compose.yml
requirements.txt
requirements-dev.txt
.env.example
alembic.ini
```

## Основная логика

При создании QR-кода генерируется криптографически случайный token.

Количество начисляемых баллов хранится в базе данных и не передаётся внутри QR-кода, поэтому пользователь не может изменить количество баллов путём изменения ссылки.

QR-код содержит Telegram deep link:

```text
https://t.me/BOT_USERNAME?start=TOKEN
```

После перехода Telegram-бот получает token и вызывает сервис начисления баллов.

Сценарий:

```text
Создание QR
    ↓
Генерация случайного token
    ↓
Сохранение token и points в PostgreSQL
    ↓
Генерация Telegram deep link
    ↓
Пользователь сканирует QR
    ↓
Telegram /start TOKEN
    ↓
Проверка QR
    ↓
Начисление баллов
    ↓
QR помечается использованным
```

## Защита от повторного использования

QR-код может быть использован только один раз.

При использовании выполняется атомарный SQL UPDATE с условием:

```text
used_at IS NULL
```

То есть QR помечается использованным только в том случае, если ранее он не был использован.

Это также защищает от race condition.

Например, если два запроса одновременно пытаются использовать один QR:

```text
Request A ──┐
            ├──► PostgreSQL
Request B ──┘
```

только один запрос сможет изменить строку:

```text
Request A → QR успешно использован → +100 points
Request B → QR уже использован
```

Итоговый баланс:

```text
100
```

а не:

```text
200
```

Эта ситуация отдельно проверяется автоматическим concurrency-тестом.

## Модели базы данных

### User

```text
id
telegram_id
username
points
created_at
```

`telegram_id` является уникальным.

Для `points` действует ограничение:

```text
points >= 0
```

### QRCode

```text
id
token
points
used_by_user_id
created_at
used_at
```

`token` является уникальным.

Для количества начисляемых баллов действует ограничение:

```text
points > 0
```

`used_by_user_id` связан с таблицей пользователей через Foreign Key.

## Environment variables

Создайте файл `.env` на основе `.env.example`.

Пример:

```env
DATABASE_URL=postgresql+asyncpg://business_user:business_password@localhost:5432/business_club

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_USERNAME=your_bot_username
```

Настоящий `.env` не должен попадать в Git.

## Запуск через Docker Compose

Для запуска необходим Docker.

Соберите и запустите проект:

```bash
docker compose up --build
```

Docker Compose запускает:

```text
PostgreSQL
Alembic migrations
FastAPI
Telegram Bot
```

Миграции выполняются автоматически перед запуском API и бота.

После запуска FastAPI доступен по адресу:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Остановить проект:

```bash
docker compose down
```

Запустить в фоне:

```bash
docker compose up -d
```

Посмотреть состояние сервисов:

```bash
docker compose ps
```

Посмотреть логи:

```bash
docker compose logs -f
```

## API

### Health check

```http
GET /
```

Пример ответа:

```json
{
  "status": "ok"
}
```

### Database check

```http
GET /db-check
```

Пример ответа:

```json
{
  "database": "ok",
  "result": 1
}
```

### Создание QR-token

```http
POST /qr?points=100
```

Пример ответа:

```json
{
  "id": 1,
  "token": "generated_token",
  "points": 100
}
```

Параметр `points` должен быть больше нуля.

Попытка отправить:

```text
points = -100
```

будет отклонена FastAPI validation.

### Создание PNG QR-кода

```http
POST /qr/image?points=100
```

Endpoint создаёт QR в базе данных и возвращает PNG-изображение.

Внутри изображения находится Telegram deep link:

```text
https://t.me/BOT_USERNAME?start=TOKEN
```

### Использование QR

```http
POST /qr/{token}/redeem
```

Пример body:

```json
{
  "telegram_id": 123456789,
  "username": "example"
}
```

Успешный ответ:

```json
{
  "qr_id": 1,
  "points_added": 100,
  "balance": 100
}
```

Если QR уже использован:

```http
409 Conflict
```

```json
{
  "detail": "QR code already used"
}
```

Если token не существует:

```http
404 Not Found
```

```json
{
  "detail": "QR code not found"
}
```

## Telegram Bot

Основные команды:

```text
/start
/balance
```

Обычный `/start` выводит приветственное сообщение.

Команда:

```text
/balance
```

показывает текущий баланс пользователя.

При переходе по deep link вида:

```text
https://t.me/BOT_USERNAME?start=TOKEN
```

бот получает token и пытается активировать QR-код.

При успешном начислении пользователь получает сообщение:

```text
Начислено: 100 баллов.
Текущий баланс: 100.
```

При повторном использовании:

```text
Этот QR-код уже был использован.
```

## Миграции

Для управления схемой базы данных используется Alembic.

Применить все миграции вручную:

```bash
alembic upgrade head
```

Создать новую миграцию:

```bash
alembic revision --autogenerate -m "migration name"
```

При запуске через Docker Compose миграции применяются автоматически.

## Тесты

Для тестов используется отдельная база:

```text
business_club_test
```

Если она ещё не создана и PostgreSQL запущен через Docker Compose:

```bash
docker compose exec db createdb -U business_user business_club_test
```

Установить зависимости для разработки:

```bash
pip install -r requirements-dev.txt
```

Запустить все тесты:

```bash
pytest -v
```

Проект содержит тесты:

- создания QR;
- сохранения QR в PostgreSQL;
- первого использования QR;
- повторного использования QR;
- корректного баланса пользователя;
- одновременного использования QR двумя запросами;
- создания QR через HTTP API;
- валидации количества баллов;
- HTTP 404 для неизвестного QR;
- HTTP 409 для уже использованного QR;
- генерации PNG QR-кода.

Особое внимание уделено concurrency-тесту, который запускает два одновременных запроса на использование одного QR и проверяет, что баллы начисляются только один раз.

## Security

Реализованы:

- криптографически случайные QR tokens;
- уникальность token на уровне PostgreSQL;
- атомарное использование QR;
- защита от повторного начисления;
- Foreign Key между QR и пользователем;
- database constraints для количества баллов;
- хранение секретов через environment variables;
- `.env` исключён из Git.

В текущей версии endpoints создания QR не защищены административной авторизацией.

Для production-использования необходимо добавить authentication/authorization для endpoints:

```text
POST /qr
POST /qr/image
```

чтобы создавать QR-коды могли только администраторы.

## Запуск проекта с нуля

```bash
git clone <repository-url>

cd business-club-qr-backend

cp .env.example .env
```

Заполните:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_USERNAME
```

Затем:

```bash
docker compose up --build
```

После запуска:

```text
Swagger:
http://localhost:8000/docs
```

Telegram-бот также начинает polling автоматически.

## Возможные дальнейшие улучшения

- авторизация администратора;
- роли пользователей;
- отдельная административная панель;
- срок действия QR-кодов;
- история начислений;
- возможность отмены начисления;
- rate limiting;
- structured logging;
- CI/CD;
- автоматический запуск тестов через GitHub Actions;
- production deployment.

## License

Project created as a backend test assignment.
```