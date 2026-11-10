#!/bin/bash
# /etc/update-motd.d/99-custom
# Managed by Ansible

# ── カラー ───────────────────────────────────────────────
RESET=$'\033[0m'
BOLD=$'\033[1m'
DIM=$'\033[2m'

RED=$'\033[91m'
GREEN=$'\033[92m'
YELLOW=$'\033[93m'
BLUE=$'\033[94m'
CYAN=$'\033[96m'
WHITE=$'\033[97m'
GRAY=$'\033[37m'

# ── 共通 ─────────────────────────────────────────────────
sep() {
  printf "${DIM}%s${RESET}\n" "────────────────────────────────────────────────────────"
}

row() {
  # $1=label $2=value_color $3=value
  printf "  ${DIM}%-10s${RESET}  ${2}%s${RESET}\n" "$1" "$3"
}

# 色の基準は Prometheus のアラート（docs/services/platform/monitoring.md）に合わせる。
# $1=使用率 $2=これを超えると黄（warning） $3=これを超えると赤（critical）
pick_pct_color() {
  local pct=$1 warn=$2 crit=$3
  if   [ "$pct" -gt "$crit" ]; then printf "%s" "$RED"
  elif [ "$pct" -gt "$warn" ]; then printf "%s" "$YELLOW"
  else                              printf "%s" "$GREEN"
  fi
}

bar() {
  local pct=$1
  local color=$2
  local width=20
  local filled=$(( pct * width / 100 ))
  local empty=$(( width - filled ))
  local f="" e="" i
  for ((i=0; i<filled; i++)); do f="${f}█"; done
  for ((i=0; i<empty;  i++)); do e="${e}░"; done
  printf "${DIM}[${RESET}${color}%s${RESET}${DIM}%s${DIM}]${RESET} ${color}%3d%%${RESET}" "$f" "$e" "$pct"
}

# ── システム情報 ────────────────────────────────────────
HOSTNAME=$(hostname -s 2>/dev/null || echo "unknown")

OS_NAME=$(awk -F= '/^PRETTY_NAME=/{gsub(/"/,"",$2); print $2}' /etc/os-release 2>/dev/null)
[ -z "$OS_NAME" ] && OS_NAME="$(uname -s)"

KERNEL=$(uname -r 2>/dev/null)

# uptime
UPTIME_SEC=$(awk '{print int($1)}' /proc/uptime 2>/dev/null)
UP_D=$(( UPTIME_SEC / 86400 ))
UP_H=$(( (UPTIME_SEC % 86400) / 3600 ))
UP_M=$(( (UPTIME_SEC % 3600) / 60 ))

if   [ "$UP_D" -gt 0 ]; then UPTIME_STR="${UP_D}d ${UP_H}h ${UP_M}m"
elif [ "$UP_H" -gt 0 ]; then UPTIME_STR="${UP_H}h ${UP_M}m"
else                          UPTIME_STR="${UP_M}m"
fi

# load
LOAD=$(awk '{print $1, $2, $3}' /proc/loadavg 2>/dev/null)
CORES=$(nproc 2>/dev/null || echo "?")
LOAD_STR="${LOAD}  (${CORES} cores)"

# cpu (0.1秒間のデルタ計測)
read_cpu() {
  awk '/^cpu /{print $2, $5; exit}' /proc/stat
}
CPU1=$(read_cpu)
sleep 0.1
CPU2=$(read_cpu)
CPU_PCT=$(awk -v a="$CPU1" -v b="$CPU2" 'BEGIN {
  split(a,x," "); split(b,y," ");
  d=y[2]-x[2];
  if (d>0) printf "%d", ((y[1]-x[1])*100/d);
  else print 0
}')
# HostCpuHigh / Critical: > 85% / 95%
CPU_COLOR=$(pick_pct_color "$CPU_PCT" 85 95)

