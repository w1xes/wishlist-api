# Wishlist API

FastAPI-застосунок для списку бажань. SQLAlchemy зберігає записи в Postgres, Redis використовується для перевірки готовності. У цьому репозиторії лежить і `compose.yaml`, який піднімає весь стек: Postgres, Redis, API та UI (код UI знаходиться в окремому репозиторії `wishlist-ui`).

## Що є в репозиторії

| Шлях | Призначення |
|---|---|
| `app/` | код API (`main.py`, `db.py`, `init_db.py`) |
| `tests/` | тести (pytest), потребують Postgres і Redis |
| `Dockerfile`, `.dockerignore` | образ API |
| `compose.yaml` | повний стек і профіль `dev` |
| `.env.example` | шаблон змінних середовища (без реальних паролів) |
| `.github/workflows/` | CI |
| `docs/` | документація; [docs/containers.md](docs/containers.md) описує образи, стек, діагностику і CI-публікацію |

## Запуск усього стеку

Потрібні Docker з Compose v2 і Git. Код UI Compose бере з публічного репозиторію `wishlist-ui` (гілка `main`), тож достатньо клонувати лише цей репозиторій. Для першого запуску потрібен інтернет.

```bash
git clone https://github.com/w1xes/wishlist-api.git
cd wishlist-api
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
```

У `.env` впишіть власний пароль після `POSTGRES_PASSWORD=` (наприклад, результат `openssl rand -hex 16`). Решту змінних можна залишити як є. Без пароля Compose не стартує: змінна `POSTGRES_PASSWORD` обов'язкова, значення за замовчуванням немає, а в `.env.example` вона порожня.

Запуск однією командою:

```bash
docker compose up -d --build --wait
```

`--build` збирає образи API та UI, `--wait` повертає керування, коли всі чотири сервіси мають статус `healthy`. Порядок старту: Postgres і Redis, потім API, потім UI.

| Що | Адреса |
|---|---|
| UI | <http://localhost:8081> |
| API, Swagger | <http://localhost:8000/docs> |
| Перевірка API | <http://localhost:8000/health>, <http://localhost:8000/ready> |

Назовні відкриті лише порти UI і API, обидва на `127.0.0.1`. Postgres і Redis доступні тільки всередині мережі Compose.

Корисні команди:

```bash
docker compose ps                # стан і health сервісів
docker compose logs -f api       # логи API
docker compose down              # зупинити і видалити контейнери, дані Postgres залишаються
docker compose down -v           # те саме і видалити том з даними Postgres
```

Дані Postgres лежать в іменованому томі `wishlist_pgdata`. Після `down` записи залишаються, після `down -v` база створюється наново і порожня. Таблиці API створює сам при старті.

Пароль Postgres застосовується лише при першій ініціалізації тому. Якщо змінити `POSTGRES_PASSWORD` в `.env` пізніше, API не зможе підключитися, доки не виконано `docker compose down -v`.

## Змінні `.env`

| Змінна | Значення за замовчуванням | Призначення |
|---|---|---|
| `POSTGRES_PASSWORD` | немає, обов'язкова | пароль Postgres і API |
| `API_PORT` | `8000` | порт API на хості |
| `UI_PORT` | `8081` | порт UI на хості |
| `VITE_API_BASE` | `http://localhost:<API_PORT>` | адреса API, яку бачить браузер |
| `UI_ORIGIN` | `http://localhost:<UI_PORT>,http://127.0.0.1:<UI_PORT>` | дозволені origin для CORS, через кому |
| `UI_CONTEXT` | git-контекст `wishlist-ui`, гілка `main` | звідки збирати UI |

Дві змінні потребують уваги:

