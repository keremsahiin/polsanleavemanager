# ADR 0001 — Modüler monolit: Python 3.14 + FastAPI, build'siz HTML/CSS/JS

- Status: Accepted
- Date: 2026-10-19

## Context
Polsan şirketler grubu (<10 şirket, <1000 çalışan) için bir izin yönetim sistemi kuruluyor.
Tek bir küçük ekip geliştirecek; ajanlar sık sık `scripts/check` çalıştıracak. İş kuralları
(4857 sayılı İş Kanunu'na göre hakediş, iş günü sayımı) yasal risk taşıdığı için iyi korunmalı.
Bootstrap mülakatında ekip backend için Python/FastAPI, frontend için saf HTML/CSS/JS seçti.

## Decision
Uygulamayı Python 3.14 + FastAPI ile tek süreçli bir **modüler monolit** olarak kuruyoruz
(modüller: identity, organization, calendar, leave, audit); frontend build adımı olmadan statik
dosyalar (ES modülleri) olarak aynı süreçten sunulur. Paket yönetimi uv (`uv.lock`), veri erişimi
SQLAlchemy 2 + Alembic. Modül sınırları import-linter ile `scripts/check` içinde zorlanır.

## Consequences
- (+) Tek araç zinciri (Python); npm/bundler yok, check hızlı ve süreç bırakmaz.
- (+) Aynı origin: CORS yok; yetki zorunlu olarak sunucuda.
- (+) Modül sınırları test edilebilir; ileride bir modül ayrılabilir.
- (−) Saf JS'te tip güvenliği yok; frontend mantığı ince tutulmalı (iş kuralı sunucuda).
- (−) Python'da derleme zamanı garantisi yok — `mypy --strict` ile telafi edilir.

## Alternatives considered
- .NET 10 + ASP.NET Core (makinede kurulu) — ekip Python'u tercih etti.
- React + TypeScript SPA — npm araç zinciri ve build adımı getirir; MVP için gereksiz.
- Mikroservisler — bu ölçek için yalnız operasyon yükü.
- Klasik katmanlı monolit — modül sınırları zamanla bulanıklaşır.

## Revisit triggers
- Frontend etkileşimi saf JS ile yönetilemez hale gelirse (ör. >~3k satır JS, tekrar eden durum
  yönetimi hataları).
- Ekip birden fazla bağımsız takıma bölünürse.
