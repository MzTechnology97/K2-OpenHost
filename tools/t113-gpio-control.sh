#!/bin/sh
set -eu

# Local T113 helper for the stock K2 Pro service GPIOs.
# It does not provide transport from the CM5; it is the endpoint that a future
# control plane may invoke. Use --dry-run for inspection.

GPIO_ROOT="${K2_GPIO_SYSFS:-/sys/class/gpio}"
DRY_RUN=0
CONFIRM_DISRUPTIVE=0

GPIO_MCU_PWR=140
GPIO_NOZZLE_CAM=162
GPIO_BUZZER=164
GPIO_USB_HUB_RST=165
GPIO_UDISK_PWR=210

usage() {
    cat <<'EOF'
Usage:
  t113-gpio-control.sh [--dry-run] [--confirm-disruptive] status
  t113-gpio-control.sh [--dry-run] [--confirm-disruptive] mcu-power on|off|cycle
  t113-gpio-control.sh [--dry-run] nozzle-camera on|off
  t113-gpio-control.sh [--dry-run] buzzer <milliseconds>
  t113-gpio-control.sh [--dry-run] [--confirm-disruptive] usb-hub assert|release
  t113-gpio-control.sh [--dry-run] udisk-power on|off

Disruptive operations are refused unless --confirm-disruptive is supplied.
EOF
}

log() { printf '%s\n' "$*"; }

write_value() {
    local value=$1
    local path=$2
    if [ "$DRY_RUN" -eq 1 ]; then
        log "WRITE $value > $path"
        return 0
    fi
    printf '%s\n' "$value" > "$path"
}

ensure_gpio() {
    local gpio=$1
    local dir="$GPIO_ROOT/gpio$gpio"
    local i=0
    if [ ! -d "$dir" ]; then
        write_value "$gpio" "$GPIO_ROOT/export"
        if [ "$DRY_RUN" -eq 0 ]; then
            while [ ! -d "$dir" ] && [ "$i" -lt 20 ]; do
                sleep 0.01
                i=$((i + 1))
            done
            [ -d "$dir" ] || { log "GPIO$gpio did not appear after export" >&2; exit 1; }
        fi
    fi
    write_value out "$dir/direction"
}

set_gpio() {
    local gpio=$1
    local value=$2
    ensure_gpio "$gpio"
    write_value "$value" "$GPIO_ROOT/gpio$gpio/value"
}

require_disruptive() {
    if [ "$CONFIRM_DISRUPTIVE" -ne 1 ]; then
        log "Refusing disruptive GPIO operation without --confirm-disruptive" >&2
        exit 2
    fi
}

show_one() {
    local name=$1
    local gpio=$2
    local dir="$GPIO_ROOT/gpio$gpio"
    local value
    if [ -r "$dir/value" ]; then
        value=$(cat "$dir/value")
        printf '%-16s gpio%-3s value=%s\n' "$name" "$gpio" "$value"
    else
        printf '%-16s gpio%-3s not-exported\n' "$name" "$gpio"
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --confirm-disruptive) CONFIRM_DISRUPTIVE=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) break ;;
    esac
done

[ $# -ge 1 ] || { usage; exit 2; }
cmd=$1
shift

case "$cmd" in
    status)
        [ $# -eq 0 ] || { usage; exit 2; }
        show_one mcu_power "$GPIO_MCU_PWR"
        show_one nozzle_camera "$GPIO_NOZZLE_CAM"
        show_one buzzer "$GPIO_BUZZER"
        show_one usb_hub_reset "$GPIO_USB_HUB_RST"
        show_one udisk_power "$GPIO_UDISK_PWR"
        ;;

    mcu-power)
        [ $# -eq 1 ] || { usage; exit 2; }
        case "$1" in
            on) set_gpio "$GPIO_MCU_PWR" 0 ;;
            off) require_disruptive; set_gpio "$GPIO_MCU_PWR" 1 ;;
            cycle)
                require_disruptive
                set_gpio "$GPIO_MCU_PWR" 1
                if [ "$DRY_RUN" -eq 1 ]; then log "SLEEP 2"; else sleep 2; fi
                set_gpio "$GPIO_MCU_PWR" 0
                ;;
            *) usage; exit 2 ;;
        esac
        ;;

    nozzle-camera)
        [ $# -eq 1 ] || { usage; exit 2; }
        case "$1" in
            on) set_gpio "$GPIO_NOZZLE_CAM" 0 ;;
            off) set_gpio "$GPIO_NOZZLE_CAM" 1 ;;
            *) usage; exit 2 ;;
        esac
        ;;

    buzzer)
        [ $# -eq 1 ] || { usage; exit 2; }
        ms=$1
        case "$ms" in *[!0-9]*|'') log "milliseconds must be an integer" >&2; exit 2 ;; esac
        [ "$ms" -gt 0 ] || ms=100
        [ "$ms" -le 30000 ] || ms=30000
        set_gpio "$GPIO_BUZZER" 1
        seconds=$(awk "BEGIN { printf \"%.3f\", $ms / 1000 }")
        if [ "$DRY_RUN" -eq 1 ]; then log "SLEEP $seconds"; else sleep "$seconds"; fi
        set_gpio "$GPIO_BUZZER" 0
        ;;

    usb-hub)
        [ $# -eq 1 ] || { usage; exit 2; }
        case "$1" in
            assert) require_disruptive; set_gpio "$GPIO_USB_HUB_RST" 1 ;;
            release) set_gpio "$GPIO_USB_HUB_RST" 0 ;;
            *) usage; exit 2 ;;
        esac
        ;;

    udisk-power)
        [ $# -eq 1 ] || { usage; exit 2; }
        case "$1" in
            on) set_gpio "$GPIO_UDISK_PWR" 0 ;;
            off) set_gpio "$GPIO_UDISK_PWR" 1 ;;
            *) usage; exit 2 ;;
        esac
        ;;

    *) usage; exit 2 ;;
esac