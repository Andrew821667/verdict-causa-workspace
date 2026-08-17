#!/usr/bin/env bash
# Автозапуск стенда после перезагрузки машины.
#
#   ./deploy/autostart.sh          установить и запустить
#   ./deploy/autostart.sh --remove снять
#
# Ставится служба уровня системы (LaunchDaemon). LaunchAgent здесь не подходит:
# он живёт в сессии вошедшего пользователя, а по ssh такой сессии нет — при
# установке `launchctl` на нём отказал молча. LaunchDaemon стартует при загрузке
# машины, до чьего-либо входа в систему.
#
# Сам стенд работает от обычного пользователя: права root нужны только для того,
# чтобы служба поднималась при старте.

set -euo pipefail

cd "$(dirname "$0")/.."
root="$(pwd)"

label="com.verdictcausa.stand"
target="/Library/LaunchDaemons/$label.plist"

if [ "${1:-}" = "--remove" ]; then
	sudo launchctl bootout "system/$label" 2> /dev/null || true
	sudo rm -f "$target"
	echo "Автозапуск снят. Работающий процесс не тронут."
	exit 0
fi

port="$(cat "$root/deploy/local/port" 2> /dev/null || true)"
if [ -z "$port" ]; then
	echo "Порт не найден: сначала выполните ./deploy/configure.sh" >&2
	exit 1
fi

if [ ! -x "$root/.venv/bin/python" ]; then
	echo "Не найден $root/.venv/bin/python — сначала ./deploy/install.sh" >&2
	exit 1
fi

logs="$HOME/Library/Logs"
mkdir -p "$logs"

echo "Служба:       $label"
echo "Пользователь: $(id -un)"
echo "Каталог:      $root"
echo "Порт:         $port (только 127.0.0.1)"
echo

# Прежний LaunchAgent, если он остался от установки, снимается: две службы с
# одной меткой — источник путаницы, а не запаса прочности.
launchctl bootout "gui/$(id -u)/$label" 2> /dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/$label.plist" 2> /dev/null || true
rm -f "$HOME/Library/LaunchAgents/$label.plist"

tmp="$(mktemp -t verdict-causa-daemon)"
sed \
	-e "s|ПОЛЬЗОВАТЕЛЬ|$(id -un)|g" \
	-e "s|КАТАЛОГ_ПРОЕКТА|$root|g" \
	-e "s|КАТАЛОГ_ЖУРНАЛОВ|$logs|g" \
	-e "s|ПОРТ_СТЕНДА|$port|g" \
	"$root/deploy/com.verdictcausa.stand.daemon.plist" > "$tmp"

if grep -q "ПОЛЬЗОВАТЕЛЬ\|КАТАЛОГ_ПРОЕКТА\|КАТАЛОГ_ЖУРНАЛОВ\|ПОРТ_СТЕНДА" "$tmp"; then
	echo "В собранном файле остались заглушки — подстановка не сработала." >&2
	exit 1
fi

# LaunchDaemon обязан принадлежать root и не быть доступным на запись другим:
# иначе launchd откажется его загружать.
sudo cp "$tmp" "$target"
sudo chown root:wheel "$target"
sudo chmod 644 "$target"
rm -f "$tmp"

# Останавливаем то, что уже запущено: и службу, и процесс, поднятый вручную.
sudo launchctl bootout "system/$label" 2> /dev/null || true
pkill -f "causa.ui.server" 2> /dev/null || true
sleep 1

sudo launchctl bootstrap system "$target"
sudo launchctl kickstart -k "system/$label" 2> /dev/null || true

echo "→ жду ответа стенда"
for _ in $(seq 1 45); do
	if curl -fsS --max-time 3 "http://127.0.0.1:$port/api/desktop" > /dev/null 2>&1; then
		cat <<DONE

Готово. Стенд поднимается сам после перезагрузки машины.

Проверить:   sudo launchctl print system/$label | head -20
Остановить:  sudo launchctl kickstart -k system/$label
Снять:       ./deploy/autostart.sh --remove
Журнал:      $logs/verdict-causa-stand.log
DONE
		exit 0
	fi
	sleep 2
done

echo "Служба установлена, но стенд не ответил на 127.0.0.1:$port за полторы минуты." >&2
echo "Последние строки журнала:" >&2
tail -20 "$logs/verdict-causa-stand-error.log" 2> /dev/null || true
exit 1
