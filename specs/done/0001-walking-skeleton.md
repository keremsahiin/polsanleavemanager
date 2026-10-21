# Spec 0001 — Uygulama iskeleti (walking skeleton)

- Status: Shipped
- Mode: lite
- Plan: `specs/plans/0001-plan.md`

## Intent
Polsan İzin Yönetimi'nin geliştirici ekibi, ilk iş özelliğine başlamadan önce uçtan uca çalışan
bir uygulama iskeleti istiyor: uygulama tek komutla ayağa kalkar, boş ama güncel şemalı bir
veritabanıyla çalışır, kendi sağlık durumunu bildirir ve tarayıcıda Türkçe bir açılış sayfası
gösterir. Sonraki tüm özelliklerin kullanacağı ortak davranışlar (standart hata yanıtı,
korelasyon kimlikli log, güvenlik başlıkları) burada bir kez kurulur. Unit, integration ve e2e
test katmanlarının her biri en az bir gerçek testle `scripts/check` içinde ve CI'da çalışır.
Başarı: sonraki özellikler (giriş, şirket ağacı, …) yalnız kendi davranışlarını ekler, altyapı
kurmaz. Bilinçli olarak yapılmayan: hiçbir iş kuralı, giriş/oturum veya izin verisi yok.

## Requirements
**Çalıştırma ve yapılandırma**
- R-1: Veritabanı dosyasının yolu zorunlu bir ortam değişkeninden okunur; tanımlı değilse uygulama
  açık bir Türkçe mesajla başlamayı reddeder. Varsayılan yol yoktur. Uygulama var olmayan bir
  veritabanı dosyasını oluşturmaz; dosyayı yalnız şema güncelleme komutu oluşturur.
- R-2: Veritabanı şeması ayrı bir komutla en güncel sürüme getirilir; uygulama başlarken şemayı
  kendiliğinden değiştirmez.
- R-3: Repoda gerçek sır içermeyen bir örnek ortam dosyası ve "yerelde nasıl çalıştırılır"
  anlatan bir geliştirici bölümü bulunur.

**Sağlık sinyalleri**
- R-4: "Canlı" sinyali, uygulama süreci istek karşılayabildiği sürece başarılıdır.
- R-5: "Hazır" sinyali yalnız veritabanı dosyası var, erişilebilir ve şema en güncel sürümdeyse
  başarılıdır; değilse "hazır değil" der ve hiçbir iç detay (dosya yolu, hata metni, sürüm) vermez.
- R-6: Sağlık sinyalleri kimlik doğrulaması gerektirmez (iç detay içermedikleri için).

**Ortak davranışlar**
- R-7: Bilinmeyen bir API adresi, var olan bir adrese desteklenmeyen bir method ve beklenmeyen
  bir hata, `docs/conventions.md` (Error handling) standardında kodlu, Türkçe bir hata yanıtı döner; beklenmeyen hatada yanıt bir korelasyon
  kimliği taşır ama iç detay taşımaz.
- R-8: Her istek standart çıktıya tek bir JSON log satırıyla kaydedilir: UTC zaman, seviye,
  method, yol, durum, süre (ms), `correlation_id`. İstek gövdesi, sorgu parametreleri, çerezler ve
  kişisel veri log'lanmaz. Beklenmeyen hatanın detayı yalnız log'a, aynı korelasyon kimliğiyle
  yazılır.
- R-8a: İstek geçerli biçimde (en fazla 64 karakter; harf, rakam, tire) bir istek kimliği taşıyorsa
  korelasyon kimliği olarak o kullanılır; yoksa veya geçersizse yenisi üretilir.
- R-9: Her yanıt (sayfa, API, hata) `docs/security.md` (Input & output) güvenlik başlıklarını taşır.

**Açılış sayfası**
- R-10: Kök adreste Türkçe bir açılış sayfası ("Polsan İzin Yönetimi") sunulur; sayfa açılışta
  sistemin hazır olup olmadığını sunucuya bir kez sorar ve sonucu gösterir; sunucu 5 saniye içinde
  yanıt vermezse ulaşılamıyor kabul edilir.

**Doğrulama sözleşmesi**
- R-11: `./scripts/check` (full) unit, integration ve e2e katmanlarını; `./scripts/check --fast`
  e2e dışındaki tüm testleri çalıştırır. Ayrım test işaretiyle yapılır; işaretsiz yeni bir test
  hızlı profilde çalışır.
- R-12: Domain kodu için kapsama kapısı (%90 satır + dal) check'te etkindir; henüz domain kodu
  yokken check yeşildir.
