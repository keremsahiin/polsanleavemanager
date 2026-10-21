# ADR 0002 — SQLite veritabanı, şirket içi tek sunucu, tek süreç

- Status: Accepted
- Date: 2026-10-19

## Context
Ölçek <1000 kullanıcı, yazma yükü düşük (günde en fazla birkaç yüz izin işlemi). Ekip ayrı bir
veritabanı sunucusu işletmek istemiyor; makinede Docker yok. Uygulama yalnız intranetten
erişilecek.

## Decision
Veri tek bir SQLite dosyasında tutulur (WAL modu ve foreign key'ler açık). Uygulama şirket içi
tek bir sunucuda **tek uvicorn süreci / tek worker** olarak çalışır; önünde HTTPS sonlandıran
bir ters proxy (IIS veya nginx) bulunur. Veritabanı dosyası her gün yedeklenir.

## Consequences
- (+) Sıfır DB operasyonu; testler gerçek motorla, geçici dosyayla milisaniyelerde çalışır.
- (+) SQLAlchemy + Alembic sayesinde ileride PostgreSQL'e geçiş kodu büyük ölçüde korur.
- (−) Yatay ölçekleme yok; birden fazla worker/sunucu yazma çakışması yaratır — yasak.
- (−) Tek dosya = tek arıza noktası: yedek ve geri yükleme prosedürü zorunlu.
- (−) SQLite'ın tip esnekliği: tipler uygulama katmanında (SQLAlchemy + mypy) korunmalı.

## Alternatives considered
- PostgreSQL — daha güçlü eşzamanlılık, ama ayrı sunucu işletmek gerekir; ekip SQLite seçti.
- Microsoft SQL Server — lisans/altyapı gerektirir.

## Revisit triggers
- Eşzamanlı yazmalarda `database is locked` hataları görülmesi.
- Birden fazla uygulama sunucusu veya yüksek erişilebilirlik ihtiyacı.
- Kullanıcı sayısının 1000'i belirgin şekilde aşması.
