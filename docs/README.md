# docs

- [方式設計書（基本設計）](basic-design/README.md): 10 の観点で整理した設計書

## 方式設計の分類に入れていないもの

10 の観点に素直に収まらないため、`docs/` 直下に置いたままにしている。

| ファイル | 内容 | 置いたままにする理由 |
| --- | --- | --- |
| [runbook.md](runbook.md) | 起動・バックアップ・更新・障害切り分け・秘密情報管理・TLS・Slack 通知など | 複数の観点にまたがる手順書。`CLAUDE.md` や他の README から参照されている |
| [incidents/](incidents/) | 障害記録 | 設計書ではなく、時系列の記録 |
| [roadmap.md](roadmap.md) | 拡張計画 | 設計書ではなく、計画 |
| [homelab-service-list.md](homelab-service-list.md) | ホームラボで使えるツールの一覧（候補集） | このリポジトリの構成を記述したものではない |
| [screenshots/](screenshots/) | README・監視文書で使う画像 | 素材 |

