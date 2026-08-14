# Задание: поднять стенд на revision.ai-verdict.ru

Работай на ресурсах подписки. **Не используй платные API языковых моделей и их
ключи** — ни свои, ни из окружения, ни из проектов на машине. Если кажется, что
без них никак, — остановись и напиши владельцу.

## Что сделать

```bash
cd ~
git clone https://github.com/andrew821667/verdict-causa-workspace.git verdict-causa 2>/dev/null || (cd verdict-causa && git pull)
cd ~/verdict-causa

export CAUSA_DOMAIN="revision.ai-verdict.ru"
export CAUSA_EMAIL="ПОЧТА_ВЛАДЕЛЬЦА"
export CAUSA_OPERATOR="operator"
export CAUSA_PASSWORD="$(python3 -c "import secrets,string; a=string.ascii_letters+string.digits; print(''.join(secrets.choice(a) for _ in range(24)))")"
echo "ПАРОЛЬ ДЛЯ ВХОДА: $CAUSA_PASSWORD"

./deploy/bootstrap.sh --yes
```

Займёт 10–20 минут. На шаге 1/4 скрипт молчит несколько минут — это нормально,
не прерывай.

## Что проверить

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://revision.ai-verdict.ru/
```

**Должно быть `401`.** Это успех: сайт работает и закрыт паролем.

## Что прислать владельцу

- пароль из строки `ПАРОЛЬ ДЛЯ ВХОДА`;
- код из проверки выше;
- если что-то упало — **последние 30 строк вывода целиком**, без пересказа.

## Правила

- **Ничего не обновляй** (`brew upgrade` запрещён): на машине другие проекты.
- **Не выключай чужие сервисы** и не трогай чужие конфигурации.
- Если скрипт сам остановился и что-то написал — **скопируй этот текст владельцу
  и ничего не предпринимай**. Он остановился намеренно.
- Не меняй код проекта, чтобы обойти ошибку.

Подробности, если понадобятся: `deploy/AGENT-TASK.md` в том же репозитории.
