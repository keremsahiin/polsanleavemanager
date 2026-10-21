# Git

> Bootstrap'ta (2026-10-19) ANEW'in güvenli varsayılanları olduğu gibi kabul edildi.
> Gevşetmek bilinçli bir karar (ADR) gerektirir.

## Branching
- Varsayılan branch: `main`.
- `feature/<spec-no>-<short-name>` — **spec yoksa branch da yok.** CHANGE lane mini-spec'leri de
  bu kalıbı kullanır.
- Refactor'lar: `refactor/<spec-no>-<short-name>` (mini-spec, Changed behavior = none).
- Düzeltmeler: `fix/<report-id>-<short-name>` (bug fix'ler spec numarası değil rapor taşır);
  olaylar: `incident/<date>-<short-name>`; önemsiz değişiklikler: `trivial/<short-name>`.
- Branch adları İngilizce, küçük harf, kebab-case (`docs/conventions.md`).

## Commits
- Conventional Commits, İngilizce, plan referansıyla: `feat(leave): approval endpoint [plan 0002/3]`.
  Scope = modül adı (`identity`, `organization`, `calendar`, `leave`, `audit`) veya `ui`, `build`,
  `docs`.
- Ajan commit'leri aynı standarda uyar: mesajı ajan yazar, insan onaylar.

## Forbidden
- `main`'e doğrudan commit.
- Paylaşılan branch'lerde force push ve geçmişi yeniden yazma. Geri alma = `git revert`
  (recovery R-11).
- Veritabanı dosyalarını, `.env`'yi veya gerçek kişisel veri içeren fixture'ları commit'lemek.

## Enforcement on GitHub
- `main` için branch protection açılır: PR zorunlu, en az 1 onay, `check` ve `doctor` job'ları
  zorunlu status check, force push ve silme kapalı. (Repo ayarıdır — repo sahibi uygular.)

## Trivial changes
<!-- Applies only to requests the change-request triage rubric
     (workflows/change-request.md) classifies as TRIVIAL: no acceptance criterion changes, no shared code. -->
- Policy: **(1) PR + one reviewer, no spec** — bootstrap'ta seçildi (2026-10-19).
  `trivial/<short-name>` branch'i → PR → bir reviewer onayı → squash-merge.
- Always: one narrow commit, `scripts/check` green. A second file or a new test means re-triage.

## Pull requests
- PR template checklist completed; `scripts/check` green in CI; squash-merge.
- PR açıklaması Türkçe; kanıt tablosu `CHECK GREEN (full, …)` satırını gösterir (fast değil).
