#!/usr/bin/env bash
# Установка стенда «Резонанс» на Mac mini.
#
# Скрипт готовит окружение и собирает интерфейс. Он намеренно ничего не
# запускает как службу и не открывает портов: установка, которая молча выпускает
# приложение наружу, недопустима — службу и Caddy включает человек, прочитав
# deploy/README.md.

set -euo pipefail

cd "$(dirname "$0")/.."
root="$(pwd)"
echo "Каталог проекта: $root"

python="${PYTHON:-python3}"
"$python" --version

if [ ! -d .venv ]; then
	echo "→ создаю виртуальное окружение"
	"$python" -m venv .venv
fi
./.venv/bin/python -m pip install --quiet --upgrade pip
echo "→ ставлю пакет"
# Дополнение documents ставится вместе с пакетом: без него стенд не прочитает
# PDF и честно об этом скажет, но материалы клиентов чаще всего приходят
# именно в PDF, и отказ на первом же файле выглядел бы поломкой.
./.venv/bin/python -m pip install --quiet -e '.[documents]'

echo "→ собираю данные разбора"
./.venv/bin/python -m causa.ui.snapshot --json web/data/desktop.json

echo "→ собираю интерфейс"
if ! command -v npm > /dev/null; then
	echo "npm не найден: поставьте Node.js 20+ и повторите" >&2
	exit 1
fi
(cd web && npm install --silent && npm run build)

if [ ! -f web/out/index.html ]; then
	echo "сборка интерфейса не создала web/out/index.html" >&2
	exit 1
fi

echo "→ проверяю, что стенд поднимается"
./.venv/bin/python - <<'PY'
from causa.ui.server import DesktopService, static_root

service = DesktopService()
cases = len(service.state.case_views)
print(f"   дел собрано: {cases}")
print(f"   интерфейс отдаётся из: {static_root()}")
assert cases > 0, "стенд собрался без дел"
PY

cat <<'NEXT'

Готово. Дальше:

  ./deploy/configure.sh

Он спросит поддомен, почту для Let's Encrypt и пароль и соберёт рабочие файлы
в deploy/local/. Запускать службу и Caddy — по deploy/README.md, вручную.

Стенд слушает только 127.0.0.1, порт подберёт configure.sh.
Аутентификации в приложении нет —
без basic_auth в Caddy наружу его выпускать нельзя.
NEXT
