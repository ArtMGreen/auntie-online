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
# generate latest requirements.txt
uv pip compile pyproject.toml -o requirements.txt
```

```shell
docker build -t yandex-gpt-bot .
```

```shell
docker run --rm -it --env-file .env yandex-gpt-bot
```
