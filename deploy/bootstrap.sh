#!/usr/bin/env bash
# Полная установка стенда «Резонанс» на Mac mini одной командой.
#
#   ./deploy/bootstrap.sh
#
# Делает всё: окружение, сборку интерфейса, настройку, службу macOS и запуск
# Caddy. В отличие от install.sh и configure.sh, этот скрипт **включает** службу
# и **открывает стенд в интернет** — поэтому он один раз спрашивает
# подтверждение и показывает, чем это грозит, до того как что-либо сделает.
#
# Пропустить подтверждение: ./deploy/bootstrap.sh --yes

set -euo pipefail

cd "$(dirname "$0")/.."
root="$(pwd)"

confirmed=0
for argument in "$@"; do
	case "$argument" in
		--yes | -y) confirmed=1 ;;
		*)
			echo "неизвестный аргумент: $argument" >&2
			exit 2
			;;
	esac
done

cat <<'WARN'
Стенд «Резонанс» — установка целиком.

Прочитайте, прежде чем продолжить:

  • Аутентификации в приложении нет. Наружу стенд закрывает только пароль
    в Caddy — тот, который вы сейчас зададите. Кто знает пароль, видит все
    дела и может загружать документы.

  • Состояние живёт в памяти процесса. Загруженные документы, замечания и
    пересчёты теряются при перезапуске службы. Хранилища у стенда нет.

  • Материалы реальных клиентов загружать нельзя. Файл не шифруется и не
    удаляется по расписанию. Берите обезличенные документы.

  • Формальный результат не является судебным выводом или юридической
    консультацией.

Скрипт запустит службу macOS и выпустит стенд на ваш поддомен.

WARN

if [ "$confirmed" -eq 0 ]; then
	read -r -p "Продолжить? [y/N] " answer
	case "$answer" in
		y | Y | yes | да) ;;
		*)
			echo "Отменено. Ничего не изменено."
			exit 0
			;;
	esac
	echo
fi

# --- Предварительные проверки -----------------------------------------------
# Лучше остановиться здесь, чем на середине, оставив половину установки.

missing=()
command -v python3 > /dev/null || missing+=("python3")
command -v npm > /dev/null || missing+=("node/npm")
command -v caddy > /dev/null || missing+=("caddy (brew install caddy)")
command -v brew > /dev/null || missing+=("homebrew")
if [ "${#missing[@]}" -gt 0 ]; then
	printf 'Не хватает: %s\n' "${missing[*]}" >&2
	exit 1
fi

if [ "$(uname -s)" != "Darwin" ]; then
	echo "Скрипт рассчитан на macOS: launchctl и brew services здесь не работают." >&2
	exit 1
fi

# --- Что уже занято на этой машине ------------------------------------------
# Mac mini обычно не пустой. Всё, что может столкнуться с чужим проектом,
# проверяется здесь и до установки: узнать о конфликте после того, как чужой
# сайт лёг, — недопустимо.

echo "════ 0/4 · проверяю, что уже работает на машине"

listener() {
	lsof -nP -iTCP:"$1" -sTCP:LISTEN 2> /dev/null | awk 'NR==2 {print $1}'
}

# Внутренний порт стенда не фиксирован: configure.sh подберёт свободный.
# Проверять здесь нечего — проверять нужно только то, что сменить нельзя.

for port in 80 443; do
	owner="$(listener "$port")"
	if [ -n "$owner" ] && [ "$owner" != "caddy" ]; then
		cat >&2 <<CONFLICT
Порт $port занят процессом «$owner», а не Caddy.

Порты 80 и 443 сменить нельзя: адрес без порта означает 443, а Let's Encrypt
проверяет владение доменом через 80. Поэтому выход не «взять другой порт», а
подключить стенд к тому серверу, который эти порты уже держит.

Что делать:
  1. Поставьте только стенд, без выпуска наружу:
       ./deploy/install.sh && ./deploy/configure.sh
     Он поднимется на 127.0.0.1 и выбранном порту, ничего не заняв снаружи.
  2. В конфигурацию «$owner» добавьте проксирование
     revision.ai-verdict.ru на этот локальный адрес.
     Подробности и примеры для nginx и Caddy: deploy/attach-to-existing.md

Установка остановлена: снимать чужой сервер с порта я не буду.
CONFLICT
		exit 1
	fi
done

brew_etc="$(brew --prefix)/etc"
existing_caddyfile=""
if [ -f "$brew_etc/Caddyfile" ]; then
	existing_caddyfile="$brew_etc/Caddyfile"
	echo "→ найдена работающая конфигурация Caddy: $existing_caddyfile"
	echo "  стенд будет добавлен к ней вставкой, файл не перезаписывается"
else
	echo "→ своей конфигурации у Caddy нет, поставлю отдельную"
fi
echo "→ порты 80 и 443 свободны либо заняты самим Caddy"

# Права root понадобятся на последнем шаге: Caddy занимает порты 80 и 443, а на
# macOS порты ниже 1024 обычному пользователю недоступны. Спрашиваем сейчас,
# чтобы установка не встала на середине с открытым запросом пароля.
echo "Понадобятся права администратора для запуска Caddy на портах 80 и 443."
sudo -v

