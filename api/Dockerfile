FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY api/pyproject.toml ./
COPY api/app ./app
RUN pip install --no-cache-dir .
COPY api/alembic ./alembic
COPY api/alembic.ini api/local.py ./
RUN useradd --create-home gandalf && mkdir /data && chown gandalf:gandalf /data
USER gandalf
ENV GANDALF_LOCAL_DATA=/data GANDALF_HOST=0.0.0.0 GANDALF_ONLINE=1
EXPOSE 8000
CMD ["python", "local.py"]
