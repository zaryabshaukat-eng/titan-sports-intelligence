FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system titan && adduser --system --ingroup titan titan

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic
RUN python -m pip install --upgrade pip && python -m pip install .

USER titan

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