# --- 1. Установка -----------------------------------------------------------

echo "════ 1/4 · окружение и сборка интерфейса"
./deploy/install.sh

# --- 2. Настройка -----------------------------------------------------------

echo
echo "════ 2/4 · поддомен, почта, пароль"
./deploy/configure.sh

plist="$root/deploy/local/com.verdictcausa.stand.plist"
caddyfile="$root/deploy/local/Caddyfile"
stand_port="$(cat "$root/deploy/local/port")"

# --- 3. Служба macOS --------------------------------------------------------

echo
echo "════ 3/4 · служба macOS"
agents="$HOME/Library/LaunchAgents"
mkdir -p "$agents"
cp "$plist" "$agents/com.verdictcausa.stand.plist"

# Перезагрузка, а не загрузка: при повторном запуске служба уже стоит, и
# launchctl load на ней молча ничего не сделает.
launchctl unload "$agents/com.verdictcausa.stand.plist" 2> /dev/null || true
launchctl load "$agents/com.verdictcausa.stand.plist"
launchctl start com.verdictcausa.stand

echo "→ жду, пока стенд соберёт дела"
started=0
for _ in $(seq 1 60); do
	if curl -fsS --max-time 3 "http://127.0.0.1:$stand_port/api/desktop" > /dev/null 2>&1; then
		started=1
		break
	fi
	sleep 2
done

if [ "$started" -eq 0 ]; then
	echo "Стенд не ответил на 127.0.0.1:$stand_port за две минуты." >&2
	echo "Смотрите ~/Library/Logs/verdict-causa-stand-error.log" >&2
	exit 1
fi
echo "→ стенд отвечает на 127.0.0.1:$stand_port"

# --- 4. Выпуск наружу -------------------------------------------------------

echo
echo "════ 4/4 · Caddy и сертификат"

site="$root/deploy/local/verdict-causa.caddy"
installed_site="$brew_etc/verdict-causa.caddy"
sudo cp "$site" "$installed_site"
sudo chmod 600 "$installed_site"

if [ -n "$existing_caddyfile" ]; then
	# Чужая конфигурация не перезаписывается: в неё добавляется одна строка
	# import, и то после резервной копии. Перезапись здесь означала бы, что
	# установка стенда молча уронила остальные сайты машины.
	if sudo grep -q "verdict-causa.caddy" "$existing_caddyfile"; then
		echo "→ вставка уже подключена к $existing_caddyfile"
	else
		backup="$existing_caddyfile.before-verdict-causa.$(date +%Y%m%d%H%M%S)"
		sudo cp "$existing_caddyfile" "$backup"
		printf '\nimport %s\n' "$installed_site" | sudo tee -a "$existing_caddyfile" > /dev/null
		echo "→ вставка подключена; копия прежней конфигурации: $backup"
	fi
	config="$existing_caddyfile"
else
	sudo cp "$caddyfile" "$brew_etc/Caddyfile"
	sudo chmod 600 "$brew_etc/Caddyfile"
	config="$brew_etc/Caddyfile"
fi

# Проверка до перезапуска: сломанный файл не должен уронить чужие сайты.
if ! sudo caddy validate --config "$config" > /dev/null 2>&1; then
	echo "Итоговая конфигурация Caddy не проходит проверку — не перезапускаю." >&2
	echo "Проверьте: sudo caddy validate --config $config" >&2
	exit 1
fi
sudo brew services restart caddy > /dev/null

domain="$(awk '/^[a-z0-9.-]+ \{/ {print $1; exit}' "$site")"

echo "→ жду сертификат для $domain"
issued=0
for _ in $(seq 1 45); do
	if curl -fsS --max-time 4 -o /dev/null "https://$domain/" 2>/dev/null; then
		issued=1
		break
	fi
	# 401 значит, что TLS уже поднялся и работает basic_auth — это успех.
	if [ "$(curl -s --max-time 4 -o /dev/null -w '%{http_code}' "https://$domain/" 2>/dev/null)" = "401" ]; then
		issued=1
		break
	fi
	sleep 4
done

echo
if [ "$issued" -eq 1 ]; then
	cat <<DONE
Готово. Стенд открыт: https://$domain

Войти: имя пользователя и пароль, заданные на шаге 2.

Служба:   launchctl stop|start com.verdictcausa.stand
Логи:     ~/Library/Logs/verdict-causa-stand.log
Caddy:    sudo brew services restart caddy
Конфиг:   $config
DONE
else
	cat <<PENDING
Стенд работает локально, но https://$domain пока не отвечает.

Почти всегда это одно из двух:

  • A-запись $domain не указывает на внешний адрес этого Mac mini
    (проверьте: dig +short $domain);
  • порты 80 и 443 не проброшены на него в роутере — без порта 80
    Let's Encrypt не подтвердит владение доменом.

Caddy продолжит попытки сам. Смотрите: brew services info caddy
и ~/Library/Logs/verdict-causa-caddy.log
PENDING
fi
