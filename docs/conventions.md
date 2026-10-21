# Conventions

> Yalnız gerçek kurallar: her kural ya araçla zorlanır (tercih edilen) ya da review'da kontrol edilir.

## Language
<!-- Set at bootstrap (step 0) and mirrored in AGENTS.md. Changing it later is allowed — edit both
     places; existing documents are not translated retroactively. -->
- Chat language (interviews, sessions): Turkish (`tr`)
- Document language (docs/, specs, plans, ADRs, review and verify reports): Turkish (`tr`)
- Always English (protocol, not prose): ANEW core files, template headings and field labels,
  `Status:` values (Draft / Approved / In progress / Shipped), `Approved by / on:`, `Source:`.
- Code identifiers, branch names, commit messages: English. Kod yorumları ve docstring'ler de
  İngilizce. Kullanıcı arayüzü metinleri ve API hata mesajlarının kullanıcıya dönük `title`/`detail`
  alanları Türkçe. Türkçe terim ↔ kod adı eşlemesi: `docs/domain.md`.
- Agent messages (handoff summaries, refusals, `Next:` lines): chat language; command names, file
  paths and protocol fields verbatim.

## Language & framework versions
- Python **3.14** (`requires-python = ">=3.14,<3.15"`); paket yönetimi **uv**, sürümler `uv.lock`
  ile sabit. Komutlar her zaman `uv run --locked …` ile çalışır.
- FastAPI + uvicorn (tek worker, ADR 0002), SQLAlchemy 2.x (senkron ORM) + Alembic, SQLite 3.
- Frontend: saf HTML/CSS/JS, ES modülleri, build adımı yok; hedef tarayıcılar güncel Chromium
  tabanlı tarayıcılar ve Firefox.
- Yeni bağımlılık: `docs/security.md`, Dependencies.

## Naming
- Python: modül/fonksiyon/değişken `snake_case`, sınıf `PascalCase`, sabit `UPPER_SNAKE_CASE`.
- Domain kavramları `docs/domain.md` "Kod adı" ile birebir aynı adlandırılır (ör. `LeaveRequest`,
  `Entitlement`, `half_days`); eşanlamlı uydurulmaz.
- Süre taşıyan her alan/parametre birimini adında taşır: `half_days` (ör. `requested_half_days`).
- Modül yerleşimi: `app/modules/<modül>/public.py` + `app/modules/<modül>/internal/…`
  (`docs/architecture.md`).
- API yolları: `/api/<kaynak-çoğul>` küçük harf, kebab-case (ör. `/api/leave-requests`).
- Hata kodları: `<modül>.<snake_case>` (ör. `leave.insufficient_balance`).
- Testler: `tests/<katman>/<modül>/test_<konu>.py`; test adı davranışı söyler
  (`test_request_exceeding_balance_is_rejected`). İş kuralı testleri adında/docstring'inde BR
  numarasını taşır (`BR-10`).
- Branch ve commit: `docs/git.md`.

## Error handling
- Domain ve servis katmanı, ortak `DomainError` taban sınıfından türeyen **kodlu** hatalar fırlatır
  (`code = "leave.insufficient_balance"`). `None`/`False` ile hata bildirmek yasak.
- API'de tek bir exception handler bu hataları RFC 9457 `application/problem+json` yanıtına çevirir:
  `type`, `title` (Türkçe), `status`, `detail` (Türkçe), `code`. Doğrulama hataları 422, yetki
  hataları 403 (varlığı gizlemek gereken yerlerde 404), çakışmalar 409.
- Beklenmeyen hatalar: 500 + `correlation_id`; ayrıntı yalnız log'a yazılır. Stack trace, SQL,
  dosya yolu veya iç kimlik bilgisi asla kullanıcıya sızmaz.
- Frontend davranışını `code` alanına göre belirler, metne göre değil.

## Data rules
- Süreler: tamsayı **yarım gün birimi** (`int`, 1 gün = 2). `float` gün yasak.
- İzin günleri: saat dilimsiz takvim tarihi (`datetime.date`); aralıklar her iki uç dahil.
- Zaman damgaları: timezone-aware UTC `datetime` olarak saklanır, arayüzde `Europe/Istanbul`
  gösterilir. Naive `datetime` yasak (ruff `DTZ`).
- "Bugün/şimdi" domain'de okunmaz; bir `Clock` bağımlılığından parametre olarak gelir (test
  edilebilirlik).
- Kimlikler: SQLite tamsayı birincil anahtar. API'de yetki kontrolü olmadan hiçbir ID ile kayıt
  dönülmez.
- SQLite bağlantısı: `PRAGMA foreign_keys=ON`, `journal_mode=WAL`. Şema yalnız Alembic göçleriyle
  değişir; uygulama başlarken `create_all` yasak.
- Para alanı yok (MVP'de ücret hesaplanmaz).

## Enforced by tooling
`scripts/check` (adımlar `scripts/check.conf`'ta):
- `ruff check` — lint, import sırası, bandit (`S`), naive datetime yasağı (`DTZ`), pyupgrade.
- `ruff format --check` — biçim tartışması yok; biçim ruff'ındır.
- `mypy` (`strict = true`, `app/`) — tüm fonksiyonlar tipli, `Any` sızıntısı yok.
- `lint-imports` — modül sınırları ve saf domain (`docs/architecture.md`, Forbidden dependencies).
- `node --check` — `app/` altındaki her `.js` dosyasının sözdizimi.
- `pytest` — `test [fast]` (unit + integration, `-m "not e2e"`) ve `e2e` (yalnız full);
  `domain-coverage` — domain kodu için %90 kapısı (`docs/testing.md`).
