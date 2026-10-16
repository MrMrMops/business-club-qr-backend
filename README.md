# Business Club QR Backend

Backend-сервис для регистрации гостей мероприятия, выдачи персональных QR-пропусков и начисления баллов при check-in.

Проект включает:

- FastAPI API
- Telegram-бот на aiogram
- PostgreSQL
- SQLAlchemy
- Alembic migrations
- HMAC-подписанные QR-пропуска
- распознавание QR-кодов с фотографий через OpenCV
- историю начисления баллов
- защиту от повторного check-in
- Docker / Docker Compose
- автоматические тесты

## Основной сценарий

### Гость

Гость регистрируется в системе и получает:

- имя;
- категорию;
- Telegram ID;
- персональный `pass_id`;
- баланс баллов.

В Telegram-боте гость может использовать:

```text
/qr
```

Бот отправляет персональный QR-пропуск.

```text
/balance
```

Бот показывает текущий баланс.

### Организатор

Организаторы определяются через allowlist Telegram ID:

```env
ORGANIZER_TELEGRAM_IDS=[123456789,987654321]
```

Организатор может отправить боту фотографию QR-кода гостя.

Бот:

1. распознаёт QR через OpenCV;
2. проверяет HMAC-подпись;
3. находит гостя;
4. показывает карточку гостя;
5. показывает текущий баланс;
6. показывает статус check-in;
7. позволяет отметить приход и начислить баллы.

Также доступен ручной fallback:

```text
/check TOKEN
```

Команда:

```text
/id
```

показывает Telegram ID пользователя — это удобно для добавления организаторов в allowlist.

## Check-in

При первом check-in:

- выставляется `checked_in_at`;
- гостю начисляются баллы;
- создаётся запись в истории начислений.

Повторный check-in не начисляет баллы ещё раз.

Операция выполняется атомарно на уровне PostgreSQL, поэтому даже при одновременной попытке check-in одного гостя баллы будут начислены только один раз.

## История начислений

Каждое начисление хранится в таблице `point_transactions`.

Для операции записываются:

- гость;
- Telegram ID организатора;
- количество начисленных баллов;
- причина;
- время начисления.

Для check-in используется причина:

```text
event_checkin
```

## Безопасность QR-пропуска

QR-код не содержит обычный ID гостя.

Для каждого гостя генерируется случайный `pass_id`.

Из него создаётся подписанный токен:

```text
pass_id.HMAC_SIGNATURE
```

Подпись создаётся с помощью HMAC-SHA256 и секрета:

```env
PASS_TOKEN_SECRET=...
```

Изменённый или поддельный токен не проходит проверку.

## Технологии

- Python 3.12
- FastAPI
- PostgreSQL 17
- SQLAlchemy
- asyncpg
- Alembic
- aiogram
- OpenCV
- qrcode
- pytest
- Docker
- Docker Compose

## Запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/MrMrMops/business-club-qr-backend.git
cd business-club-qr-backend
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Заполнить:

```env
DATABASE_URL=postgresql+asyncpg://business_user:business_password@localhost:5432/business_club

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_USERNAME=your_bot_username

PASS_TOKEN_SECRET=your_secret_key

ORGANIZER_TELEGRAM_IDS=[123456789]
CHECKIN_POINTS=100
```

Для генерации секрета, например:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Собрать проект

```bash
docker compose build
```

### 4. Запустить

```bash
docker compose up -d
```

Docker Compose:

- запускает PostgreSQL;
- выполняет Alembic migrations;
- запускает FastAPI;
- запускает Telegram-бота.

Проверить состояние:

```bash
docker compose ps
```

## API

Swagger:

```text
http://localhost:8000/docs
```

### Создание гостя

```http
POST /guests
```

Пример:

```json
{
  "name": "Test Guest",
  "category": "guest",
  "telegram_id": 123456789,
  "username": "test_user"
}
```

Пример ответа:

```json
{
  "id": 1,
  "name": "Test Guest",
  "category": "guest",
  "telegram_id": 123456789,
  "username": "test_user",
  "points": 0
}
```

Повторная регистрация того же Telegram ID возвращает:

```text
409 Conflict
```

## Telegram Bot

Команды:

```text
/qr       — получить персональный QR-пропуск
/balance  — посмотреть баланс
/id       — узнать свой Telegram ID
/check    — ручная проверка токена организатором
```

Обычный пользователь не имеет доступа к функциям организатора.

## Структура данных

### users

Хранит:

- Telegram ID;
- username;
- имя;
- категорию;
- персональный `pass_id`;
- баланс;
- время check-in.

### point_transactions

Хранит историю начислений:

- guest ID;
- organizer Telegram ID;
- amount;
- reason;
- created_at.

## Миграции

Применить все миграции:

```bash
alembic upgrade head
```

Откатить:

```bash
alembic downgrade base
```

И снова применить:

```bash
alembic upgrade head
```

## Локальная установка для разработки и тестов

Для запуска тестов локально создайте виртуальное окружение и установите dev-зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Убедитесь, что PostgreSQL запущен:

```bash
docker compose up -d db
```

## Тесты

Для тестов используется отдельная PostgreSQL database:

```text
business_club_test
```

Создать её:

```bash
docker compose exec db createdb -U business_user business_club_test
```

Запустить тесты:

```bash
pytest -v
```

Тесты проверяют:

- создание гостя;
- уникальность Telegram ID;
- HMAC-подпись пропуска;
- обнаружение подделанного токена;
- поиск гостя по QR-пропуску;
- начисление баллов;
- сохранение истории начислений;
- запрет повторного check-in;
- конкурентный check-in;
- генерацию QR-кода;
- распознавание QR-кода;
- FastAPI endpoints и validation.

## Проверенный сценарий

Проект проверен с чистой PostgreSQL database:

```text
Docker build
→ PostgreSQL
→ Alembic upgrade
→ FastAPI
→ Telegram bot
→ QR scan
→ check-in
→ PointTransaction
→ pytest
```

Повторный check-in не приводит к повторному начислению баллов.