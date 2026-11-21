# 未着手の項目

この文書には、[ロードマップ](README.md)の項目のうち、まだ着手していないものを、領域ごとに載せる。大型の計画は、別の文書にある。

## ネットワーク・DNS

- 方針: 自分だけが使うアクセスは、Tailscale だけで完結させる（[ADR 0005](../../adr/0005-tailscale-only-remote-access.md)）。Cloudflare Tunnel で外部に公開するのは、Tailscale を入れていない他の人と共有したいという具体的なニーズが出たサービスに限る。そのニーズが出るまでは、Cloudflare Tunnel と Split-Horizon DNS には着手しない。
- [ ] **検討中**: Omada Cloud（クラウドアクセス）を使い続けるか、無効にするか。2026-11-03 から、便利そうなので当面は有効にして試している。最終的に無効にするかもしれない。判断の材料は、使い勝手と、リスク（Tailscale と Caddy を通らず、TP-Link ID の認証だけで、コントローラーの管理画面に外から入れる経路が増える。[第5章 ネットワーク](../../architecture/hld/05-network.md#管理画面への外部到達リスクを受け入れる)）。決めたら ADR に残し、無効にするときは、[外部サービスの表](../../architecture/hld/05-network.md#外部サービスへの依存)・[構成図](../../diagrams/as-is-diagram/make-as-is-diagram.py)・[システム構成・環境](../../architecture/hld/01-system.md)の Omada Cloud と、「外から入る経路は Tailscale だけ」の例外の記述（`03-network.md`、`05-security.md`、`01-overview.md`）を消す
- [x] Wi-Fi の SSID の名前を `Onda` と `Onda-Forte` に変える（**2026-11-03 に実施**。移行の前に、運用者が変えた。[第5章 ネットワーク](../../architecture/hld/05-network.md)に記録）。SwitchBot Hub 2 は繋ぎ直し済み（`Onda` に接続）。WPA3 の名前は `Onda-Forte` で設定済み。残り: テレビと仕事用 PC は、運用者が気づいたときに繋ぎ直す（段階 1 の確認の前に、繋ぎ直しておく）。Buffalo 本体のバックアップの取り直しは、運用者が行う。理由は、名前が長くて打ち込みにくいこと、飽きたこと、もう少し homelab らしい名前にしたいこと。**あわせて、バンドステアリング Lite（2.4GHz と 5GHz で共通の SSID にする Buffalo の機能）を使いたい**。調べた範囲では、Lite は信号の強さだけで帯域を切り替え、ルーター全体の設定で、端末ごとには指定できず、既定は無効。使うには共通の SSID を設定する。**共通 SSID の名前を自由に決められるかは未確認**（第三者の記事では `Buffalo-XXXX` と `Buffalo-XXXX-WPA3` という名前になる。このリポジトリの設定の記録にも、共通 SSID は MAC アドレス由来の既定名とある）。AP モードで使えるか、WPA2 と WPA3 の組み合わせがどうなるかも未確認。Buffalo の画面で、バンドステアリング Lite の項目に、名前の入力欄があるかを見る。今の `Ceci n'est pas un Wi-Fi [2.4]` / `[5]` / `[2.4+]` / `[5+]` の 4 つは、WPA2 の 2 つも残す（[第5章 ネットワーク](../../architecture/hld/05-network.md)）。時期は、**移行（段階 1〜3）が落ち着いてから**。移行の最中に変えると、不具合の原因が、ネットワークの変更なのか、SSID の変更なのか、切り分けられなくなる。変えると、全端末が繋ぎ直しになる。SwitchBot Hub は、Wi-Fi の設定をアプリでやり直す必要がある可能性が高い（未確認）。段階 4 で Omada の AP を入れるときは、VLAN ごとの SSID（Trusted / IoT / Guest）を作り直すので、**そこで使う名前を今のうちに決めて、Buffalo に先に付けておけば、端末は 1 回の繋ぎ直しで済む**（AP を替えても、SSID とパスワードが同じなら、端末は設定を変えずに繋がる）。名前の案は、Trusted は今の名前の系統、IoT と Guest は空白や記号のない ASCII（IoT は 2.4GHz のみ）。
- [x] Servers・Lab の VM が、内部の名前（`*.lab.kanare.dev`）を引けないのは、**既定の設計**（2026-11-17 に確認。[ADR-0007](../../adr/0007-vm-host-dns-is-router.md)）。VM のホスト DNS はルーター（Terraform の `nameserver`。段階 3 で `10.77.20.1`、`10.77.40.1`）にし、AdGuard が要るコンテナだけ、`docker-compose.yml` の `dns:` で `10.77.20.10` を指定している（`homepage`、`n8n`、`freshrss`、`monitoring`）。段階 3 の手順 7 で、`vm-monitoring` から `getent hosts omada.lab.kanare.dev` が何も返さないことに気づいたが、ADR-0007 のとおりの動き。外形監視（blackbox）のアラートは、コンテナの `dns:` のおかげで、正常に動いている。新しく困る場面が出たら、そのとき見直す（案: ER605 の DNS プロキシで `lab.kanare.dev` を `vm-infra` に転送する。Omada の画面で設定できるかは未確認）。
- Omada 導入・VLAN 化と OPNsense 導入は、それぞれ大型計画として扱う（下の「大型計画」）

## インフラ・IaC・運用

- [x] `docs/architecture/lld/` の文書を、役割ごとにフォルダ分けした（**2026-11-06 に実施**。`network/`、`platform/`、`apps/`、`dev/`。番号は外した。機器の設定値は `docs/architecture/lld/hardware/<機器>/settings.md` に移した。[lld/README.md](../../architecture/lld/README.md)、[hardware/README.md](../../architecture/lld/hardware/README.md)）
- [ ] **検討中**: `vm-infra` の役割を分ける。DNS、リバースプロキシ、Tailscale を、別々に置き、**DNS とリバースプロキシは LXC にする**（2026-11-20、運用者がやりたいことを決めた。**設計は未決定**。次の作業の候補）。
  - 今の構成: `vm-infra`（`10.77.20.10`、Servers）の 1 台に、DNS（AdGuard Home、Unbound、CoreDNS）、リバースプロキシ（Caddy、[ADR 0019](../../adr/0019-caddy-reverse-proxy.md)）、Tailscale（サブネットルーター）が同居している（[構成図](../../architecture/hld/01-system.md)）。
  - やりたいこと: (1) DNS、リバースプロキシ、Tailscale を、別々の置き場所に分ける。(2) DNS とリバースプロキシは、VM でなく LXC にする。
  - 動機（運用者）: (1) 構成を綺麗にする。(2) LXC にすることで、リソースを節約できるかもしれない。**節約は小さい見込み**: `vm-infra` は、1.5GB の割り当てのうち約 0.5GB を使っている（2026-11-20）。LXC は、ホストのカーネルを共有するので、VM ごとの OS のぶんは減るが、ホストは 24GB で余裕があり、効くのは数百 MB 程度。主な利点は、構成の分かりやすさと、起動の速さ。
  - Tailscale（2026-11-20 の見立て。**未決定**）: 今は、サブネットルーターとして使っている（`10.77.20.0/24` と `10.77.40.0/24` を広告。外出先から、Servers・Lab の VM に IP で入る）。置き場所は、**小さな VM** を推す。理由: 外（tailnet）からの入口なので、ホストのカーネルを共有しない VM のほうが、境界がはっきりする。LXC では、`/dev/net/tun` の受け渡しと設定（特権・cgroup）が要る。LXC にもできる（資源は、さらに軽い）。どちらにするかは、DNS・プロキシの LXC を試したあとで決めてもよい。なお、Mac は、家でも、Servers・Lab を Tailscale の経路（`utun`）で引く（2026-11-20 の観測）。**ER605 の ACL を通らない**ので、ACL を絞るときの試験は、Tailscale を切って行う。
  - Tailscale の使い方（2026-11-20 の見立て。**未決定**）: 今は、外出先からのリモートアクセスだけで、`vm-infra` が subnet router（`10.77.20.0/24` と `10.77.40.0/24` を広告）。exit node は使っていない。ACL は既定のまま（全許可）。
    - **subnet router は続ける。** VM に Tailscale を入れずに済む。
    - **Tailscale 側の ACL を絞る。** subnet router の SNAT で、Servers の VM からは、送信元がすべて `vm-infra` に見えるので、ER605 の ACL では、端末ごとに区別できない。タグ（`tag:subnet-router` など）と ACL で、「どの端末が、どこの、どのポートに入れるか」を、Tailscale 側で絞る（例: iPhone は `vm-apps` の 443 だけ、Mac は全部）。ER605 の ACL を絞る日（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）とそろえて行う。
    - **exit node は、試す価値がある。** 利点: 公共 Wi-Fi で、通信を全部、家まで暗号化して運べる。外出先の DNS を、家の AdGuard に向けて、広告ブロックが外でも効く。海外から、日本の IP で出られる。引っ越し先が CGNAT でも使える。注意: 家の上り回線（建物の共用回線、二重 NAT。**上り速度は未測定**）と遅延が、外出先の速度になる。exit node の機器は、任意の通信を中継するので、**LAN に入れない形**（専用のノードで、VLAN と ACL により、インターネットへだけ出られる。LAN への通信は拒否）にする。管理画面で、exit node の承認が要る。
    - **置き場所の案**: `vm-infra` から分けた、専用の小さな VM に、subnet router と exit node の両方を持たせる（上の「Tailscale の置き場所」）。役割が増えるので、先に ACL を絞っておく。
    - ER605 の ACL の試験は、Tailscale を切って行う（Mac は、家でも、Servers・Lab を Tailscale の経路で引くため）。
  - LXC の管理（2026-11-20 の見立て。**未検証**）: Terraform は、今のプロバイダー（`telmate/proxmox`）に、LXC のリソース（`proxmox_lxc`）がある。ただし、VM のモジュール（`modules/vm`）とは別に、LXC のモジュールを作る（テンプレートの取得、`nesting` などの機能、VLAN タグ、IP）。Ansible は、LXC に SSH で入れば、VM と同じに扱える。注意: 今の AdGuard・Unbound・Caddy は Docker で動いている。LXC の中で Docker を動かすのは、Proxmox が勧めていないので、**パッケージで直接入れる形に、Ansible のロールを書き直す**のが素直（CoreDNS はバイナリ）。
  - 決めること（未決）: Tailscale の置き場所（上）。LXC の VLAN と IP（[IP の規則](../../adr/0025-address-octets-by-role.md)、VMID の規則 [ADR-0026](../../adr/0026-vmid-from-vlan-and-octet.md)）。移行の順序と戻し方（DNS が止まると、`*.lab.kanare.dev` と、Tailscale 経由の入口が止まる）。
  - VMID: 分割で作る LXC は、最初から新しい VMID の規則（`VLAN ID × 100 + 第 4 オクテット`。[ADR-0026](../../adr/0026-vmid-from-vlan-and-octet.md)）で作れる（付け替えが要らない）。今の `vm-infra`（VMID 111。付け替えると 2010）は、LXC に置き換わって、なくなる。VMID の付け替え（下の別の項目）の対象が、1 台減る。
  - 順序（運用者の考え、2026-11-20）: **ACL を絞ってから**行う。ACL の許可元・許可先が、役割ごとの IP（[ADR-0025](../../adr/0025-address-octets-by-role.md)）で書ければ、あとで置き場所を変えても、IP を引き継げば、ACL を直さずに済む（DNS・プロキシの新しい LXC に、今の `10.77.20.10` を引き継ぐか、新しい IP にして ACL を直すかは、そのとき決める）。
  - 採用を決めたら、設計書（[システム構成・環境](../../architecture/hld/01-system.md)、[DNS](../../architecture/lld/network/dns.md)）と ADR に移す。
- [ ] **検討中**: Omada コントローラー（`vm-omada`）を、Proxmox の外（別のハード）に移す（2026-11-08、運用者の考え。別のハードを買ったときに検討する）。理由: コントローラーが、管理する機器（SG2210P）の先の Proxmox の上にあるので、Proxmox が LAN から消えると、コントローラーも消え、スイッチの設定を直せない（[INC-2026-11-08](../incidents/2026-11-08-sg2210p-native-vlan-overwrite.md)）。当面は、IP（`https://192.168.11.12:8043`）でのアクセスと、ER605 の LAN ポートへの直結の切り戻し（[障害時切り分け](../runbooks/11-troubleshooting.md#proxmox-ホストと全-vm-にlan-から届かない)）で補う。
- [ ] 学習用に Traefik を `vm-apps` 上で試す。既存の入口（`vm-infra` の Caddy、[ADR 0019](../../adr/0019-caddy-reverse-proxy.md)）は置き換えず、`vm-apps` のコンテナ向けの別の入口として並べる。Docker ラベルによる自動検出、ダッシュボード、ミドルウェアを触るのが目的。Caddy を置き換えるかは、試したあとに新しい ADR で判断する
- [ ] VM の OS を Ubuntu 26.04 LTS に移行する（[ADR 0021](../../adr/0021-ubuntu-lts-for-vms.md)）。新しい cloud image で `ubuntu-cloud`（VMID 9000）を作り直し、まず `vm-dev` で Ansible が通るか確認してから、VM を 1 台ずつ作り直す。その場更新はしない。24.04 のサポートは 2029 年 4 月までなので急がない
- [ ] VM の VMID を、新しい規則（`VLAN ID × 100 + 第 4 オクテット`。[ADR-0026](../../adr/0026-vmid-from-vlan-and-octet.md)）に付け替える。段階 3 の後、VM を作り直すとき（上の Ubuntu LTS の入れ替えなど）に行う。状態を持たない VM（`vm-dev`）で先に手順を試す。データを持つ VM は、`qm clone` で複製して Terraform の state を付け替える案がある（未検証）。付け替えるたびに、`terraform.tfvars`、[Runbook 01](../runbooks/01-vm-startup-shutdown.md) の VMID、[IP アドレス一覧](../../architecture/lld/network/ip-addresses.md)、`vm-omada` と `vm-code` の文書の VMID を直す
- [ ] PVE ホストを 9.1 → 9.2 に更新する。保留 248 パッケージ（セキュリティ修正 61 件）が溜まっている。QEMU 10 → 11 とカーネル更新で、全 VM の停止を伴う再起動が要る。見送りの理由と再検討の条件は[障害記録 §4.3](../incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md)。バックアップ（`vzdump`）を先に入れる順番が望ましい
- [x] thin pool の過剰割当を解消した（`LvmThinPoolOverprovisioned`。**2026-11-05 に実施**）。`vm-omada`（20G）を足した 2026-11-03 に、割当の合計が 243.5G、pool（155.6G）に対する比率が 1.57 になり、しきい値 1.5 を超えていた。(1) `vm-dev` のディスクを 30G → 10G にした（Terraform は縮小できないので、`terraform apply -replace='module.vm["vm-dev"].proxmox_vm_qemu.vm'` で作り直し、`ansible-playbook playbooks/site.yml --limit vm-dev` で再構成した。残すデータは無かった）。(2) `vm-windows`（60G、VMID 130）を削除した。vzdump を 1 回取ったが、復元しない方針にして 2026-11-06 に消した（必要になったら ISO から作り直す。手順は[バックアップの手順](../runbooks/06-backup-restore.md#vm-windows-の削除と作り直し2026-11-05)）。結果は、割当の合計 163.5G、比率は約 1.05、pool の使用率は 54.5% → 33.7%。メモリも、`vm-windows` を起動すると 24GB を超える状態が解消した。しきい値は、1.6 が INC-2026-10-22 の障害時の値なので、上げていない。作り直すと 60G の割当が戻り、比率は約 1.5 になるので、`vm-dev` を縮めるなど、割当を空けてから作る
- [ ] **検討中**: ER605・SG2210P の設定（VLAN、DHCP、ACL、ポートの割り当て）をコード化できるか（2026-11-03、運用者の疑問）。調べた範囲では、(1) Omada コントローラーに **Open API**（REST。OAuth のクライアント認証。設定は Global view > Settings > Platform Integration > Open API）がある。(2) **公式の Terraform プロバイダーはない**（TP-Link の担当者は、その方法をサポートしないと回答している）。(3) コミュニティ製の [Tohaker/terraform-provider-omada](https://github.com/Tohaker/terraform-provider-omada) がある（コントローラー v5.x・v6.x 対応とされる。VLAN・ACL・ポートの設定を扱えるかは**未確認**）。移行（段階 1〜3）のあとに、コントローラーの Open API の文書（コントローラーの画面から開ける）で、VLAN・ACL・DHCP・スイッチのポートのエンドポイントがあるかを見て、プロバイダーの対応範囲と照らす。コード化できない部分は、設計書の許可表と設定値の表を正にして、バックアップを併用する（Buffalo と同じ運用）。コード化するなら、クライアントの鍵は SOPS に入れる。
- [ ] **検討中**: Omada コントローラーのバックアップの保存先を、iCloud Drive から S3 などに広げるか。今は手で取って、iCloud Drive に暗号化せずに置く（決定 2026-11-03。運用者は、今の段階では厳密さを求めない）。設定の唯一の記録がコントローラーの中にあり（[第5章 ネットワーク](../../architecture/hld/05-network.md)）、Mac だけだと、Mac と `vm-omada` が同時に失われたときに戻せない。S3 にするなら、バックアップファイルを暗号化してから置く（設定と認証情報が入るため）。バックアップ全般の方針（[ADR 0001](../../adr/0001-no-vm-backup.md)、NAS・PBS・restic の検討）と合わせて決める
- [ ] `vm-omada` の Omada コントローラーの画面（HTTPS）の外形監視を、blackbox に加える。`vm-omada` の OS の死活は、2026-11-03 に Prometheus の scrape に入れて、`TargetDown` で見ている（`up` が 1 になることを確認済み）。残りは、Caddy と DNS に `omada.lab.kanare.dev` を足したあとに、`prometheus.yml` の `blackbox_http` に足すこと（段階 1 の「同じ変更で直すもの」と一緒にやる）。足したら、[監視・アラート](../../architecture/lld/platform/monitoring.md)の注記を消す
- [ ] **検討中**: `vm-omada` だけに、プロセス・コンテナ別のメモリの履歴を取る仕組みを入れる（2026-11-09、[INC-2026-11-09](../incidents/2026-11-09-omada-memory-exhaustion.md) のアクションアイテム #3）。**採用は未決定**。
  - 動機: node_exporter は VM 全体の値しか出さず、01:46 の +327MB が Java か MongoDB かを特定できなかった。上限の設定（Java ヒープ 768MB、MongoDB キャッシュ 0.25GB、`mem_limit` 2.5GB）が効くかを、適用後に実測で確かめたい。
  - 案 A: **cAdvisor**（`gcr.io/cadvisor/cadvisor`）を `vm-omada` に 1 コンテナ置き、Prometheus が `:8080` を scrape する。`container_memory_working_set_bytes{name="omada"}` で、コンテナ単位の履歴と `mem_limit` への近さが取れる。UFW は `vm-monitoring`（`192.168.11.13`）からだけ許可する。メモリは 50〜100MB 程度（`mem_limit` を付ける）。系列数を絞る（`--docker_only`、使わないメトリクスの除外）。**限界**: Java と MongoDB は同じコンテナの中なので、cAdvisor では、どちらが増えたかは分からない。
  - 案 B: **process-exporter**（プロセス名ごとに RSS を出す。`java` と `mongod` を別の系列にする）を、`vm-omada` に systemd で置く。**今回知りたかった「Java か MongoDB か」に答えられる**。コンテナ内のプロセスも、ホストの `/proc` から見える。設定は、プロセス名の一致（`java`、`mongod`）を書いた YAML 1 つ。
  - 案 C: 入れない。適用後の数日だけ、`docker stats` と `ps` を手で見る（再発したら入れる）。
  - 見立て: 今回の目的には B が合う。コンテナ単位の傾向も見たければ A も足す。Omada 以外の VM には、必要になるまで入れない。
  - 決める条件・確認: Prometheus の TSDB の上限（5GB）への影響（`vm-omada` だけなら軽い）。`HostMemoryLow` に加えて、コンテナ・プロセス別のアラートを足すかは、実測を見てから決める。
  - 採用を決めたら、設計書（[監視・アラート](../../architecture/lld/platform/monitoring.md)、[Omada コントローラー](../../architecture/lld/network/omada-controller.md)）と ADR に移す。
- [ ] **検討中**: Omada のメトリクスを Grafana で見られるようにする（2026-11-09、運用者の希望）。**採用は未決定**。
  - 動機: 今の監視は、`vm-omada` の OS（node_exporter）と、ルーター・回線の ping だけで、Omada が管理する機器（ER605・SG2210P・AP）とクライアントの状態は、Omada の画面でしか見られない。Grafana に載せれば、回線・VM の監視と同じ画面で、推移とアラートが扱える。
  - 見たいもの（**未決定**）: 機器の状態（オンライン・オフライン）、ポートごとのトラフィック、AP ごとの接続端末数、クライアント数など。何を見たいかを先に決めると、方法を選びやすい。
  - 方法の候補（**未調査・未検証**）: (1) コミュニティ製の Omada 用 Prometheus exporter（例: `charlie-haley/omada_exporter`。**コントローラー v6 に対応しているかは未確認**）。(2) コントローラーの Open API（上の「設定のコード化」の項目と同じ API）を呼ぶ自前の exporter。どちらも、コントローラーの閲覧用の認証情報が要り、SOPS に入れる（読み取り専用のユーザーを作る）。
    - 2026-11-20 の調べ（検索のみ。**動かしていない**）: `charlie-haley/omada_exporter` とその派生（Docker イメージ `rcooler/omada-exporter` など。Web API v2 と OpenAPI の両方に対応と説明）がある。Grafana 用のダッシュボードは、[Omada Overview（16343）](https://grafana.com/grafana/dashboards/16343)と [Omada Overview（20854）](https://grafana.com/grafana/dashboards/20854)。**コントローラー 6.3 に対応しているかは、どの資料にも明記がない。** 試して確かめる。
  - 時期: ~~移行（段階 1〜3）が落ち着いてから~~ → **段階 3b が完了した（2026-11-20）。VLAN・ポートの設定が固まったので、着手できる**（運用者が、やりたいことの 1 つに挙げた、2026-11-20）。[ネットワーク通信の収集・可視化](06-network-traffic-analysis.md)とは目的が違う（こちらは機器の状態と使用量、06 はパケットレベルの通信）。
  - 採用を決めたら、設計書（[監視・アラート](../../architecture/lld/platform/monitoring.md)、[Omada コントローラー](../../architecture/lld/network/omada-controller.md)）と ADR に移す。
- [ ] **検討中**: AdGuard Home のダッシュボードを Grafana で見られるようにする（2026-11-20、運用者の希望。上の Omada と同じ仕組みに載せる）。**採用は未決定**。
  - 動機: 今の監視は、AdGuard への名前解決の成否（blackbox の `dns-lab`・`dns-external`）だけ。クエリ数、ブロック率、上流の応答時間、クライアントごとの件数などは、AdGuard の画面でしか見られない。
  - 見たいもの（**未決定**）: クエリ数、ブロックされた件数と率、平均の処理時間、上位のクライアント・ドメイン、保護の有効・無効。
  - 方法の候補（**未検証**。2026-11-20 に検索で調べただけ）:
    - (1) `henrywhitaker3/adguard-exporter`（Prometheus の exporter。1 つで複数の AdGuard を見られる。`:9618`）と、Grafana の[ダッシュボード 20799](https://grafana.com/grafana/dashboards/20799)。調べた中で、一番素直な組み合わせ。
    - (2) `JonanekDev/AdGuardHome-Exporter` と[ダッシュボード 24520](https://grafana.com/grafana/dashboards/24520)（複数の AdGuard 向け）。
    - (3) GeoIP や、クライアントの地域のパネルが欲しいなら、[ダッシュボード 24856](https://grafana.com/grafana/dashboards/24856)（別の Go の exporter）。
    - 古い `ebrianne/adguard-exporter` を前提にしたダッシュボード（13330、14038）は、元のプロジェクトが無くなっているので、避ける。
    - どの exporter も、公開されている最新の状態は、**導入の前に GitHub で確かめる**。
  - 置き場所: exporter は、`vm-monitoring`（Servers。Prometheus と Grafana がある）に Docker で置き、`vm-infra` の AdGuard の API（`:3000`）を見る案。AdGuard の管理者の認証情報は、SOPS に入れる（読み取りだけの用途でも、管理者のユーザーが要る。専用のユーザーを作れるかは、確かめる）。UFW は、`vm-monitoring` からだけ許可する。
  - **`vm-infra` の分割（上の項目）との関係**: AdGuard は、DNS の LXC に移る。exporter が見る先の IP が変わるので、**分割の前に入れるなら、移したあとに、`prometheus.yml` の対象を直す**。LXC の IP を、今の `10.77.20.10` から引き継げば、直さずに済む。
  - 既存の仕組み: Grafana のダッシュボードは `docker/compose/monitoring/grafana/dashboards` と `provisioning` で、コードで入れている。取り込んだダッシュボードも、同じ形（JSON をリポジトリに置く）にする。アラート（Prometheus のルール）を足すかは、実測を見てから決める。
  - 採用を決めたら、設計書（[監視・アラート](../../architecture/lld/platform/monitoring.md)、[DNS](../../architecture/lld/network/dns.md)）と ADR に移す。
- [ ] **検討中**: 詳細設計書を整備し、「文書が先」の運用にする（2026-11-20、運用者の希望）。**運用の分け方と構成図の運用は、採用し、`CLAUDE.md` に反映した（2026-11-20）。抽出スクリプト、詳細設計書の置き場所、差分の検査は、未決定**。
  - やりたいこと: (1) Omada、Tailscale、AdGuard Home などの設定値を、詳細設計書として文書にする。(2) 構成を変えるときは、文書を更新してから変える。(3) Omada のバックアップファイルから、スクリプトで設定値を抽出して、詳細設計書を作れないか。
  - 今ある文書: 機器の設定値は `docs/architecture/lld/hardware/<機器>/settings.md`、Omada は [Omada コントローラー](../../architecture/lld/network/omada-controller.md)、DNS と Tailscale は [DNS 構成](../../architecture/lld/network/dns.md)。今の決まり（`CLAUDE.md`）は、「設定を変えたら、**同じ変更で**文書を更新する」。足りないのは、(a) 全項目をそろえること、(b) 実機との**差分の検査**、(c) 「先に書く」変更の線引き。
  - **運用の分け方と構成図の運用は、採用した（2026-11-20）**: 変更の種類で、文書が先か、同時かを分ける。構成図は、to-be を先に、as-is は実機の変更ごとに更新する。詳細は [ADR-0033](../../adr/0033-docs-first-by-change-type-and-diagram-order.md) と `CLAUDE.md`。
  - 文書は「あるべき姿」、抽出は「実際の姿」。**差分が、ドリフト（実機と文書のずれ）**。抽出スクリプトで実際の値を出し、設計書と比べる。
  - 抽出の方法（2026-11-20 の調べ。**未検証**）:
    - **Omada のバックアップファイル（`.cfg`）からは、おすすめしない。** 先頭がランダムに見える並びで（`PK` でも gzip でもない）、暗号化か独自形式の可能性が高い（中身は読んでいない）。復号の方法は、公開されていない。管理者の認証情報や Wi-Fi のパスワードも入る。
    - 候補: (1) **Open API**（公式。読み取り専用のクライアントを作り、認証情報は SOPS）。取得範囲（LAN、Wi-Fi、ポートのプロファイル、ACL）は**未確認**。スキーマが公開されていて、バージョンが変わっても壊れにくい。(2) `vm-omada` の MongoDB を、読み取りで直接見る。全部取れるが、内部のスキーマ（非公開）で、バージョンで壊れやすい。(3) 併用（取れる分は自動、残りは手書き）。**まず、Open API の取得範囲を調べる**。バックログの「設定のコード化」の項目（上）と、同じ API。
    - AdGuard Home: 設定ファイル（`AdGuardHome.yaml`）を、Ansible で配っている。文書は、そこから起こせる。
    - Tailscale: ACL は、公式の GitOps（`tailscale/gitops-acl-action`）で、リポジトリのファイル（HuJSON）にできる。**文書が先**の運用に、そのまま乗る。
  - 抽出した値の扱い（リポジトリは公開）: MAC アドレス、認証情報、Wi-Fi のパスワード、アカウントのハッシュは、**抽出の段階で落とす**（既存の決まり: 機器の MAC は書かない）。抽出した値は、手書きの文書と分けて置く案（例: `generated/`）。置き場所は、今の `docs/architecture/lld/` と `docs/architecture/lld/hardware/` を広げる案（新しい階層は作らない）。**未決**。
  - 決めること（未決）: 置き場所（上）。「文書が先」の変更の線引きの、細かい基準。`CLAUDE.md`（図の項を含む）と ADR への入れ方（採用を決めたあと）。差分の検査を、CI に入れるか、手元で実行するか。上の「ドキュメント体系を整理する」項目との前後（書式をそろえてから整備するほうが、手戻りが少ない）。
  - 採用を決めたら、運用の方針を `CLAUDE.md` と ADR に移す。
- [ ] **検討中**: ドキュメント体系を整理する（2026-11-09、運用者の希望）。**採用は未決定**。**移行（段階 1〜3）が終わったあとに行う**。移行の最中は構成と文書が頻繁に変わるので、先に整理しても、すぐに崩れる。
  - 文書の種類ごとの書式を決める: 設計書、ADR、Runbook、障害記録、ロードマップ、機器の設定の文書、サービス別の文書。見出しの構成、書く項目、日付・状態の書き方をそろえる。
  - 古くなった文書を削除・統合する: 移行前の構成の記述、完了した計画、役目を終えた検討記録。消す前に、経緯や判断の理由が ADR・障害記録に残っているかを確認し、消すものは一覧にして運用者が確認する。
  - 記載内容を、人間が読んで整理する: 運用者が通読して、重複、古い記述、書きすぎ・足りなさを直す。文書は Claude Code と一緒に書き足してきたので、機械的な点検では拾えない読みづらさを、人の目で見る。
  - ドキュメントの運用方法を明確化する: どの情報をどの文書に書くか（正の置き場所）、更新の契機、検討中と採用済みの分け方、見直しの頻度。今のルールは `docs/README.md` の「文書の運用」と `CLAUDE.md` に分かれているので、一本化するか（`CLAUDE.md` は参照だけにするか）も決める。文書の lint（今は markdownlint とリンク検査）を足すかも含める。
  - 進め方（案）: 文書の棚卸し（一覧、役割、最終更新）→ 方針を決める（書式、削除の基準）→ 領域ごとに少しずつ直す。方針は ADR に残す。
- [ ] **検討中**: Authentik による SSO（シングルサインオン）を試すか検討する（2026-11-09、運用者の希望）。**採用は未決定**。
  - 位置づけ: Authelia を見送った [ADR 0008](../../adr/0008-no-authelia.md) は、Authentik / Keycloak を「1.5GB の `vm-infra` と 1 人の利用に対して過剰」として見送っている。この項目はそれを覆すのではなく、**条件が変わったか、学習として試すか**を確かめるもの。ADR 0008 の再検討の条件（人や端末の増加、認証のないサービスの増加、管理画面への 2 要素認証）のどれに当たるか、または学習目的かを、最初に決める。
  - 決めること:
    - 目的: ログインの一元化、2 要素認証、認証のない画面（Prometheus・Alertmanager・Homepage）の保護、学習のどれか。
    - 置き場所: `vm-infra` は 1.5GB で足りない見込み（Authentik は PostgreSQL などの構成要素が要る。**必要なメモリは未確認**）。新しい VM を作るか、`vm-apps` に置くか。VLAN 化（[Omada 導入・VLAN 化](04-network-omada-vlan.md)）の後の Servers の番号と合わせる。
    - 守り方: アプリが OIDC に対応していれば OIDC で連携する（Grafana と Proxmox は対応している。他のサービスは未確認）。対応していない画面は、Caddy の前段認証（forward auth）で守る。ただし、Caddy を通らないポート直打ちは素通りになる（ADR 0008 の理由 4）。
    - 止まったときの扱い: Authentik が落ちると、連携した画面に入れなくなる。各サービスのローカル管理者のログインを残す（緊急用）。特に Proxmox と Grafana。`vm-omada` を別のハードへ移す検討（上の項目）と同じ、依存の向きの問題。
    - 秘密値: クライアントの鍵と Authentik の初期設定は SOPS に入れる。バックアップは、DB と設定をどうするか（[ADR 0001](../../adr/0001-no-vm-backup.md) の方針と合わせる）。
  - 時期: **移行（段階 1〜3）が落ち着いてから**。アドレスと VLAN が固まる前に置くと、作り直しになる。
  - 採用するなら、新しい ADR で ADR 0008 を置き換える（ステータスを「置き換え済み」にする）。そのあとで、設計書（[セキュリティ](../../architecture/hld/06-security.md)）に移す。
- [ ] k3s などのクラスタ構成を検討する（学習用クラスタとして分離運用し、Grafana / PVE / AdGuard Home 等の安定稼働中サービスは当面 Docker Compose のまま維持する）。より重いワークロードや複数アプリの分離運用もここで扱う

## ハードウェア・拡張

- [ ] NAS の導入（TrueNAS）。**将来は、NAS 専用機で TrueNAS を動かしたい**（2026-11-20、運用者の考え）。その前の段階として、下の「USB SSD の NAS」を試す。導入後は、PBS / restic による自動バックアップ（[ADR 0001](../../adr/0001-no-vm-backup.md)）と、Home Assistant の `.storage/` と履歴の保護（[ADR 0011](../../adr/0011-home-assistant-on-vm-apps.md) の再検討の条件）も見直す

- [ ] **検討中**: Proxmox ホストに USB の外付け SSD を付けて、NAS にする（USB SSD の NAS。2026-11-20、運用者の構想。**設計は未決定**）。将来の専用機（上の TrueNAS）の前の段階。
  - 決めたこと（運用者、2026-11-20）: 用途は、**ファイル共有**と**写真・動画の管理**。方式は、**ホストでマウントして、LXC の Samba で配る**。容量は **1TB 前後**で、消えても困らないものが中心。バックアップ先（vzdump、PBS、restic）は、今回の用途に入れていない。
  - 前提: ホスト（ThinkCentre M70q Tiny）には PCIe スロットがなく、外付けは USB だけ。内蔵の NVMe は 256GB の 1 枚で、プールの空きは小さい（[ハードウェア](../../architecture/lld/hardware/thinkcentre-m70q-tiny/spec.md)）。冗長化はしない（SSD 1 台。壊れたら、データは消える）。
  - 見立て（**未検証**）:
    - ディスク: 背面の USB 3.2 Gen 2 に直接つなぐ（ハブを通さない）。UASP 対応のケース。給電と熱に注意。ファイルシステムは **ext4**（ZFS は USB だと不安定になりやすい）。`/etc/fstab` に UUID で書き、**`nofail`** にする（ディスクが外れていても、ホストが起動する）。
    - LXC: 特権なしの LXC に、ホストのマウント先を bind マウントし、Samba を**パッケージで**入れる。特権なしの LXC は UID がずれるので、共有用の UID・GID の対応（idmap）を決める。メモリは軽い（100〜200MB 程度）。
    - 置き場所: Servers の未使用の帯（`.40–.49`。[ADR-0027](../../adr/0027-servers-octet-bands-and-emergency-dns.md)）に置く案。VMID は規則（[ADR-0026](../../adr/0026-vmid-from-vlan-and-octet.md)）に従い、`2040` など。Trusted から SMB（445/tcp）で入るので、ACL を絞るときに許可を足す。外出先からは、Tailscale のサブネットルーターが `10.77.20.0/24` を広告しているので、入れる。
    - 写真・動画: アプリ（Immich など。[サービスカタログ](../../homelab-service-catalog.md)では未検討）は `vm-apps` に置き、**DB は内蔵の NVMe**、原本だけを NAS（SMB か NFS）に置く。
    - 監視: node_exporter のファイルシステムの使用率、マウントの有無（外れたときのアラート）。SMART は、USB ブリッジ越しに見えないことがある（`smartctl -d sat` を試す）。
  - **リスクと未決**:
    - 写真の原本は、取り直せない。「消えても困らない」とのずれがある。写真の原本は、元の端末にも残すか、別の場所に二次バックアップを取るか、決める。
    - USB の切断（ケーブル・給電・省電力）で、I/O エラーが出る。外れたときの挙動（Samba の LXC が固まらないか）を、試す。
    - SSD の製品・容量・つなぐ USB ポート。共有の構成（フォルダ、ユーザー）。VLAN・IP（上）。
  - 将来の専用機（TrueNAS）への引っ越し: 共有名・フォルダの構成・UID を、あとで写せるようにそろえておく（`rsync` でデータを移す）。
  - 順序: LXC を Terraform・Ansible で管理する流れは、`vm-infra` の分割（上の項目）と共通。**DNS・プロキシは止まると影響が大きいので、止まっても困らない、この NAS の LXC を、最初の LXC として試す**案がある。ACL を絞るあと（運用者の考え）に、どちらを先にするかも決める。
  - 採用を決めたら、設計書（[システム構成・環境](../../architecture/hld/01-system.md)、[監視・アラート](../../architecture/lld/platform/monitoring.md)）と ADR に移す。
- [ ] UPS 導入と自動シャットダウン

## ホームオートメーション

- [ ] Home Assistant の機器の検出と VLAN を決める（[VLAN 化](04-network-omada-vlan.md)と合わせて。Servers から Trusted・IoT への mDNS の中継か、置き場所の変更。Cast や Matter を使う前に）
- [ ] MQTT (Mosquitto) + ESP32 連携

  ```plaintext
  ESP32 → MQTT → HomeAssistant → Prometheus → Grafana
  ```

- [ ] **検討中**: SwitchBot Hub 2 の温度・湿度（将来は CO2 濃度）を監視し、しきい値を超えたら Slack にアラートを送る（2026-11-09、運用者の希望）。**採用は未決定**。
  - 今の状態: Home Assistant が SwitchBot Cloud 経由で値を取得し（`sensor.switchbot_hub_2_temperature` / `sensor.switchbot_hub_2_humidity`）、Homepage のウィジェットが HA から表示している（[Homepage](../../architecture/lld/apps/homepage.md)、[Home Assistant](../../architecture/lld/apps/home-assistant.md)）。**現在値を見るだけで、履歴もアラートも無い**。
  - CO2: 今の Hub 2 では取れない前提（運用者の話。機種の仕様は未確認）。CO2 に対応するセンサーを足したときに、同じ仕組みに載せる（機種は未定）。
  - 方法の候補（**未調査・未検証**）: Home Assistant の Prometheus 連携でセンサーの値を Prometheus に出し、`alerts.yml` にルールを足す。既存の Alertmanager から Slack に送る経路をそのまま使え、Grafana に履歴も出る。上の ESP32 の流れ（HA → Prometheus → Grafana）と同じ経路にできる。
  - 決めること: 温度・湿度・CO2 のしきい値と継続時間、HA の認証情報（長期アクセストークン）の置き場所（SOPS）、SwitchBot Cloud のポーリング間隔（反応が遅い。API の上限は 1 日 10,000 回）で足りるか、センサーの値が途絶えたときの扱い（欠測の検知）。
  - 採用を決めたら、設計書（[監視・アラート](../../architecture/lld/platform/monitoring.md)、[Home Assistant](../../architecture/lld/apps/home-assistant.md)）と ADR に移す。

- [ ] IP カメラ + Frigate の導入
- [ ] メディアサーバーの導入（Jellyfin / Plex / Emby）
- [ ] テレビの統合

## 大型計画

- [ ] [Omada 導入・VLAN 化](04-network-omada-vlan.md)
- [ ] [GPU 搭載ゲーミング PC 兼ホームサーバー](05-gpu-pc.md)
- [ ] [ネットワーク通信の収集・可視化](06-network-traffic-analysis.md)（ntopng などでパケットレベルの通信を可視化）
- [ ] [DMZ と外部公開](07-dmz.md)（DMZ の VLAN にハニーポットや公開用 Web サーバーを置く）
- [ ] [OPNsense 導入](08-network-opnsense.md)（Omada・VLAN 化のあと。補助的に検証し、ER605 の後継にする）
- [ ] [ラックの導入と 3D プリントのマウント](09-rack.md)（10 インチラックに ThinkCentre Tiny・ER605・SG2210P を載せる。マウントは業者に印刷を頼む）