- R-13: Check, iki profilde de arkasında çalışan süreç bırakmaz — e2e testi başarısız olsa bile.
- R-14: CI, pull request'lerde tam profili (e2e dahil) çalıştırır; ayrıca bilinen açık taraması
  ayrı bir job olarak çalışır ve bilinen bir açık bulursa kırmızı olur (zorunlu status check
  değildir).

## User experience
- Flow: kullanıcı tarayıcıda uygulamanın kök adresini açar → sayfa başlığı ve "Kontrol ediliyor…"
  görünür → sunucu yanıtına göre "Sistem çalışıyor" veya "Sisteme şu an ulaşılamıyor" görünür.
- States:
  - Yükleniyor: "Kontrol ediliyor…"
  - Başarı: "Sistem çalışıyor"
  - Hata (hazır değil, sunucuya ulaşılamıyor veya 5 sn içinde yanıt yok): "Sisteme şu an ulaşılamıyor"
  - Boş: yok — gösterilecek veri yok.
  - Yetki yok: yok — iskelette giriş/yetki yok.
- Design reference: none — the flow above is the design.
- Accessibility: sayfa dili Türkçe olarak bildirilir; durum metni değiştiğinde ekran okuyuculara
  duyurulur; metin kontrastı WCAG 2.1 AA (≥ 4.5:1); sayfada fare gerektiren etkileşim yoktur.

## Constraints & out of scope
- Kısıtlar: `docs/architecture.md`, `docs/conventions.md`, `docs/security.md`, `docs/testing.md`
  ve ADR 0001/0002 geçerlidir (tek süreç/tek worker, build'siz frontend, SQLite WAL + foreign key,
  Alembic dışında şema değişikliği yok, naive datetime yok).
- Yeni bağımlılıklar planda listelenir ve plan onayıyla onaylanır (`docs/security.md`).
- Out of scope: giriş/oturum, roller, herhangi bir iş tablosu veya iş kuralı; üretim dağıtımı
  (IIS/nginx yapılandırması, servis kaydı); yedekleme; GitHub branch protection ayarı;
  sayfanın periyodik yenilenmesi.

## Acceptance criteria
**Çalıştırma ve yapılandırma**
- [ ] AC-1 — Veritabanı yolu tanımlı ve şema güncelken uygulama başlar ve canlı sinyali başarılı döner.
- [ ] AC-2 — Veritabanı yolu tanımlı değilken uygulama başlamaz, sıfırdan farklı çıkış koduyla
  biter ve çıktıda ortam değişkeninin adını içeren Türkçe bir mesaj gösterir.
- [ ] AC-3 — Şema güncelleme komutu var olmayan bir veritabanı dosyasını oluşturur ve en güncel
  sürüme getirir; ikinci kez çalıştırıldığında hata vermez ve hiçbir şey değiştirmez.
- [ ] AC-4 — Şeması hiç güncellenmemiş bir veritabanıyla başlatılan uygulama şemayı değiştirmez
  (başlatma sonrası şema sürümü hâlâ boştur).
- [ ] AC-5 — Var olmayan bir dosya yoluyla başlatılan uygulama, başlatmadan ve hazır sinyali
  sorgulandıktan sonra o yolda dosya oluşturmamıştır.
- [ ] AC-6 — Örnek ortam dosyası repoda bulunur, gerekli her değişkeni listeler ve gerçek bir sır
  içermez; geliştirici bölümündeki adımlar temiz bir klonda uygulamayı başlatmak için yeterlidir.

**Sağlık sinyalleri**
- [ ] AC-7 — Veritabanı erişilebilir ve şema güncelken hazır sinyali başarılıdır.
- [ ] AC-8 — Şema güncel değilken hazır sinyali "hazır değil" (HTTP 503) döner.
- [ ] AC-9 — Veritabanı dosyası yokken veya erişilemezken hazır sinyali "hazır değil" (HTTP 503) döner.
- [ ] AC-10 — "Hazır değil" yanıtı veritabanı yolunu, hata metnini veya şema sürümünü içermez.
- [ ] AC-11 — Canlı ve hazır sinyalleri oturum olmadan çağrılabilir.

**Ortak davranışlar**
- [ ] AC-12 — Bilinmeyen bir API adresi HTTP 404 ve `application/problem+json` döner; yanıtta
  `type`, `title` (Türkçe), `status`, `detail` (Türkçe) ve `code` alanları bulunur.
