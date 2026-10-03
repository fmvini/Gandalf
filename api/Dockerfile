FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY api/pyproject.toml ./
COPY api/app ./app
RUN --mount=type=secret,id=gandalf_build_ca,required=false \
    if [ -f /run/secrets/gandalf_build_ca ]; then \
        PIP_CERT=/run/secrets/gandalf_build_ca pip install --no-cache-dir .; \
    else \
        pip install --no-cache-dir .; \
    fi
COPY api/alembic ./alembic
COPY api/alembic.ini api/local.py api/deploy.py ./
RUN useradd --create-home gandalf && mkdir /data && chown gandalf:gandalf /data
USER gandalf
ENV GANDALF_LOCAL_DATA=/data GANDALF_HOST=0.0.0.0 GANDALF_ONLINE=1
EXPOSE 8000
CMD ["python", "local.py"]
