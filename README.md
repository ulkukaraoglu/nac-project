# NAC Staj Projesi (Local Dev İskelet)

Bu repo; `freeradius`, `postgres`, `redis` ve `api` servislerinden oluşan local geliştirme iskeletini içerir.

## Gereksinimler

- Docker Desktop (veya Docker Engine)
- Docker Compose (tercihen `docker-compose` ya da `docker compose`)

## Kurulum

1. `.env.example` dosyasını `.env` olarak kopyalayın:

   - Windows / PowerShell:
     - `Copy-Item .env.example .env`
   - Alternatif:
     - `.env.example` içeriğini `.env` dosyasına kopyalayın

2. `.env` içindeki `POSTGRES_PASSWORD` gibi değerleri kendi local ortamınıza göre güncelleyin.

## Çalıştırma

Proje kök dizininde:

- `docker-compose up -d`

İşlerin ayağa kalktığını doğrulamak için:

- `docker-compose ps`
- `docker-compose logs -f api`
- API health kontrolü:
  - `http://localhost:8000/healthz`

## Durdurma

- `docker-compose down`

