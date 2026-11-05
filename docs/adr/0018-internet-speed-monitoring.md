# 0018. 回線は ping（ICMP）で監視し、Speedtest は回線を使い切るため見送る

- ステータス: 採用（未適用）
- 日付: 2026-11-01

## 背景

家のインターネット回線が落ちた時と、建物側のネットワークが遅くなった時に気づけるようにしたい。推移も見たい。
既存の監視（[監視・アラート](../services/platform/monitoring.md)）は、VM・ストレージ・HTTPS・DNS が対象で、回線の状態は見ていない。外形監視（blackbox）は LAN 内のサービスと、AdGuard 経由の名前解決だけで、回線断や遅延は分からない。

当初は、速度の定期測定（Ookla Speedtest を `speedtest-exporter` で 30 分毎）と、ping の併用を考えた。検討の途中で、日中は在宅で仕事をしているため、測定のたびに回線を使い切られるのは困る、という制約が出た。

## 決定

- blackbox-exporter の ICMP で、ルーター・建物の共用ルーター（`172.22.0.1`）・`1.1.1.1`・`8.8.8.8` に 30 秒毎に ping する。通信量はほぼゼロなので、仕事中も止めない。
- 回線断: ルーターに届くのに `1.1.1.1` と `8.8.8.8` の両方に届かない状態が 2 分続いたら `InternetDown`（critical）。回線断の間は、遅延・パケットロス・外の名前解決の失敗の通知を抑制する。
- 遅延: `1.1.1.1` への RTT（10 分平均）が、7 日間の中央値の 2 倍かつ 50ms 超で 10 分続いたら `InternetLatencyHigh`。パケットロス（10 分で 10% 超）も通知する。
- 推移は Grafana「Internet Connectivity」で見る。通知は既存の Alertmanager から Slack へ送る。
- **Speedtest による速度の定期測定は見送る**。理由と再検討の条件は [見送り中の項目](../operations/roadmap/03-deferred.md#回線速度の定期測定speedtest)。
- 家庭内 LAN（iperf3）と Wi-Fi 経由の測定は、将来の拡張とし、手順を文書に残す（[Wi-Fi 経由の測定](../services/platform/monitoring.md#wi-fi-経由の測定未実装)、[家庭内 LAN への拡張](../services/platform/monitoring.md#家庭内-lan-への拡張未実装)）。

## 理由

- 回線を使わない。仕事中のビデオ会議にも、建物の共用回線にも影響しない。
- ルーター → 建物の共用ルーター → インターネットの順に測るので、建物内の問題か、その先（ISP）かを切り分けられる。
- 既存の blackbox・Prometheus・Grafana・Alertmanager にそのまま載る。新しいコンテナや DB を足さない。
- 遅延の基準は固定の数字ではなく、7 日間の中央値との比較にする。回線を替えても追随する。

## 代替案

| 案 | 見送った理由 |
| --- | --- |
| speedtest-exporter（30 分毎） | 測定のたびに 30〜60 秒、回線を使い切る。Prometheus の scrape で測るため、時間帯（仕事中を避ける）を指定できない |
| Speedtest を systemd timer で夜間・休日だけ | 仕事中の影響は避けられるが、Ookla CLI のインストールと textfile 出力の実装が増える。ping で足りるかを見てから判断する（再検討の条件を参照） |
| MySpeed | 独自の DB と画面を持ち、Prometheus・Alertmanager に載らない。通知経路と画面が増える |
| LibreSpeed | 自分で立てたサーバーまでの速度を測るので、インターネット回線の速度にならない |
| 固定のしきい値 | 平常値を先に決める必要があり、回線を替えるたびに直す |

## 影響と再検討の条件

- ping は遅延とロスを見るもので、**速度（Mbps）は測らない**。遅延が増えずに帯域だけ絞られる場合は検知できない。
- `vm-monitoring` は有線なので、Wi-Fi の状態は測れない。有線と Wi-Fi の差は、手元の端末で測るか、将来 Wi-Fi 側の測定端末を足す。
- 回線断の間は Slack に通知できない。外部 Heartbeat（Healthchecks.io）の DOWN が先に届き、`InternetDown` は復旧後に届く（[ADR 0010](0010-external-heartbeat.md)）。
- 建物の共用ルーター宛ての ping は、ICMP に応答しない構成だと誤報になるため、確認用のグラフだけでアラートにしない。上流が変わったら（引っ越しなど）宛先を直す。
- 外れ値による誤報が多い、または見逃しが多い場合は、`alerts.yml` の `2`（倍率）、`0.05`（下限）、窓を調整する。
- Speedtest の再検討の条件は、[見送り中の項目](../operations/roadmap/03-deferred.md#回線速度の定期測定speedtest)にまとめている。
