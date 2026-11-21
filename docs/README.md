# docs

| ディレクトリ | 内容 |
| --- | --- |
| [architecture/hld/](architecture/hld/README.md) | 基本設計（HLD）。第1章 システム構成・環境、第2章 信頼性、第3章 運用・保守、第4章 性能・拡張性、第5章 ネットワーク、第6章 セキュリティ |
| [architecture/lld/](architecture/lld/README.md) | 詳細設計（LLD）。サービスごとの詳細と IP アドレス一覧。役割ごとのフォルダ（`network/`: DNS・リバースプロキシと TLS・Omada コントローラー・IP アドレス一覧、`platform/`: 監視・アラート・MOTD、`apps/`: Homepage・Home Assistant・n8n・FreshRSS、`dev/`: CI/CD・vm-code、`hardware/`: 機器の仕様・公式資料と、導入前の機器・用品（[future/rack-10inch/](architecture/lld/hardware/future/rack-10inch/README.md)）） |
| [operations/](operations/runbooks/README.md) | 運用。[Runbook](operations/runbooks/README.md)、[バックアップの手順](operations/runbooks/06-backup-restore.md)、[障害記録](operations/incidents/README.md)、[ロードマップ](operations/roadmap/README.md)（[Omada・VLAN](operations/roadmap/04-network-omada-vlan.md)、[OPNsense](operations/roadmap/08-network-opnsense.md)、[GPU 搭載 PC](operations/roadmap/05-gpu-pc.md)、[通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md)、[DMZ と外部公開](operations/roadmap/07-dmz.md)、[ラック](operations/roadmap/09-rack.md)、[ER605・SG2210P の移行計画](operations/roadmap/10-er605-sg2210p-migration-plan.md)、[構成レビューの改善案](operations/roadmap/11-design-review-ideas.md)、[IP 割り当てと DHCP の見直し](operations/roadmap/12-ip-address-and-dhcp-review.md)、[見送り中の項目](operations/roadmap/03-deferred.md)） |
| [diagrams/](diagrams/README.md) | 構成図（現行は draw.io の SVG、VLAN 化のあとと物理構成図は HTML と PNG）と、生成・整形スクリプト、更新の手順 |
| [adr/](adr/README.md) | 設計判断の記録（ADR） |
| [homelab-service-catalog.md](homelab-service-catalog.md) | ホームラボで使えるツールのカタログ（候補集。導入済み・計画中・見送りなどの状況つき。このリポジトリの構成ではない） |

## リポジトリ構成

```text
homelab/
├── README.md
├── LICENSE
├── assets/                 # リポジトリ全体で使う素材。logo/（ロゴの SVG と生成スクリプト make-logo.py、使い方の README）、screenshots/（README・監視文書で使う画像）
├── Makefile                # lint-all、terraform / ansible の実行ショートカット
├── .sops.yaml              # SOPS の暗号化ルール
├── .markdownlint-cli2.yaml # Markdown lint のルール
├── .github/workflows/      # CI（lint）
├── .githooks/              # pre-push フック（make hooks で有効化）
├── terraform/
│   └── proxmox/            # VM のプロビジョニング
├── ansible/
│   ├── inventory/
│   ├── roles/
│   └── playbooks/
├── docker/
│   └── compose/            # dns / freshrss / homeassistant / homepage / monitoring / n8n / omada / reverse-proxy
├── tools/
│   └── check-md-links.py   # Markdown の内部リンク検査
└── docs/
    ├── architecture/       # 設計書
    │   ├── hld/            # 基本設計（第1章〜第6章）
    │   └── lld/            # 詳細設計（役割ごとのフォルダ: network/、platform/、apps/、dev/、hardware/）
    │       └── hardware/   # 機器ごとの仕様・資料（置き方の決まりは README）と、導入前の機器・用品（future/rack-10inch/。他の作者のモデルのデータは、Git 管理しない）
    ├── diagrams/           # 構成図（現行は draw.io の SVG、VLAN 化後と物理構成図は HTML と PNG）と生成・整形スクリプト、README（更新の手順）。assets/ はアイコン素材（Git 管理外）
    ├── operations/         # Runbook、バックアップ、障害記録、ロードマップ
    └── adr/                # 設計判断の記録
```

## 文書の運用

計画の文書と、現行構成の文書を混ぜないために、内容の状態で書く場所を分ける。

| 状態 | 書く場所 | 内容 |
| --- | --- | --- |
| 検討中 | [ロードマップ](operations/roadmap/README.md)（大型計画は 04 以降、小さな項目は 01） | 案、選択肢、リスク、緩和策の候補。**設計書・ADR にはまだ書かない** |
| 見送り | [見送り中の項目](operations/roadmap/03-deferred.md) | 理由と、再検討する条件 |
| 採用（未適用） | `architecture/hld/` `architecture/lld/` の設計書と ADR（ステータスは「採用（未適用）」） | 決めたことを、同じ変更で設計書と ADR に移す。設計書の冒頭に「未適用」と明記する |
| 適用済み | 同じ設計書・ADR、構成図、`README.md` | 「未適用」の表記を外し、ADR のステータスを「採用」にする。構成図と README を更新し、[完了済みの項目](operations/roadmap/02-completed.md)に一行残す |

- 「採用」にするかは、ユーザーが決める。Claude は、会話で案が出ただけのものを設計書や ADR に書かない。案はロードマップに「検討中」と明記して書く。
- 採用すると、ロードマップの該当箇所は設計書へのリンクに置き換え、詳細を二重に持たない。
- 判断を変えるときは、新しい ADR を追加し、古い ADR を「置き換え済み」にする（[ADR の書き方](adr/README.md)）。
- 会話に出たツールは、採用前でも[サービスカタログ](homelab-service-catalog.md)に「未検討」で追記する。
- 設定・構成を変えるとき、文書を**先**に更新するか、**同時**に更新するかは、変更の種類で決める。構成図は、to-be を先に、as-is は実機の変更ごとに更新する（[ADR-0033](adr/0033-docs-first-by-change-type-and-diagram-order.md)）。
