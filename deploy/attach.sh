#!/usr/bin/env bash
# Подключение стенда к веб-серверу, который уже держит порты 80 и 443.
#
#   ./deploy/attach.sh
#
# Скрипт ничего не меняет. Он выясняет, кто держит публичные порты, проверяет,
# что стенд отвечает локально, и печатает готовый кусок конфигурации под тот
# сервер, который нашёлся. Применять его — решение человека.
#
# Почему не автоматически: конфигурацию боевого веб-сервера правит тот, кто
# знает, что там ещё обслуживается. Ошибка здесь роняет чужие сайты.

cd "$(dirname "$0")/.." || exit 1
root="$(pwd)"

domain="${CAUSA_DOMAIN:-revision.ai-verdict.ru}"
port="$(cat "$root/deploy/local/port" 2> /dev/null || true)"

echo "══════ стенд ══════"
if [ -z "$port" ]; then
	echo "Порт не найден: сначала выполните ./deploy/install.sh && ./deploy/configure.sh"
	exit 1
fi
echo "порт: $port"
if curl -fsS --max-time 3 "http://127.0.0.1:$port/api/desktop" > /dev/null 2>&1; then
	echo "состояние: отвечает"
else
	echo "состояние: НЕ отвечает — запустите стенд, прежде чем подключать поддомен"
fi

echo
echo "══════ кто держит 80 и 443 ══════"
owners=""
for p in 80 443; do
	line="$(sudo lsof -nP -iTCP:"$p" -sTCP:LISTEN 2> /dev/null | awk 'NR>1')"
	if [ -z "$line" ]; then
		echo "$p: свободен"
	else
		echo "$p:"
		printf '%s\n' "$line" | sed 's/^/    /'
		owners="$owners $(printf '%s\n' "$line" | awk '{print $1}' | sort -u | tr '\n' ' ')"
	fi
done

echo
echo "══════ контейнеры ══════"
containers="$(docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}' 2> /dev/null || true)"
if [ -z "$containers" ]; then
	# Docker может быть запущен под другим пользователем: у Colima сокет лежит
	# в его домашнем каталоге, и наш `docker` его не видит.
	for candidate in $(ps -axo user= -o command= | awk '/colima|dockerd/ && !/awk/ {print $1}' | sort -u); do
		echo "Docker работает под пользователем «$candidate», а не под вами."
		echo "Посмотрите так: sudo -u $candidate docker ps"
	done
	[ -z "$containers" ] && echo "(через ваш docker контейнеров не видно)"
else
	printf '%s\n' "$containers"
fi

echo
echo "══════ что делать дальше ══════"

# Внутри контейнера 127.0.0.1 — это сам контейнер. До хоста из Colima и Docker
# Desktop ведёт host.docker.internal; это самая частая ошибка в такой схеме.
host_from_container="host.docker.internal"

case "$owners" in
	*caddy*)
		cat <<CADDY
Порты держит Caddy. Подключите готовую вставку:

    BREW_ETC="\$(brew --prefix)/etc"
    sudo cp deploy/local/verdict-causa.caddy "\$BREW_ETC/verdict-causa.caddy"
    sudo cp "\$BREW_ETC/Caddyfile" "\$BREW_ETC/Caddyfile.backup.\$(date +%Y%m%d%H%M%S)"
    echo "import \$BREW_ETC/verdict-causa.caddy" | sudo tee -a "\$BREW_ETC/Caddyfile"
    sudo caddy validate --config "\$BREW_ETC/Caddyfile"
    sudo brew services restart caddy
CADDY
		;;
	*nginx*)
		cat <<NGINX
Порты держит nginx. Добавьте отдельный файл, существующие сайты не трогайте.
Готовый блок лежит в deploy/local/nginx-$domain.conf — перенесите его в каталог
конфигураций nginx, создайте пароль и перезагрузите:

    htpasswd -c /opt/homebrew/etc/nginx/.htpasswd-revision operator
    sudo nginx -t && sudo nginx -s reload

Сертификат выпускайте тем же способом, что и для остальных ваших сайтов.
NGINX
		mkdir -p "$root/deploy/local"
		cat > "$root/deploy/local/nginx-$domain.conf" <<NGINXCONF
server {
    listen 80;
    server_name $domain;
    location /.well-known/acme-challenge/ { root /usr/local/var/www; }
    location / { return 301 https://\$host\$request_uri; }
}

server {
    listen 443 ssl;
    server_name $domain;

    ssl_certificate     /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;

    # Аутентификации в приложении нет. Без этих двух строк стенд открыт всем.
    auth_basic           "Rezonans";
    auth_basic_user_file /opt/homebrew/etc/nginx/.htpasswd-revision;

    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    location / {
        proxy_pass http://127.0.0.1:$port;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
NGINXCONF
		echo
		echo "Файл записан: deploy/local/nginx-$domain.conf"
		;;
	*ssh* | *com.docker* | *docker*)
		cat <<DOCKER
Порты держит проброс Docker: наружу их отдаёт контейнер, а не процесс на хосте.

Значит, поддомен нужно завести в том контейнере, который работает обратным
прокси (nginx, Traefik, Caddy). Цель проксирования — **не** 127.0.0.1: внутри
контейнера это он сам. Хост доступен как:

    $host_from_container:$port

Если в списке контейнеров выше виден Traefik — добавьте метку маршрута;
если nginx — добавьте файл конфигурации в его том; если Caddy — блок сайта.
Пришлите вывод раздела «контейнеры», и я соберу конфигурацию под него.

Никакой контейнер сам не останавливайте: там работающий сервис.
DOCKER
		;;
	*)
		cat <<FREE
Порты 80 и 443 свободны — подключать стенд к чужому серверу не нужно.
Запускайте обычную установку: ./deploy/bootstrap.sh
FREE
		;;
esac

echo
echo "══════ пришлите этот вывод целиком ══════"
