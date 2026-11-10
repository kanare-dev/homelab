# MOTD（SSH ログイン時の表示）

各 VM に SSH でログインしたときに出る、ホスト名のバナーとシステム情報の表示。Ansible の `common` ロールが、全 VM に同じスクリプトを配る。VM ごとに設定を変える仕組みは無い。

| 内容 | 場所 |
| --- | --- |
| 表示のスクリプト | `ansible/roles/common/files/motd.sh`（変数を含まない素のシェルスクリプト。`copy` で配る） |
| 配布のタスク | `ansible/roles/common/tasks/main.yml`（「Install figlet」から「Disable motd-news」まで、apt の更新頻度の 3 タスク、「Disable SSH last login banner」） |
| 配布先 | `/etc/update-motd.d/99-custom`（所有者 root、権限 `0755`） |

## 表示の内容

上から順に次のものが出る。

| 項目 | 内容 |
| --- | --- |
| バナー | ホスト名を figlet（フォント `ansi-shadow`）で大きく表示。シアン |
| OS | OS 名とカーネルのバージョン |
| Hostname | ホスト名 |
| Uptime | 稼働時間（日・時間・分） |
| Load | ロードアベレージ（1・5・15 分）とコア数 |
| CPU | 使用率（0.1 秒間の差分で計測）。バーと % |
| Memory | 使用率と、使用量 / 総量（GB）。バーと % |
| Disk / | ルートファイルシステムの使用率と、使用量 / 総量。バーと % |
| IP | 外向きの通信に使う IP アドレス |
| 更新 | 更新可能なパッケージがあるときだけ「N updates available → apt upgrade」を赤で表示 |
| 再起動 | 再起動が必要なときだけ「System restart required」を黄で表示 |

ログイン履歴（Last login）は表示しない。Ubuntu 26.04 では `last` の仕組みが変わり、壊れても気づきにくいため、載せないことにした（[VM の OS を Ubuntu 26.04 に移行する計画](../../adr/0021-ubuntu-lts-for-vms.md)）。sshd の `PrintLastLog` も `no` にしているので、OpenSSH 標準の「Last login」行も出ない。

### バーの色

色の基準は、[Prometheus のアラート](monitoring.md)に合わせている。黄がアラートの warning、赤が critical に当たる。

| 項目 | 黄（これを超える） | 赤（これを超える） | 対応するアラート |
| --- | --- | --- | --- |
| CPU | 85% | 95% | HostCpuHigh / Critical（全コア平均 > 85% / 95%） |
| Memory | 使用率 90%（利用可能が 10% 未満） | 使用率 95%（利用可能が 5% 未満） | HostMemoryLow / Critical |
| Disk / | 80% | 90% | HostDiskUsageHigh / Critical |

アラートは一定時間続いたときに鳴る（CPU は 15 分など）。motd はログインした瞬間の値なので、一瞬の高負荷でも色が変わる。アラートの基準を変えたときは、`motd.sh` の `pick_pct_color` の呼び出しも同じ値に直す。

### 更新数

更新数は、`/var/lib/update-notifier/updates-available` の「N updates can be applied immediately.」の行から読む。このファイルは、Ubuntu が `apt update` の成功時と、dpkg の実行のたびに更新する。ログイン時に `apt` を動かすと約 2 秒かかるので、ファイルを読むだけにしている。

- 件数の行は 1 行目とは限らない（0 件のときは 1 行目が空）ので、行を探して読む
- 数字は `apt dist-upgrade` で入る件数。`apt upgrade` では入らない（保留される）ものも含む
- パッケージ一覧が古いと、更新数も古くなる。標準では一覧の更新が実質 1 日 1 回なので、`common` ロールが 6 時間ごとに更新するよう変えている（下の「配布の仕組み」）

## 配布の仕組み

`common` ロールは、次のことを行う。

1. `figlet` をインストールし、フォント `ansi-shadow` を `/usr/share/figlet/` に取得する（コミットとチェックサムを固定。下の「フォントのライセンスと更新」）
2. スクリプトを `/etc/update-motd.d/99-custom` に配置する
3. Ubuntu の標準の MOTD スクリプト（`/etc/update-motd.d/` の他のファイル）の実行権限を外し、標準の表示を出さない（シンボリックリンクは、リンク先を `dpkg-statoverride` で止める。下の「標準の MOTD の無効化」）
4. `motd-news.service` と `motd-news.timer` を停止して無効化・マスクする（Ubuntu の広告つきニュース表示を止める）
5. sshd の `PrintLastLog` を `no` にする
6. `apt-daily.timer` を 6 時間ごと（0・6・12・18 時、最大 30 分の遅延）に動かし、`APT::Periodic::Update-Package-Lists` を `always` にして、実行のたびにパッケージ一覧を更新する（`/etc/systemd/system/apt-daily.timer.d/override.conf` と `/etc/apt/apt.conf.d/52apt-update-always`）。無人の自動更新（`apt-daily-upgrade`）の時刻は変えない

