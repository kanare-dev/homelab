# 障害時切り分け

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
