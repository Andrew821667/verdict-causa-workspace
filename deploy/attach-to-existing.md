# Если порты 80 и 443 уже заняты другим сервером

На машине с несколькими проектами это обычное дело. Установка стенда в такой
ситуации останавливается сама — и правильно делает.

## Почему нельзя «просто взять другие порты»

Внутренний порт стенда действительно любой: `configure.sh` подбирает свободный
сам, и наружу тот порт не открывается ни при каком выборе.

А вот 80 и 443 сменить нельзя:

- `https://revision.ai-verdict.ru/` без порта в адресе означает **443** — это
  часть протокола, а не настройка;
- Let's Encrypt подтверждает владение доменом через **80** (проверка HTTP-01)
  либо через **443** (TLS-ALPN-01). Другого бесплатного пути нет.

На нестандартном порту адрес превратится в `https://revision.ai-verdict.ru:8443/`,
а сертификат придётся получать проверкой DNS-01: это токен API вашего
регистратора, положенный на диск, и пересборка Caddy с плагином для этого
регистратора. Ради тестового стенда — плохой размен.

**Правильный путь: стенд не занимает публичные порты вовсе.** Он поднимается на
`127.0.0.1` и своём локальном порту, а сервер, который уже держит 80 и 443,
проксирует на него один поддомен. Сертификат тоже выпускает он — тем механизмом,
которым уже пользуется для остальных сайтов.

## Шаг 1. Поставьте стенд без выпуска наружу

```bash
cd ~/verdict-causa
./deploy/install.sh
./deploy/configure.sh
```

`configure.sh` спросит поддомен, почту и пароль, подберёт свободный порт и
напечатает его. Порт также лежит в `deploy/local/port`:

```bash
PORT="$(cat deploy/local/port)"; echo "$PORT"
```

Запустите службу:

```bash
cp deploy/local/com.verdictcausa.stand.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.verdictcausa.stand.plist
launchctl start com.verdictcausa.stand
curl -s "http://127.0.0.1:$PORT/api/desktop" | head -c 200; echo
```

Дальше `deploy/bootstrap.sh` **не запускайте**: он предназначен для случая, когда
публичные порты свободны.

## Шаг 2. Подключите поддомен к существующему серверу

### Если 80 и 443 держит Caddy

Проще всего — уже собранная вставка. Подключите её к работающей конфигурации:

```bash
BREW_ETC="$(brew --prefix)/etc"
sudo cp deploy/local/verdict-causa.caddy "$BREW_ETC/verdict-causa.caddy"
sudo chmod 600 "$BREW_ETC/verdict-causa.caddy"

# копия перед правкой
sudo cp "$BREW_ETC/Caddyfile" "$BREW_ETC/Caddyfile.backup.$(date +%Y%m%d%H%M%S)"
echo "import $BREW_ETC/verdict-causa.caddy" | sudo tee -a "$BREW_ETC/Caddyfile"

sudo caddy validate --config "$BREW_ETC/Caddyfile"   # обязательно до перезапуска
sudo brew services restart caddy
```

Вставка содержит `basic_auth` и заголовки — менять в ней ничего не нужно.

### Если 80 и 443 держит nginx

Добавьте отдельный файл конфигурации, а не правьте существующие сайты.
Подставьте порт из шага 1 вместо `ПОРТ`:

```nginx
# /opt/homebrew/etc/nginx/servers/revision.ai-verdict.ru.conf

server {
    listen 80;
    server_name revision.ai-verdict.ru;
    # Оставьте путь для проверки Let's Encrypt, если используете certbot webroot.
    location /.well-known/acme-challenge/ { root /usr/local/var/www; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    server_name revision.ai-verdict.ru;

    ssl_certificate     /etc/letsencrypt/live/revision.ai-verdict.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/revision.ai-verdict.ru/privkey.pem;

    # Аутентификации в приложении нет. Без этих двух строк стенд открыт всем.
    auth_basic           "Rezonans";
    auth_basic_user_file /opt/homebrew/etc/nginx/.htpasswd-revision;

    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    location / {
        proxy_pass http://127.0.0.1:ПОРТ;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Сборка стола и пересчёт дела занимают десятки секунд: короткий таймаут
        # оборвёт ровно то, ради чего стенд ставится.
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

Пароль для `auth_basic`:

```bash
htpasswd -c /opt/homebrew/etc/nginx/.htpasswd-revision operator
```

Сертификат — тем же способом, каким выпускаются остальные ваши сайты
(`certbot --nginx -d revision.ai-verdict.ru` либо ваш обычный порядок).

Проверка и перезагрузка:

```bash
sudo nginx -t && sudo nginx -s reload
```

### Если 80 и 443 держит Docker

Смотрите, какой контейнер слушает порт: `docker ps`. Если это Traefik,
nginx-proxy или Caddy в контейнере — добавьте маршрут его средствами, указав
цель `host.docker.internal:ПОРТ` (из контейнера `127.0.0.1` — это сам контейнер,
а не хост; это самая частая ошибка в такой схеме).

## Шаг 3. Проверьте

```bash
curl -s -o /dev/null -w "без пароля: %{http_code}\n" https://revision.ai-verdict.ru/
curl -s -o /dev/null -w "с паролем:  %{http_code}\n" -u operator:ПАРОЛЬ https://revision.ai-verdict.ru/
```

- **без пароля — `401`**: так и должно быть, HTTPS работает и стенд закрыт;
- **с паролем — `200`**.

Если без пароля приходит `200` — аутентификация не подключилась. Выключите
поддомен и разберитесь: в приложении своей аутентификации нет, и открытый адрес
означает, что дела видит кто угодно.

## Обновление в будущем

```bash
cd ~/verdict-causa && git pull
./deploy/install.sh
launchctl stop com.verdictcausa.stand && launchctl start com.verdictcausa.stand
```

Внешний сервер трогать не нужно: порт и поддомен не меняются. `configure.sh`
повторяйте, только если меняете пароль или поддомен — тогда и порт может стать
другим, проверьте `deploy/local/port` и поправьте `proxy_pass`.
