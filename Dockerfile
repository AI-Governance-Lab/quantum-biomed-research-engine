# =============================================================================
# Quantum BioMed Research Engine — Production Multi-Stage / Hardened Dockerfile
# Runs as non-root user (uid=10001) with persistent /data mount for FDA Part 11
# =============================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR="/data" \
    FDA_LEDGER_DB_PATH="/data/fda_part11_audit_ledger.db" \
    FINOPS_BUDGET_DB_PATH="/data/clinical_study_finops.db" \
    API_BIND_HOST="0.0.0.0" \
    API_BIND_PORT="8000"

WORKDIR /app

RUN groupadd -g 10001 biomed && \
    useradd -u 10001 -g biomed -m -s /usr/sbin/nologin biomed && \
    mkdir -p /data && \
    chown -R biomed:biomed /app /data

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

COPY --chown=biomed:biomed pyproject.toml README.md /app/
COPY --chown=biomed:biomed src /app/src
COPY --chown=biomed:biomed tests /app/tests

USER 10001:10001

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