# memory
MEM_TOTAL=$(awk '/^MemTotal:/{print $2}'    /proc/meminfo 2>/dev/null)
MEM_AVAIL=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo 2>/dev/null)
MEM_USED=$(( MEM_TOTAL - MEM_AVAIL ))
MEM_PCT=$(( MEM_USED * 100 / MEM_TOTAL ))
MEM_USED_G=$(awk "BEGIN {printf \"%.1f\", $MEM_USED/1048576}")
MEM_TOTAL_G=$(awk "BEGIN {printf \"%.1f\", $MEM_TOTAL/1048576}")
# HostMemoryLow / Critical: 利用可能 < 10% / 5%（使用率 > 90% / 95%）
MEM_COLOR=$(pick_pct_color "$MEM_PCT" 90 95)

# disk
read -r DISK_PCT DISK_USED DISK_TOTAL <<EOF
$(df -hP / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print int($5), $3, $2}')
EOF
[ -z "$DISK_PCT"   ] && DISK_PCT=0
[ -z "$DISK_USED"  ] && DISK_USED="N/A"
[ -z "$DISK_TOTAL" ] && DISK_TOTAL="N/A"
# HostDiskUsageHigh / Critical: > 80% / 90%
DISK_COLOR=$(pick_pct_color "$DISK_PCT" 80 90)

# ip
IP_ADDR=$(ip route get 1.1.1.1 2>/dev/null | awk '/src/ {for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
[ -z "$IP_ADDR" ] && IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP_ADDR" ] && IP_ADDR="N/A"

# updates
# update-notifier が apt update と dpkg の実行のたびに更新するファイルから読む。
# 件数の行は 1 行目とは限らない（0 件のときは 1 行目が空）ので、行を探して読む。
UPDATE_COUNT=$(grep -m1 -oE '^[0-9]+ update' /var/lib/update-notifier/updates-available 2>/dev/null | grep -oE '^[0-9]+')
UPDATE_COUNT=${UPDATE_COUNT:-0}

# reboot required
REBOOT_REQUIRED=0
[ -f /var/run/reboot-required ] && REBOOT_REQUIRED=1

# ── 出力 ────────────────────────────────────────────────
echo ""

if command -v figlet >/dev/null 2>&1; then
  figlet -f ansi-shadow "$HOSTNAME" | while IFS= read -r line; do
    printf "${CYAN}%s${RESET}\n" "$line"
  done
else
  printf "${BOLD}== %s ==${RESET}\n" "$HOSTNAME"
fi

echo ""
printf "  ${DIM}%-6s${RESET}  ${BLUE}%s${RESET}  ${DIM}│${RESET}  ${GRAY}%s${RESET}\n" \
  "OS" "$OS_NAME" "$KERNEL"

echo ""
sep

row "Hostname" "$WHITE" "$HOSTNAME"
row "Uptime"   "$GREEN" "$UPTIME_STR"
row "Load"     "$CYAN"  "$LOAD_STR"

printf "  ${DIM}%-10s${RESET}  " "CPU"
bar "$CPU_PCT" "$CPU_COLOR"
echo ""

printf "  ${DIM}%-10s${RESET}  " "Memory"
bar "$MEM_PCT" "$MEM_COLOR"
printf "  ${DIM}%sG / %sG${RESET}\n" "$MEM_USED_G" "$MEM_TOTAL_G"

printf "  ${DIM}%-10s${RESET}  " "Disk /"
bar "$DISK_PCT" "$DISK_COLOR"
printf "  ${DIM}%s / %s${RESET}\n" "$DISK_USED" "$DISK_TOTAL"

row "IP" "$CYAN" "$IP_ADDR"

echo ""

if [ "$UPDATE_COUNT" -gt 0 ]; then
  printf "${RED}󰀦${RESET}  ${RED}%d updates available${RESET}  ${DIM}→ apt upgrade${RESET}\n" "$UPDATE_COUNT"
fi

if [ "$REBOOT_REQUIRED" -eq 1 ]; then
  printf '%s󰜗%s  %sSystem restart required%s\n' "$YELLOW" "$RESET" "$YELLOW" "$RESET"
fi

if [ "$UPDATE_COUNT" -gt 0 ] || [ "$REBOOT_REQUIRED" -eq 1 ]; then
  echo ""
fi

sep
echo ""
