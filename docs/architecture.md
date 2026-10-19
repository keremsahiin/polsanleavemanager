# Architecture

> Bootstrap'ta (2026-10-19) kararlaştırılan mimari. Ajanlar planlamadan önce bu dosyayı okur.

## System overview
polsanleavemanager, Polsan şirketler grubunun (ana şirket + alt şirketler) çalışanları için izin
talebi, yönetici onayı ve yıllık izin bakiyesi yönetimi sağlayan şirket içi bir web uygulamasıdır.
Tarzı **modüler monolit**: tek bir Python süreci (FastAPI + uvicorn) hem `/api` altındaki JSON
API'yi hem de `/` altındaki statik HTML/CSS/JS arayüzünü aynı origin'den sunar; veri tek bir
SQLite dosyasındadır. Gerekçe: <1000 çalışan ve <10 şirket ölçeğinde tek dağıtım birimi yeterli;
modül sınırları araçla (import-linter) korunur — bkz. ADR 0001 ve ADR 0002.

Kod yerleşimi:
- `app/modules/<modül>/public.py` — modülün dışarıya açık tek arayüzü (fonksiyonlar, DTO'lar).
- `app/modules/<modül>/internal/` — modülün iç kodu; `internal/domain/` saf iş kurallarıdır.
- `app/platform/` — modüllerin altındaki ortak altyapı (ayarlar, veritabanı bağlantısı, HTTP hata
  deseni, istek log'u, güvenlik başlıkları, sağlık sinyalleri). İş kuralı içermez; modülleri import
  etmez. `app/main.py` uygulamayı birleştirir (composition root).
- `migrations/` — Alembic şema göçleri (şemayı değiştirmenin tek yolu).
- `app/static/` — frontend (build adımı yok, ES modülleri, `fetch` ile `/api`).
- `tests/unit`, `tests/integration`, `tests/e2e` — bkz. `docs/testing.md`.

## Modules / components and ownership

| Module | Single responsibility | Owns |
|---|---|---|
| `identity` | Kimlik doğrulama (yerel hesap, oturum) ve rol ataması | Kullanıcı hesabı, şifre hash'i, oturum, rol atamaları |
| `organization` | Şirket ağacı ve çalışan–yönetici hiyerarşisi | Şirket (ana/alt), çalışan, yönetici ilişkisi, izne esas kıdem tarihi |
| `calendar` | Şirket bazında hangi günün iş günü olduğunu söylemek | Çalışma günü düzeni, resmi tatiller, arife (yarım gün) |
| `leave` | İzin talebi yaşam döngüsü ve bakiye | İzin türleri, talepler, onay/ret/iptal, hakediş, bakiye hareketleri, ek gün tanımları |
| `audit` | Değişmez denetim kaydı | Denetim olayları (kim, ne zaman, neyi, önce/sonra) |
| `app/platform` (modül değil) | Tüm modüllerin kullandığı teknik altyapı | Hiçbir iş verisi; yalnız şema sürüm bilgisi |

## Communication rules
- Modüller arası iletişim **yalnız senkron, doğrudan fonksiyon çağrısıdır** ve yalnız hedef
  modülün `public.py` arayüzü üzerinden yapılır. MVP'de olay/mesaj kuyruğu yoktur.
- Bağımlılık yönü tek yönlüdür: `leave → calendar | identity → organization → audit`
  (üstteki alttakini kullanabilir, tersi yasak; `calendar` ile `identity` birbirini kullanmaz).
- Bir modül başka bir modülün tablolarına SQL/ORM ile **erişemez**; veri yalnız `public.py`
  fonksiyonlarıyla alınır.
- Frontend yalnız `/api` üzerinden konuşur; yetki ve iş kuralı kararlarının tamamı sunucudadır.
- HTTP katmanı (route'lar) incedir: doğrulama + servis çağrısı + hata eşleme. İş kuralı içermez.

## Forbidden dependencies (make them testable)
`pyproject.toml` → `[tool.importlinter]`, `scripts/check` içindeki `boundaries` adımında denetlenir:
1. **Katmanlı modüller:** `leave → calendar | identity → organization → audit`; ters yönde veya
   `calendar ↔ identity` arasında import yasak (layers sözleşmesi).
2. **Yalnız public arayüz:** bir modül başka bir modülün `internal` paketini import edemez
   (forbidden sözleşmesi, `app.modules.*` → `app.modules.*.internal`).
3. **Saf domain:** `app.modules.*.internal.domain` paketleri `fastapi`, `starlette`,
   `sqlalchemy`, `alembic`, `sqlite3`, `uvicorn`, `httpx` import edemez; saat/tarih "şimdi"yi
   kendisi okumaz, parametre olarak alır.
4. **Platform iş modüllerine bağımlı değildir:** `app.platform` hiçbir `app.modules` paketini
   import edemez (forbidden sözleşmesi); modüller platformu kullanabilir.
5. **Frontend iş kuralı hesaplamaz** (bakiye, gün sayısı, yetki) — araçla denetlenemez, code
   review'da kontrol edilir.

## Deliberately out of scope
MVP (v1) için bilinçli olarak dışarıda bırakılanlar:
- AD/LDAP/SSO girişi, bordro aktarımı, takvim (Outlook vb.) entegrasyonu — v2.
- Rapor (sağlık) ve doğum izni için iş akışı/SGK entegrasyonu — MVP'de yalnız kayıt.
- Saatlik izin, vardiya/mesai yönetimi.
- Şirket bazında tam esnek izin politikası motoru (yalnız yasal tabana "ek gün").
- Çoklu sunucu / yatay ölçekleme, çok-kiracılık (multi-tenant) — bkz. ADR 0002.
- Çok kademeli onay zinciri.
