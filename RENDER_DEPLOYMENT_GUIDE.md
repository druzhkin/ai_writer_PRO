# AI Writer PRO - Руководство по деплою на Render

## Обзор проекта

AI Writer PRO - это полнофункциональное веб-приложение для генерации контента с использованием ИИ, состоящее из:
- **Backend**: FastAPI с PostgreSQL и Redis
- **Frontend**: Next.js с TypeScript
- **Background Tasks**: Celery для асинхронных задач
- **Monitoring**: Prometheus и Grafana

## Настройка деплоя на Render

### 1. Подготовка репозитория

✅ Код уже загружен на GitHub: https://github.com/druzhkin/ai_writer_PRO

### 2. Создание Blueprint на Render

1. Войдите в [Render Dashboard](https://dashboard.render.com)
2. Нажмите "New +" → "Blueprint"
3. Подключите репозиторий `druzhkin/ai_writer_PRO`
4. Выберите файл `render.yaml` из корня репозитория
5. Нажмите "Apply"

### 3. Настройка переменных окружения

После создания Blueprint, настройте следующие переменные в Render Dashboard:

#### Production Secrets (production-secrets)
```
# JWT и Session Secrets (генерируются автоматически)
JWT_SECRET_KEY=generateValue: true
SESSION_SECRET_KEY=generateValue: true

# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_s3_bucket_name

# Email Configuration
SMTP_HOST=your_smtp_host
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password

# Monitoring
SENTRY_DSN=your_sentry_dsn
GOOGLE_ANALYTICS_ID=your_ga_id

# Webhook
WEBHOOK_SECRET=your_webhook_secret

# Production URLs (будут автоматически установлены Render)
BACKEND_BASE_URL=auto_generated
FRONTEND_BASE_URL=auto_generated
NEXT_PUBLIC_APP_URL=auto_generated
NEXT_PUBLIC_API_URL=auto_generated
FRONTEND_URL=auto_generated
FRONTEND_CORS_ORIGINS=auto_generated
CORS_ORIGINS=auto_generated
OAUTH_REDIRECT_URI=auto_generated
WEBSOCKET_URL=auto_generated
```

#### Staging Secrets (staging-secrets)
```
# Аналогично production, но с staging значениями
# Используйте тестовые API ключи и staging URLs
```

### 4. Сервисы, которые будут созданы

Blueprint создаст следующие сервисы:

#### Базы данных
- `ai-writer-db` (PostgreSQL, Standard план)
- `ai-writer-db-staging` (PostgreSQL, Starter план)

#### Redis
- `ai-writer-redis` (Redis, Starter план)
- `ai-writer-redis-staging` (Redis, Starter план)

#### Web сервисы
- `ai-writer-backend` (FastAPI, Standard план)
- `ai-writer-frontend` (Next.js, Standard план)
- `ai-writer-backend-staging` (FastAPI, Starter план)
- `ai-writer-frontend-staging` (Next.js, Starter план)

#### Worker сервисы
- `ai-writer-celery-worker` (Celery Worker, Standard план)
- `ai-writer-celery-beat` (Celery Beat, Standard план)

### 5. Особенности конфигурации

#### Backend (FastAPI)
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`
- **Health Check**: `/health`
- **Dockerfile**: `./backend/Dockerfile`
- **Auto Deploy**: из ветки `main`

#### Frontend (Next.js)
- **Start Command**: `node server.js`
- **Health Check**: `/`
- **Dockerfile**: `./frontend/Dockerfile`
- **Standalone Output**: включен в `next.config.js`
- **Build Args**: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_URL`
- **Auto Deploy**: из ветки `main`

#### Celery Workers
- **Worker**: `celery -A app.tasks worker --loglevel=info --concurrency=4`
- **Beat**: `celery -A app.tasks beat --loglevel=info`

### 6. Мониторинг и логи

- **Health Checks**: настроены для всех сервисов
- **Logs**: доступны в Render Dashboard
- **Metrics**: Prometheus метрики включены
- **Error Tracking**: Sentry интеграция

### 7. Безопасность

- **HTTPS**: автоматически включен для всех сервисов
- **CORS**: настроен для production доменов
- **Session Security**: `SESSION_SECURE=True` в production
- **JWT**: настроен с безопасными настройками

### 8. Масштабирование

- **Backend**: 1-3 инстанса, CPU 70%, Memory 80%
- **Frontend**: 1-2 инстанса, CPU 70%, Memory 80%
- **Workers**: фиксированное количество (4 concurrency)

### 9. Стоимость (примерная)

#### Production
- PostgreSQL Standard: ~$7/месяц
- Redis Starter: ~$7/месяц
- Backend Standard: ~$7/месяц
- Frontend Standard: ~$7/месяц
- Celery Worker Standard: ~$7/месяц
- Celery Beat Standard: ~$7/месяц
- **Итого**: ~$42/месяц

#### Staging
- PostgreSQL Starter: ~$7/месяц
- Redis Starter: ~$7/месяц
- Backend Starter: ~$7/месяц
- Frontend Starter: ~$7/месяц
- **Итого**: ~$28/месяц

### 10. После деплоя

1. Проверьте health checks всех сервисов
2. Настройте домены (если нужно)
3. Проверьте работу OAuth провайдеров
4. Настройте мониторинг в Sentry
5. Протестируйте генерацию контента

### 11. Полезные ссылки

- [Render Dashboard](https://dashboard.render.com)
- [Render Blueprint Documentation](https://render.com/docs/blueprint-spec)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment Guide](https://nextjs.org/docs/deployment)

## Поддержка

При возникновении проблем:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения настроены
3. Проверьте health checks сервисов
4. Обратитесь к документации Render
