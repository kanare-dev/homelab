#!/usr/bin/env bash
# Unbound が再帰解決できているかを node_exporter の textfile collector 形式で出力する。
# AdGuard は fallback DNS を持つため、Unbound が止まっても利用者は気づけない。その盲点を埋める。
# キャッシュやキャッシュ切れの応答（serve-expired）に隠れないよう、毎回ランダムな未キャッシュの名前を引く。
# NOERROR / NXDOMAIN なら再帰解決できている。SERVFAIL・タイムアウトは失敗。systemd timer から 1 分間隔で実行する。
set -euo pipefail

OUT_DIR="${1:-/var/lib/node_exporter/textfile}"
OUT="${OUT_DIR}/unbound.prom"
TMP="$(mktemp "${OUT_DIR}/.unbound.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

name="unbound-probe-${RANDOM}${RANDOM}.example.com"
start="${EPOCHREALTIME/./}"
# タイムアウトで dig が非 0 終了しても、失敗として記録するために継続する（set -e で止まると古い値が残る）
status="$(dig @127.0.0.1 -p 5335 "$name" A +tries=1 +time=5 +noall +comments 2>/dev/null |
  awk '/status:/ { gsub(/,/, "", $6); print $6; exit }' || true)"
end="${EPOCHREALTIME/./}"
duration="$(awk -v s="$start" -v e="$end" 'BEGIN { printf "%.3f", (e - s) / 1000000 }')"

case "${status:-}" in
  NOERROR|NXDOMAIN) success=1 ;;
  *) success=0 ;;
esac

{
  echo "# HELP unbound_probe_success 1 if Unbound resolved an uncached name recursively (NOERROR or NXDOMAIN)."
  echo "# TYPE unbound_probe_success gauge"
  echo "unbound_probe_success $success"
  echo "# HELP unbound_probe_duration_seconds Time taken by the probe query."
  echo "# TYPE unbound_probe_duration_seconds gauge"
  echo "unbound_probe_duration_seconds $duration"
  echo "# HELP unbound_probe_last_run_timestamp_seconds Last run of this collector."
  echo "# TYPE unbound_probe_last_run_timestamp_seconds gauge"
  echo "unbound_probe_last_run_timestamp_seconds $(date +%s)"
} > "$TMP"

chmod 0644 "$TMP"
mv "$TMP" "$OUT"
trap - EXIT
