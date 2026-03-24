FROM python:3.12-slim-bookworm
WORKDIR /app

# Reliable CA bundle + OpenSSL for aiohttp/discord.py TLS (gateway + voice signalling).
# Coolify/minimal runtimes sometimes missing or stale certs; avoids odd SNI/TLS failures.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates openssl \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
