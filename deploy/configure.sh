#!/usr/bin/env bash
# Настройка выпуска стенда «Резонанс» наружу: поддомен, почта, пароль.
#
# Скрипт спрашивает три значения и собирает из шаблонов рабочие файлы в
# deploy/local/. Он ничего не запускает и не открывает портов — как и install.sh.
#
# Почему отдельный скрипт, а не правка файлов руками. Правок три, и каждая
# молчаливо ломается по-своему: не тот поддомен — Caddy не получит сертификат,
# не та почта — Let's Encrypt не пришлёт предупреждение об истечении, не тот
# хэш — браузер будет спрашивать пароль и не пускать. Здесь же пароль
# проверяется вводом дважды, а готовый файл — командой caddy validate.
#
# Пароль нигде не сохраняется: он не печатается на экран, не попадает в
# аргументы команды (их видно в ps) и не пишется в файл — в файл идёт только
# bcrypt-хэш. Сами файлы deploy/local/ не попадают в git.

set -euo pipefail

cd "$(dirname "$0")/.."
root="$(pwd)"
out="$root/deploy/local"

mkdir -p "$out"

echo "Каталог проекта: $root"
echo

if ! command -v caddy > /dev/null; then
	echo "caddy не найден. Поставьте его: brew install caddy" >&2
	exit 1
fi

# --- Значения ---------------------------------------------------------------
# Переменные окружения нужны не для удобства, а чтобы скрипт можно было
# прогнать без человека при проверке; обычный путь — интерактивный ввод.

domain="${CAUSA_DOMAIN:-}"
while [ -z "$domain" ]; do
	read -r -p "Поддомен (например stand.example.com): " domain
done

email="${CAUSA_EMAIL:-}"
while [ -z "$email" ]; do
	read -r -p "Почта для Let's Encrypt (туда придёт предупреждение об истечении): " email
done

operator="${CAUSA_OPERATOR:-}"
if [ -z "$operator" ]; then
	read -r -p "Имя пользователя для входа [operator]: " operator
	operator="${operator:-operator}"
fi

password="${CAUSA_PASSWORD:-}"
while [ -z "$password" ]; do
	read -r -s -p "Пароль: " password
	echo
	read -r -s -p "Пароль ещё раз: " confirmation
	echo
	if [ "$password" != "$confirmation" ]; then
		echo "Пароли не совпали, попробуйте снова." >&2
		password=""
	elif [ "${#password}" -lt 12 ]; then
		echo "Стенд открыт в интернет: пароль короче 12 знаков не подойдёт." >&2
		password=""
	fi
done

# --- Хэш --------------------------------------------------------------------
# Через stdin, а не через --plaintext: аргументы команды видны в ps любому
# пользователю машины.

hash="$(printf '%s' "$password" | caddy hash-password 2> /dev/null || true)"
if [ -z "$hash" ]; then
	echo "caddy hash-password не вернул хэш — проверьте версию caddy." >&2
	exit 1
fi
unset password confirmation

# --- Файлы ------------------------------------------------------------------

logs="$HOME/Library/Logs"
mkdir -p "$logs"

python_bin="$root/.venv/bin/python"
if [ ! -x "$python_bin" ]; then
	echo "Не найден $python_bin — сначала запустите ./deploy/install.sh" >&2
	exit 1
fi

caddyfile="$out/Caddyfile"
umask 077
sed \
	-e "s|you@example.com|$email|" \
	-e "s|stand\.example\.com|$domain|" \
	-e "s|operator ЗАМЕНИТЕ_НА_ХЭШ|$operator $hash|" \
	-e "s|/var/log/caddy/verdict-causa\.log|$logs/verdict-causa-caddy.log|" \
	"$root/deploy/Caddyfile" > "$caddyfile"
chmod 600 "$caddyfile"

plist="$out/com.verdictcausa.stand.plist"
sed \
	-e "s|/Users/ВАШ_ПОЛЬЗОВАТЕЛЬ/verdict-causa|$root|g" \
	-e "s|/Users/ВАШ_ПОЛЬЗОВАТЕЛЬ/Library/Logs|$logs|g" \
	"$root/deploy/com.verdictcausa.stand.plist" > "$plist"
chmod 644 "$plist"

# --- Проверки ---------------------------------------------------------------
# Файл, который не проходит caddy validate, лучше отклонить здесь, чем узнать
# об этом при первом запуске с открытым портом.

# Проверяются сами заглушки, а не строка «example.com»: поддомен пользователя
# теоретически может её содержать, и ложная тревога здесь хуже, чем её нет.
if grep -q "ЗАМЕНИТЕ_НА_ХЭШ\|ВАШ_ПОЛЬЗОВАТЕЛЬ\|you@example\.com" "$caddyfile" "$plist"; then
	echo "В собранных файлах остались заглушки — подстановка не сработала." >&2
	exit 1
fi

caddy validate --config "$caddyfile" > /dev/null
echo "→ конфигурация Caddy проверена"

cat <<NEXT

Готово. Собрано:

  $caddyfile   (права 600: внутри хэш пароля)
  $plist

Дальше — вручную, по deploy/README.md:

  cp "$plist" ~/Library/LaunchAgents/
  launchctl load ~/Library/LaunchAgents/com.verdictcausa.stand.plist
  launchctl start com.verdictcausa.stand
  curl -s http://127.0.0.1:8765/api/desktop | head -c 200

  sudo caddy run --config "$caddyfile"

Порты 80 и 443 должны быть проброшены на Mac mini, а A-запись
$domain — указывать на его внешний адрес: без порта 80
Let's Encrypt не подтвердит владение доменом.

Стенд слушает только 127.0.0.1:8765. Аутентификации в приложении нет —
без basic_auth в Caddy наружу его выпускать нельзя.
NEXT
