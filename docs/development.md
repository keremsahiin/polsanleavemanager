# Development

> Yerelde çalıştırma, yapılandırma ve doğrulama. Kurallar `docs/conventions.md`, `docs/testing.md`
> ve `docs/security.md`'dedir; bu sayfa yalnız "nasıl"ı anlatır.

## Requirements
- Python 3.14 ve [uv](https://docs.astral.sh/uv/) (`pip install uv` veya resmi kurulum betiği).
- Node.js (yalnız `js-syntax` check adımı için; `node --check`).
- Git Bash (Windows'ta `./scripts/*` betikleri POSIX `sh` ile çalışır).

## First-time setup
```sh
uv sync --locked                        # bağımlılıklar, uv.lock ile birebir
uv run --locked playwright install chromium   # e2e için bir kez (~150 MB)
cp .env.example .env                    # PowerShell: Copy-Item .env.example .env
mkdir -p data                           # PLM_DATABASE_PATH'in klasörü
```

## Configuration
Uygulama ayarlarını yalnız ortam değişkenlerinden okur; `.env` otomatik yüklenmez, komutlara
`uv run --env-file .env …` ile verilir.

| Değişken | Zorunlu | Varsayılan | Anlamı |
|---|---|---|---|
| `PLM_DATABASE_PATH` | evet | — | SQLite dosyasının yolu. Yoksa uygulama başlamaz (çıkış kodu 2). |
| `PLM_HOST` | hayır | `127.0.0.1` | Dinlenecek adres; üretimde ters proxy arkasında loopback kalır. |
| `PLM_PORT` | hayır | `8000` | Dinlenecek port. |

## Database schema
Şemayı yalnız Alembic göçleri değiştirir; uygulama başlarken şemaya dokunmaz ve var olmayan bir
veritabanı dosyasını oluşturmaz.
```sh
uv run --env-file .env alembic upgrade head            # dosyayı oluşturur / en güncel sürüme getirir
uv run --env-file .env alembic revision -m "<açıklama>" # yeni göç (migrations/versions/)
```

## Run the app
```sh
uv run --env-file .env python -m app
```
Tarayıcıda `http://127.0.0.1:8000` açılış sayfasını gösterir. Sağlık sinyalleri:
`/api/health/live` (süreç ayakta) ve `/api/health/ready` (veritabanı erişilebilir ve şema
güncel; değilse 503). Tek süreç, tek worker (ADR 0002); log'lar stdout'a satır başına bir JSON.

## Verify
```sh
./scripts/check --fast   # iç döngü: lint, format, types, boundaries, js-syntax, test, domain-coverage
./scripts/check          # tam sözleşme (+ e2e) — tek kanıt bu
./scripts/residue        # check arkasında süreç bırakmıyor mu (check.conf değişince)
```