- [ ] AC-13 — Var olan bir API adresine desteklenmeyen bir method HTTP 405 ve AC-12 ile aynı
  biçimde bir yanıt döner.
- [ ] AC-14 — Beklenmeyen bir hata HTTP 500, Türkçe genel bir mesaj ve `correlation_id` döner;
  yanıt stack trace, istisna metni veya dosya yolu içermez.
- [ ] AC-15 — AC-14'teki hatanın detayı log'da aynı `correlation_id` ile bulunur.
- [ ] AC-16 — Her yanıt bir korelasyon kimliği başlığı taşır ve her istek için o kimliği içeren
  tek bir JSON log satırı yazılır; satır UTC zaman, seviye, method, yol, durum ve süre (ms) alanlarını içerir.
- [ ] AC-17 — Geçerli bir istek kimliğiyle gelen istekte yanıtın ve log satırının korelasyon
  kimliği o değerdir; 64 karakterden uzun veya izin verilmeyen karakter içeren bir istek kimliği
  kullanılmaz, yerine yeni bir kimlik üretilir.
- [ ] AC-18 — Sorgu parametresi ve gövde içeren bir isteğin log satırında ne sorgu değerleri ne de
  gövde bulunur.
- [ ] AC-19 — Sayfa, API ve hata yanıtlarının her biri `Content-Security-Policy` (`default-src
  'self'` ve `frame-ancestors 'none'` içerir), `X-Content-Type-Options: nosniff` ve
  `Referrer-Policy: same-origin` başlıklarını taşır.

**Açılış sayfası**
- [ ] AC-20 — Kök adres, başlığı "Polsan İzin Yönetimi" olan, dili Türkçe bildirilmiş ve Türkçe
  karakterleri doğru görüntülenen bir sayfa döner.
- [ ] AC-21 — Sunucu yanıtı gelmeden önce sayfada "Kontrol ediliyor…" görünür.
- [ ] AC-22 — Sistem hazırken sayfada "Sistem çalışıyor" görünür.
- [ ] AC-23 — Sistem hazır değilken veya sunucuya ulaşılamıyorken sayfada "Sisteme şu an
  ulaşılamıyor" görünür.
- [ ] AC-24 — Sunucu 5 saniye içinde yanıt vermezse sayfada "Sisteme şu an ulaşılamıyor" görünür.
- [ ] AC-25 — Durum metni ekran okuyuculara duyurulan bir bölgededir ve metin kontrastı ≥ 4.5:1'dir.

**Doğrulama sözleşmesi**
- [ ] AC-26 — `./scripts/check` (full) unit, integration ve e2e testlerinin her birinden en az
  birini çalıştırır ve yeşildir.
- [ ] AC-27 — `./scripts/check --fast` hiçbir e2e testi çalıştırmaz ve diğer tüm testleri çalıştırır;
  fast ve full'ün çalıştırdığı testlerin birleşimi tüm testlerdir.
- [ ] AC-28 — Henüz domain kodu yokken `./scripts/check` yeşildir; domain kapsaması %90'ın altına
  düştüğünde kırmızıdır (geçici bir kopyada kasıtlı düşük kapsamla gösterilir).
- [ ] AC-29 — `./scripts/residue` ve `./scripts/residue --fast` `RESIDUE CLEAN` verir.
- [ ] AC-30 — Bir e2e testi başarısız olduğunda, check bittikten sonra test için başlatılan
  uygulama süreci çalışmaya devam etmez.
- [ ] AC-31 — CI'da pull request için `check` job'u tam profili (e2e dahil) çalıştırır; bilinen
  açık taraması ayrı bir job olarak çalışır ve bilinen bir açık bulduğunda kırmızı olur.

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation) — QA tablosu PR #2'de; AC-31 PR #2'nin CI koşularıyla
- [x] `scripts/check` green — CHECK GREEN (full, 8 steps, 16 s)
- [x] Independent review done; real findings fixed, noise rejected with written rationale — `specs/plans/0001-plan.md` triage bölümleri
- [x] Docs / ADRs updated if behavior or architecture changed — architecture, conventions, testing, security, development; ADR 0003
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 1 (taslakta öz-eleştiri: 7 boşluk eklendi); onaydan sonra 0 |
| Fix rounds | 5 (review #1/#2/#3/#5/#7 · F1/F2 · VERIFY V1–V3 · F-1 · CI audit A1) |
| Review findings: real / noise | 8 / 4 (ayrıca QA: 3 real; CI audit: 1 real) |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 (ship anında) |
