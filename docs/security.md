# Security

> Ajanların her planda ve review'da uyduğu temel kurallar. İzin verisi kişisel veridir (KVKK);
> sağlık raporu bilgisi özel nitelikli kişisel veri sayılabilir.

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.
- Oturum imzalama anahtarı ve benzeri sırlar yalnız ortam değişkeninden okunur; varsayılan değer
  yoktur — eksikse uygulama başlamaz.
- SQLite veritabanı dosyaları (`*.db`, `*.sqlite*`) kişisel veri içerir: repoya girmez
  (`.gitignore`), test ve geliştirmede yalnız sentetik veri kullanılır.

## Input & output
- Her API girdisi Pydantic modelleriyle sınırda doğrulanır; bilinmeyen alanlar reddedilir
  (`extra="forbid"`).
- SQL yalnız SQLAlchemy ile, parametreli; string birleştirerek SQL yasak.
- Frontend'de kullanıcı verisi DOM'a yalnız `textContent` / `setAttribute` ile yazılır;
  `innerHTML` ile kullanıcı verisi basmak yasak (XSS).
- Statik yanıtlarda güvenlik başlıkları: `Content-Security-Policy: default-src 'self'` (inline
  script yok), `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`,
  `frame-ancestors 'none'`.
- Hata yanıtları `docs/conventions.md`, Error handling'e uyar: iç detay sızmaz.
- **Veri minimizasyonu (KVKK):** TC kimlik numarası tutulmaz; rapor kayıtlarında tanı/açıklama
  tutulmaz (yalnız tarih + tür); doğum tarihi yalnız BR-3 yaş kuralı için tutulur.
- Log'lara isim, e-posta, şifre, oturum çerezi veya TC kimlik no yazılmaz — yalnız iç ID'ler ve
  `correlation_id`.

## AuthN / AuthZ
- **Kimlik doğrulama (MVP):** yerel hesaplar; şifreler argon2id ile hash'lenir. Sunucu taraflı
  oturum; çerez `HttpOnly`, `Secure`, `SameSite=Strict`. Durum değiştiren her istek (POST/PUT/
  PATCH/DELETE) özel bir CSRF başlığı ister. Başarısız girişlerde hesap + IP bazında hız sınırı.
  Çıkışta ve şifre değişiminde oturum sunucuda geçersiz kılınır. AD/SSO v2'de (identity modülü
  arkasında).
- **Yetkilendirme default-deny'dır** ve her modülün **servis katmanında** uygulanır (route
  dekoratörü tek başına yeterli sayılmaz). Her servis fonksiyonu çağıranın kimliğini (`Actor`)
  parametre olarak alır.
- Roller ve kapsamları `docs/domain.md` BR-17/BR-18: Çalışan (kendi), Yönetici (hiyerarşiden
  türetilir, bağlı ekip), Şirket İK (kendi şirketi), Grup İK (tüm şirketler), Sistem Yöneticisi
  (kullanıcı/rol yönetimi, izin verisi yok).
- **Şirket sınırı en kritik veri sınırıdır:** Şirket İK ve yönetici başka bir şirketin kaydına
  hiçbir endpoint üzerinden erişemez; erişim denemesi varlığı sızdırmamak için 404 döner.
- Kimse kendi talebini onaylayamaz (BR-13); rol atamaları ve yetki değişiklikleri denetim
  kaydına yazılır.
- Her endpoint için yetkisiz erişim testi zorunludur (`docs/testing.md`).

## Dependencies
- Her yeni bağımlılık (runtime veya dev) planda adı, amacı ve lisansıyla listelenir ve plan
  onayıyla birlikte insan tarafından onaylanır. Onaysız `uv add` yasak.
- Kabul edilen lisanslar: MIT, BSD, Apache-2.0, PSF, ISC, MPL-2.0 (değiştirilmeden kullanılır;
  ADR 0003). GPL ailesi kabul edilmez. Diğerleri ADR gerektirir. Kontrol geçişli bağımlılıkları da
  kapsar.
- Sürümler `uv.lock` ile sabittir; check `--locked` ile çalışır (kilit dosyası güncel değilse
  kırmızı).
- Bilinen açık taraması: `pip-audit`, CI'da `check`'ten ayrı bir job olarak (ağ gerektirdiği için
  check'in deterministikliğini bozmasın diye). Walking skeleton spec'inde eklenir.

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase.
