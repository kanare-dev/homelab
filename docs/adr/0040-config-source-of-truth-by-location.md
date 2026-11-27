# 0040. 設定値の正は置き場所で決め、Tailscale と AdGuard Home の設定はコードに移す

- ステータス: 採用（Tailscale は 2026-11-27、AdGuard Home は 2026-11-28 に適用）
- 日付: 2026-11-27

## 背景

運用者は、Omada コントローラー、Tailscale、AdGuard Home などの設定値を、すべて文書に残したいと考えている（[バックログ](../operations/roadmap/01-backlog.md)の「詳細設計書を整備し、『文書が先』の運用にする」）。

2026-11-27 に、サービスごとに設定値がどこにあるかを確かめると、置き場所は 3 種類に分かれた。

- **コードにある**: Terraform の VM、Ansible の UFW、Caddy、CoreDNS、Unbound、Prometheus と Alertmanager のルール、Tailscale のノード側の設定（`tailscale up` の `--advertise-routes`、`--accept-dns=false`）。
- **一部だけコードにある**: AdGuard Home。Ansible（`ansible/playbooks/infra.yml`）が書き換えるのは、上流の DNS、フォールバック、クエリログの保持期間、exporter のユーザーの 4 つだけである。フィルターのリスト、DNS の書き換え、クライアントの設定などは画面で変えたもので、`vm-infra` の `AdGuardHome.yaml` にしかない。バックログには「設定ファイルを Ansible で配っている」と書いていたが、実際と違っていた。
- **画面にしかない**: Omada コントローラー（ER605・SG2210P の設定を含む）、Tailscale の管理画面（ACL のポリシー、経路の承認、split DNS、鍵の期限）、Cloudflare（DNS のレコード、API トークン）、Buffalo、Healthchecks。

コードにある値を文書にも写すと、正が 2 か所になり、片方だけ直し忘れてずれる。画面にしかない値は、文書に残さなければ、コントローラーや機器を作り直したときに戻せない（[ADR-0034](0034-acl-for-vlan-boundaries-ufw-for-ports.md) で、ACL が全許可に戻るおそれを挙げた）。

## 決定

1. **設定値の正は、置き場所ごとに 1 か所にする。**
2. **コードにある設定は、コードを正とする。** 詳細設計書には、設計の意図と、コードへのリンクを書く。値を写したパラメーターシートは作らない。
3. **コードに移せる設定は、コードに移す。**
   - Tailscale の ACL のポリシー（tailnet policy file）は、リポジトリのファイルにし、公式の GitHub Action（`tailscale/gitops-acl-action`）で適用する。
   - AdGuard Home の設定は、`AdGuardHome.yaml` 全体を Ansible のテンプレートにする。パスワードのハッシュなどの秘密の値は、SOPS に入れる。
   - 移し終えるまでは、画面にある分は、次の 4 の扱いにする。
4. **画面にしか置けない設定は、詳細設計書（パラメーターシート）を正とする。** 変更のときに文書を先に直すか同時に直すかは、[ADR-0033](0033-docs-first-by-change-type-and-diagram-order.md) の分け方に従う。API があるもの（Omada の Open API、Cloudflare の API）は、取り出した値と文書を比べて、ずれを検査する。検査の方法（手元か CI か）は、まだ決めていない。
5. アプリのデータ（Home Assistant の `.storage`、n8n のワークフロー、Grafana の画面で作ったもの）は、この ADR の対象にしない。バックアップの方針（[ADR-0001](0001-no-vm-backup.md)）で扱う。

## 理由

- 正が 1 か所なら、どちらを直せばよいか迷わない。コードの値を文書に写すと、写し忘れが起きても気づけない。
- コードにすると、変更が diff として残り、PR で見直せる。作り直したときも、同じ設定に戻せる。文書に写すより確実である。
- Tailscale の ACL は、公式の仕組みでファイルにできる。ちょうど Tailscale 側の ACL を絞る作業が次の候補にあり、同じ作業でコードにできる。
- 画面にしか置けないものは、文書を正にするしかない。手で写す対象を、この種類だけに絞れる。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| すべての設定値を、パラメーターシートに写す | コードにある値と二重になり、ずれる。量も多い |
| 置き場所はそのままにし、画面の値は文書だけで残す（AdGuard・Tailscale も） | 移せるものまで手で写すことになる。変更の diff が残らない |
| Omada もコードにする（コミュニティ製の Terraform プロバイダー） | 公式のサポートがなく、VLAN・ACL・ポートを扱えるかも確かめていない（[バックログ](../operations/roadmap/01-backlog.md)の「設定のコード化」で検討中）。確かめてから決める |

## 影響と再検討の条件

- `CLAUDE.md` の「運用ドキュメント」に、この方針を書いた。
- [サービスカタログ](../homelab-service-catalog.md)に、`tailscale/gitops-acl-action` を「計画中」で足した。
- Tailscale の GitOps では、ポリシーのファイルが公開リポジトリに載る。利用者のメールアドレスは書かず、タグと `autogroup` で書く。GitHub Actions が使う Tailscale の認証情報の置き場所は、導入の作業で決める（GitHub の Secrets に置くなら、SOPS の外にあるものとして、非公開の台帳に記録する）。
- AdGuard の設定をテンプレートにするときは、今の画面の値を `AdGuardHome.yaml` から取り込み、変わらないことを確かめてから置き換える。
- 画面にしかない設定で、公式にコードにできる方法が出たら（Omada の公式の Terraform プロバイダーなど）、3 に移すかを見直す。
