FROM python:3.11

WORKDIR /app

RUN pip install poetry

RUN poetry config virtualenvs.create false

ENV PATH="/root/.local/bin:${PATH}"

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-root --no-interaction --no-ansi

COPY . .

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
