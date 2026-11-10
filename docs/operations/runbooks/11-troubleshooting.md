# 障害時切り分け

## Proxmox ホストと全 VM に、LAN から届かない

Mac から `192.168.11.10`（Proxmox）、`.11`、`.12` などに届かず、ER605（`192.168.11.1`）と `1.1.1.1` には届く。外部の Heartbeat が途絶し、Slack には何も届かない。**前回（[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）は NIC の送信停止、今回（[INC-2026-11-08](../incidents/2026-11-08-sg2210p-native-vlan-overwrite.md)）は SG2210P の p2 の VLAN 設定の書き換え**だった。症状が似ているので、次の順で切り分ける。

**直前に、SG2210P・ER605・Omada のネットワークやポートの設定を触ったか**を、まず思い出す。触っていれば、そちらが先に疑わしい。

```text
1. Proxmox にモニターとキーボードを繋ぐ（成功すれば使わない保険。夜間でもすぐ繋げるよう、場所を決めておく）
2. ログインして、次を実行する
   dmesg | grep -i "Hardware Unit Hang" | tail -3     # NIC の送信停止
   journalctl -k | grep -i nic0 | tail -20             # リンクの上下の時刻
   ethtool nic0 | grep -i "Link detected"
   ping -c 3 192.168.11.1                              # ホストから ER605 に届くか
3. 判定
   - Hang あり            → NIC の送信停止。ip link set nic0 down; sleep 2; ip link set nic0 up。だめなら reboot
   - Hang なし、リンクあり、.1 に届かない → SG2210P の p2 の側（VLAN 設定など）。次の「切り戻し」へ
```

**切り戻し（コントローラーを使わずに、Proxmox を LAN に戻す）**: コントローラー（`vm-omada`）は Proxmox の上にあるので、Proxmox が LAN から消えると、**コントローラーから直せない**。次のようにする。

1. Proxmox の LAN ケーブルを、SG2210P の p2 から外し、**ER605 の LAN ポート**（WAN/LAN3 など。Native が Default で、タグなし）に、直接挿す。SG2210P を迂回する。
2. `ping -c 3 192.168.11.1`（ホストから）。届けば、原因は SG2210P 側。`vm-omada` も戻る。
3. コントローラーに、**IP で**入る（`https://192.168.11.12:8043`。証明書の警告は進む。`omada.lab` は DNS に依存するので、DNS が落ちているときは使えない）。
4. SG2210P の p1〜p4 の VLAN Configuration（Devices → `sg2210p` → Ports → Edit Port）を見て、**Native が Default(1) か、Network Tags が Allow All か**を確認し、直す。
5. 直したら、ケーブルを p2 に戻し、`ping -c 3 192.168.11.1` を確認する。

## VM が応答しない

```text
1. ping で疎通確認
   $ ping 192.168.11.XX

2. Proxmox Web UI で VM のステータス確認
   → https://192.168.11.10:8006

3. Proxmox コンソールで起動状況を確認
   → Web UI > VM > Console
   ※ SSH が使えないときは、コンソールから `ubuntu` でログインできる
     （全 VM 共通のパスワード。iCloud Keychain `homelab / vm ubuntu password`）。
     `root` はロックされているので、必要なら `sudo -i`（パスワード不要）。
     SSH はパスワード認証を無効にしている（鍵のみ）。

4. VM を再起動
   $ ssh root@192.168.11.10 "qm reboot <vmid>"

5. VM を強制停止・起動
   $ ssh root@192.168.11.10 "qm stop <vmid> && qm start <vmid>"
```

## サービスが応答しない

```text
1. Docker コンテナのステータス確認
   $ docker compose ps

2. ログ確認
   $ docker compose logs --tail=50 <service>

3. コンテナ再起動
   $ docker compose restart <service>

4. コンテナ再作成
   $ docker compose up -d --force-recreate <service>
```

## DNS が引けない

```text
1. CoreDNS のステータス確認
   $ ssh ubuntu@192.168.11.11 "systemctl status coredns"

2. CoreDNS のログ確認
   $ ssh ubuntu@192.168.11.11 "journalctl -u coredns --tail=50"

3. 直接クエリして確認
   $ dig @192.168.11.11 grafana.lab.kanare.dev

4. CoreDNS を再起動
   $ ssh ubuntu@192.168.11.11 "sudo systemctl restart coredns"
```

## `vm-infra` の停止で名前解決が止まったとき（仕事用 PC）

DHCP が配る DNS は `vm-infra`（AdGuard）だけで、フォールバックは配っていない（理由と、受け入れたリスクは [ADR-0024](../../adr/0024-dhcp-dns-single-no-fallback.md)）。`vm-infra` が止まると、家のネットワークの名前解決が止まる。

仕事用の Windows PC は、会社の方針で DNS の設定を変えられない。会社の VPN の接続先が、ホスト名なら、VPN に繋ぎ直すときに、家の DNS が要る。

```text
1. vm-infra の復旧を試す（上の「VM が応答しない」「DNS が引けない」）

2. 仕事に間に合わないときは、仕事用 PC を、家のネットワークから外す
   - 壁の WAN から出ている Wi-Fi（建物の共用ルーターの Wi-Fi）に、直接繋ぐ
   - 家のホームラボから独立しているので、vm-infra が止まっていても使える

3. 復旧したら、家の Wi-Fi に戻す
```

- 建物の Wi-Fi の SSID とパスワードの所在は、台帳（Keychain）に記録しておく。
- 実際に止まって困る頻度が高ければ、別の対策を検討する（別の VM に 2 つ目の AdGuard を立てる、など。ホストが止まる場合は効かない）。
- 更新や再起動で `vm-infra` を止めるのは、勤務時間の外にする。

## Prometheus がスクレイプに失敗

```text
1. Prometheus の Targets ページを確認
   → https://prometheus.lab.kanare.dev/targets

2. ターゲット VM の node_exporter を確認
   $ ssh vm-monitoring curl -s http://192.168.11.XX:9100/metrics | head   # node_exporter は vm-monitoring からしか届かない

3. ファイアウォール確認
   $ ssh ubuntu@192.168.11.XX "sudo ufw status"

4. node_exporter を再起動
   $ ssh ubuntu@192.168.11.XX "sudo systemctl restart node_exporter"
```

## Grafana にログインできない

```text
1. Grafana のステータス確認
   $ docker compose -f /opt/monitoring/docker-compose.yml ps grafana

2. パスワードリセット
   $ docker compose -f /opt/monitoring/docker-compose.yml exec grafana \
       grafana cli admin reset-admin-password <new-password>
```