- `VITE_API_BASE` Vite вшиває в JavaScript під час збирання образу UI, у контейнер вона не передається. Браузер викликає API з хоста, тому адреса має вигляд `http://localhost:<порт>`, а не `http://api:8000`. За замовчуванням вона сама слідує за `API_PORT`. Після зміни виконайте `docker compose up -d --build`.
- `UI_ORIGIN` має містити адресу, за якою відкрито UI, інакше браузер заблокує запити через CORS. За замовчуванням вона слідує за `UI_PORT`.

Щоб зібрати UI з локального клону (наприклад, перевірити ще не злиті зміни), задайте `UI_CONTEXT=../wishlist-ui` у `.env`.

## Режим розробки (профіль `dev`)

Профіль `dev` додає два сервіси, які не заважають основному стеку (інші порти, спільні Postgres і Redis):

| Сервіс | Адреса | Як працює |
|---|---|---|
| `api-dev` | <http://localhost:8100> | той самий Dockerfile, `uvicorn --reload`, `develop.watch` |
| `ui-dev` | <http://localhost:5174> | образ `node:24-alpine`, сирці UI змонтовані з хоста, Vite dev server |

```bash
docker compose --profile dev up -d --build --wait
docker compose --profile dev watch --no-up      # окремий термінал, залишити запущеним
```

- Зміни в `app/` `docker compose watch` копіює (`sync`) у працюючий контейнер, `uvicorn --reload` перезапускає процес. Образ не перезбирається.
- Зміна `requirements.txt` запускає `rebuild`: образ збирається заново, контейнер `api-dev` замінюється.
- Код UI береться з локального клону в теці `UI_DEV_PATH` (за замовчуванням `../wishlist-ui`, клон треба зробити поруч) через bind mount, Vite підхоплює зміни без збирання. `CHOKIDAR_USEPOLLING` увімкнено, бо bind mount з Windows і macOS не передає події файлової системи.
- Поверх `/app/node_modules` змонтовано окремий том `ui_dev_node_modules`. Через це `node_modules` з хоста (його може не бути або він зібраний для Windows) не підміняє пакунки, які `npm ci` встановив у контейнері для Linux. Текою на хості контейнер не користується, пакунки живуть у томі. Після зміни `package-lock.json` перезапустіть `ui-dev`: `docker compose --profile dev up -d --force-recreate ui-dev`.
- Адреси dev-режиму задаються змінними `UI_DEV_PATH`, `API_DEV_PORT`, `UI_DEV_PORT`, `VITE_DEV_API_BASE`, `UI_DEV_ORIGIN` (значення в `.env.example`).

Зупинка: `docker compose --profile dev down` (додайте `-v`, щоб видалити і дані Postgres, і том `ui_dev_node_modules`).

## Збирання лише образу API

```bash
docker build -t wishlist-api:local .
docker run --rm -p 8000:8000 \
  -e POSTGRES_HOST=host.docker.internal -e POSTGRES_PASSWORD=... \
  -e REDIS_URL=redis://host.docker.internal:6379/0 wishlist-api:local
```

Образ не містить конфігурації: хост бази, пароль, адреса Redis і дозволені origin передаються змінними середовища (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `REDIS_URL`, `UI_ORIGIN`). Процес запускається від користувача `app` (не root) і слухає `0.0.0.0:8000`.

## Ендпоїнти

- `GET /health` перевіряє лише доступність самого API.
- `GET /ready` перевіряє зв'язок із Postgres і Redis і повертає 503, якщо одного з них немає. Саме його використовує healthcheck у Compose.
- `GET /items` повертає список бажань, `POST /items` додає бажання з полем `title`, `DELETE /items/{id}` видаляє запис.

Документація Swagger: `/docs`.

## Тести та лінтер

Тестам потрібні Postgres і Redis та змінна `POSTGRES_PASSWORD`. CI запускає їх як service containers, локально вони мають слухати `127.0.0.1:5432` і `127.0.0.1:6379`. Порти Postgres і Redis зі `compose.yaml` на хост не відкриваються навмисно.

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

Правила лінтера: `E,F,I,UP`, довжина рядка 100 (`pyproject.toml`).
