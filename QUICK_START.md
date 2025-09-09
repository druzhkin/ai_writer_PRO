# 🚀 Быстрый старт - AI Writer PRO на Render

## Шаг 1: Подготовка (5 минут)

✅ **Код уже загружен на GitHub**: https://github.com/druzhkin/ai_writer_PRO

## Шаг 2: Создание Blueprint на Render (2 минуты)

1. Откройте [Render Dashboard](https://dashboard.render.com)
2. Нажмите **"New +"** → **"Blueprint"**
3. Подключите репозиторий: `druzhkin/ai_writer_PRO`
4. Выберите файл: `render.yaml`
5. Нажмите **"Apply"**

## Шаг 3: Настройка переменных окружения (10 минут)

### Обязательные переменные для production-secrets:

```bash
# OpenAI (обязательно)
OPENAI_API_KEY=sk-your_openai_api_key_here

# OAuth (обязательно для авторизации)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id

# AWS S3 (обязательно для файлов)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_s3_bucket_name

# Email (обязательно для уведомлений)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Опциональные переменные:

```bash
# Мониторинг
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Webhook
WEBHOOK_SECRET=your_webhook_secret

# Vapi (если используется)
VAPI_PRIVATE_KEY=your_vapi_private_key
VAPI_PUBLIC_KEY=your_vapi_public_key
```

## Шаг 4: Ожидание деплоя (5-10 минут)

Render автоматически создаст:
- ✅ 2 PostgreSQL базы данных
- ✅ 2 Redis сервиса
- ✅ 4 Web сервиса (backend + frontend для prod и staging)
- ✅ 2 Celery worker сервиса

## Шаг 5: Проверка работы (2 минуты)

После завершения деплоя проверьте:

1. **Backend Health**: `https://your-backend-url.onrender.com/health`
2. **Frontend**: `https://your-frontend-url.onrender.com`
3. **Регистрация**: создайте тестовый аккаунт
4. **Генерация контента**: попробуйте создать статью

## 🎯 Готово!

Ваше приложение AI Writer PRO теперь работает на Render!

### Полезные ссылки:
- 📊 **Render Dashboard**: https://dashboard.render.com
- 📚 **Полная документация**: `RENDER_DEPLOYMENT_GUIDE.md`
- 🔧 **Переменные окружения**: `RENDER_ENV_VARS.md`

### Стоимость:
- **Production**: ~$42/месяц
- **Staging**: ~$28/месяц

### Поддержка:
При проблемах проверьте логи в Render Dashboard или обратитесь к полной документации.
