# Auntie Julia Online

## Start

Create `.env` and fill values

Run

```shell
uv sync
source .venv/bin/activate
uv run src/main.py
```

## Run in Docker

```shell
uv sync
```

```shell
docker build -t yandex-gpt-bot .
```

```shell
docker run --rm -it --env-file .env yandex-gpt-bot
```