適用の対象は、`site.yml` が指す `infra`、`monitoring`、`apps`、`dev`、`code` の各 VM。`apps.yml`、`monitoring.yml`、`code.yml` は `common` を含むが、**`infra.yml` は含まない**ので、`vm-infra` に反映するには `site.yml` を使う。**Proxmox ホスト（`pve`）には配らない**（`proxmox.yml` に `common` が無い）。

```bash
# 全 VM に適用
cd ansible && ansible-playbook playbooks/site.yml

# 変更だけ確認する（dry-run）
cd ansible && ansible-playbook playbooks/site.yml --check --diff
```

## フォントのライセンスと更新

フォント（`ansi-shadow`、元の名前は `ANSI Shadow.flf`）は、リポジトリに**置かない**。

- 配布元の [xero/figlet-fonts](https://github.com/xero/figlet-fonts) に、ライセンスの記載が無い（GitHub のライセンス欄が空で、LICENSE ファイルも無い。README は使い方だけ）
- フォントのファイルの中にも、作者の記載が「Font Author: ?」とあるだけで、再配布の条件が分からない
- ライセンスが明示されていないものは、既定では再配布できないので、リポジトリには入れない

代わりに、取得するコミット（`fbf3b68…`、フォントを最後に変更したコミット）と、ファイルの SHA-256 を固定している。配布元が書き換わっても、中身が変わったら Ansible が失敗する。取得は各 VM が配布元から直接行い、このリポジトリでは再配布しない。

フォントを更新するとき（または別のフォントに変えるとき）は、次の手順で、コミットとチェックサムを確かめてから `tasks/main.yml` を差し替える。

```bash
# 最後にフォントを変更したコミットを調べる
gh api "repos/xero/figlet-fonts/commits?path=ANSI%20Shadow.flf&per_page=1" --jq '.[0].sha'

# そのコミットのファイルの SHA-256 を計算する
gh api -H "Accept: application/vnd.github.raw" \
  "repos/xero/figlet-fonts/contents/ANSI%20Shadow.flf?ref=<コミット>" | shasum -a 256
```

ライセンスが明確なフォント（figlet 本体に同梱のもの）に変えれば、取得が要らなくなる。

## 標準の MOTD の無効化

標準の MOTD スクリプト（`/etc/update-motd.d/` の `99-custom` 以外）は、実行権限を外して止めている。

| 対象 | 止め方 |
| --- | --- |
| 通常のファイル（`00-header`、`10-help-text`、`50-motd-news`、`85-fwupd`、`90-updates-available` など） | ファイルの権限を `0644` にする。リンクではないので、他のファイルには触らない |
| シンボリックリンク（`50-landscape-sysinfo`） | リンク先（`/usr/share/landscape/landscape-sysinfo.wrapper`、`landscape-common` パッケージのファイル）に、`dpkg-statoverride` で「所有者 root、権限 `0644`」を記録する |

シンボリックリンクのリンク先を `chmod` するだけだと、パッケージの更新で実行権限が戻り、標準の「System information」が次の Ansible 実行まで混ざって出る。`dpkg-statoverride` に記録すると、dpkg がパッケージの更新のたびにこの権限を適用するので、戻らない。

```bash
# 記録されている権限の上書きを見る
dpkg-statoverride --list /usr/share/landscape/landscape-sysinfo.wrapper
# → root root 0644 /usr/share/landscape/landscape-sysinfo.wrapper

# 記録を外す（標準の表示を戻したいとき）
sudo dpkg-statoverride --remove /usr/share/landscape/landscape-sysinfo.wrapper
sudo chmod 0755 /usr/share/landscape/landscape-sysinfo.wrapper
```

- 以前のタスクは、`find` の結果を `follow: true` で `chmod` していたため、リンク先の権限だけが変わり、パッケージの更新で戻る状態だった（2026-11-01 に実機の `vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code` で、リンク先が `0644` に変わっていることを確認した）。現在のタスクは、通常のファイルだけを `chmod` し、リンクは `dpkg-statoverride` に任せる
- 標準のスクリプトが増えたときも、`find` が見つけて同じ方法で止める
- `pve` は `common` ロールの対象外。`/etc/update-motd.d/10-uname` だけがあり、`landscape` の件は関係しない

## 注意点

- **Nerd Font が要る。** 更新と再起動の行の先頭のアイコンは Nerd Font の文字で、使っているターミナルのフォントが Nerd Font でないと、豆腐（□）や空白になる
- **ログインのたびに実行される。** スクリプトは root でログイン時に毎回動く。実行時間は約 0.15 秒（CPU の計測に 0.1 秒かかる）
- **シェルスクリプトは shellcheck で検査する。** `make shell-lint`（`make lint-all` に含まれる。CI も同じ）。ローカルでは `brew install shellcheck` が要る
- 表示を変えたいときは、`motd.sh` を直して、`site.yml` を再実行する。VM ごとに変える設定項目は無い
