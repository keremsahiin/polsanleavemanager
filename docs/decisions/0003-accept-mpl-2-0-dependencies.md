# ADR 0003 — MPL-2.0 lisanslı bağımlılıkların kabulü

- Status: Accepted
- Date: 2026-10-19

## Context
`docs/security.md` yalnız MIT, BSD, Apache-2.0, PSF ve ISC lisanslarını kabul ediyor, diğerleri
ADR gerektiriyor. Spec 0001'in (uygulama iskeleti) BUILD aşamasında yapılan lisans taraması üç
geçişli geliştirme bağımlılığını liste dışında buldu: `certifi` (MPL-2.0, httpx üzerinden),
`pathspec` (MPL-2.0, mypy üzerinden) ve `text-unidecode` (Artistic/GPL, pytest-playwright →
python-slugify üzerinden). `pathspec` bootstrap'tan beri vardı, ama o zaman lisans taraması
yapılmamıştı.

## Decision
MPL-2.0 kabul edilen lisanslar listesine eklenir: dosya düzeyinde zayıf copyleft olduğu için,
değiştirilmeden kullanılan bir MPL-2.0 paketi kodumuza hiçbir yükümlülük getirmez. GPL ailesi
kabul edilmez. Bu yüzden `pytest-playwright` eklentisi kaldırılır ve Playwright doğrudan, kendi
fixture'larımızla kullanılır (`text-unidecode` ve `python-slugify` bağımlılık ağacından çıkar).

## Consequences
- (+) httpx (`TestClient`) ve mypy kullanılabilir. `certifi` Python ekosisteminde pratikte kaçınılmaz.
- (+) Tarayıcının yaşam döngüsü tamamen kendi e2e fixture'ımızda olur (resource hygiene).
- (−) pytest-playwright'ın hazır `page` fixture'ları ve CLI seçenekleri yok; birkaç satırlık kendi
  fixture'ımızı bakımda tutarız.
- (−) Bir MPL-2.0 paketinin kaynağı değiştirilirse değiştirilen dosyalar yayımlanmalıdır.
  Kural: MPL-2.0 paketleri yamalanmaz ve fork'lanmaz.

## Alternatives considered
- `text-unidecode`'u da "yalnız dev, dağıtılmıyor" gerekçesiyle kabul etmek — GPL'i bir istisnayla
  bile listeye sokmak politikayı aşındırır, oysa kaçınmak ~20 satır kod.
- Hukuk birimine danışana kadar BUILD'i bekletmek — MPL-2.0 iyi bilinen, düşük riskli bir lisans.

## Revisit triggers
- Bir MPL-2.0 paketinin yamalanması gerekirse.
- Şirket hukuk biriminin açık kaynak politikası farklı bir liste belirlerse.
