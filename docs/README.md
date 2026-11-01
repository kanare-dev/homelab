# docs

| ディレクトリ | 内容 |
| --- | --- |
| [architecture/](architecture/README.md) | 方式設計。構成図、インフラ、ネットワーク、可用性・信頼性、セキュリティ、移行性、災害対策 |
| [services/](services/README.md) | サービスごとの詳細設計。DNS、リバースプロキシと TLS、監視・アラート、Homepage、Home Assistant、n8n、CI/CD、vm-code、FreshRSS、MOTD |
| [operations/](operations/runbooks/README.md) | 運用。[Runbook](operations/runbooks/README.md)、[バックアップの手順](operations/runbooks/06-backup-restore.md)、[障害記録](operations/incidents/README.md)、[ロードマップ](operations/roadmap/README.md)（[Omada・VLAN](operations/roadmap/04-network-omada-vlan.md)、[OPNsense](operations/roadmap/08-network-opnsense.md)、[GPU 搭載 PC](operations/roadmap/05-gpu-pc.md)、[通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md)、[DMZ と外部公開](operations/roadmap/07-dmz.md)、[ラック](operations/roadmap/09-rack.md)、[見送り中の項目](operations/roadmap/03-deferred.md)） |
| [adr/](adr/README.md) | 設計判断の記録（ADR） |
| [homelab-service-catalog.md](homelab-service-catalog.md) | ホームラボで使えるツールのカタログ（候補集。導入済み・計画中・見送りなどの状況つき。このリポジトリの構成ではない） |
| screenshots/ | README・監視文書で使う画像 |

## 文書の運用

計画の文書と、現行構成の文書を混ぜないために、内容の状態で書く場所を分ける。

| 状態 | 書く場所 | 内容 |
| --- | --- | --- |
| 検討中 | [ロードマップ](operations/roadmap/README.md)（大型計画は 04 以降、小さな項目は 01） | 案、選択肢、リスク、緩和策の候補。**設計書・ADR にはまだ書かない** |
| 見送り | [見送り中の項目](operations/roadmap/03-deferred.md) | 理由と、再検討する条件 |
| 採用（未適用） | `architecture/` `services/` の設計書と ADR（ステータスは「採用（未適用）」） | 決めたことを、同じ変更で設計書と ADR に移す。設計書の冒頭に「未適用」と明記する |
| 適用済み | 同じ設計書・ADR、構成図、`README.md` | 「未適用」の表記を外し、ADR のステータスを「採用」にする。構成図と README を更新し、[完了済みの項目](operations/roadmap/02-completed.md)に一行残す |

- 「採用」にするかは、ユーザーが決める。Claude は、会話で案が出ただけのものを設計書や ADR に書かない。案はロードマップに「検討中」と明記して書く。
- 採用すると、ロードマップの該当箇所は設計書へのリンクに置き換え、詳細を二重に持たない。
- 判断を変えるときは、新しい ADR を追加し、古い ADR を「置き換え済み」にする（[ADR の書き方](adr/README.md)）。
- 会話に出たツールは、採用前でも[サービスカタログ](homelab-service-catalog.md)に「未検討」で追記する。
