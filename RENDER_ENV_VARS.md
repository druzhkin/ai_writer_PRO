# Переменные окружения для Render

## Production Environment Variables

Скопируйте эти переменные в Render Dashboard для настройки production-secrets:

```bash
# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_S3_BUCKET=your_s3_bucket_name_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here

# Monitoring
SENTRY_DSN=https://your_sentry_dsn_here@sentry.io/project_id
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Webhook
WEBHOOK_SECRET=your_webhook_secret_here

# Vapi Configuration (если используется)
VAPI_PRIVATE_KEY=your_vapi_private_key_here
VAPI_PUBLIC_KEY=your_vapi_public_key_here
```

## Staging Environment Variables

Для staging-secrets используйте тестовые значения:

```bash
# OAuth Configuration (Staging)
GOOGLE_CLIENT_ID=your_staging_google_client_id_here
GOOGLE_CLIENT_SECRET=your_staging_google_client_secret_here
GITHUB_CLIENT_ID=your_staging_github_client_id_here
GITHUB_CLIENT_SECRET=your_staging_github_client_secret_here
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_staging_google_client_id_here
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_staging_github_client_id_here

# OpenAI Configuration (Staging)
OPENAI_API_KEY=sk-your_staging_openai_api_key_here

# AWS S3 Configuration (Staging)
AWS_ACCESS_KEY_ID=your_staging_aws_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_staging_aws_secret_access_key_here
AWS_S3_BUCKET=your_staging_s3_bucket_name_here

# Email Configuration (Staging)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_staging_email@gmail.com
SMTP_PASSWORD=your_staging_app_password_here

# Monitoring (Staging)
SENTRY_DSN=https://your_staging_sentry_dsn_here@sentry.io/project_id
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Webhook (Staging)
WEBHOOK_SECRET=your_staging_webhook_secret_here

# Vapi Configuration (Staging)
VAPI_PRIVATE_KEY=your_staging_vapi_private_key_here
VAPI_PUBLIC_KEY=your_staging_vapi_public_key_here
```

## Автоматически генерируемые переменные

Эти переменные будут автоматически созданы Render:

```bash
# JWT и Session Secrets (генерируются автоматически)
JWT_SECRET_KEY=auto_generated
SESSION_SECRET_KEY=auto_generated

# Database URLs (автоматически из подключенных баз данных)
DATABASE_URL=auto_generated_from_database
REDIS_URL=auto_generated_from_redis

# Service URLs (автоматически генерируются)
BACKEND_BASE_URL=auto_generated
FRONTEND_BASE_URL=auto_generated
NEXT_PUBLIC_APP_URL=auto_generated
NEXT_PUBLIC_API_URL=auto_generated
FRONTEND_URL=auto_generated
FRONTEND_CORS_ORIGINS=auto_generated
CORS_ORIGINS=auto_generated
OAUTH_REDIRECT_URI=auto_generated
WEBSOCKET_URL=auto_generated

# Celery Configuration (автоматически из Redis)
CELERY_BROKER_URL=auto_generated_from_redis
CELERY_RESULT_BACKEND=auto_generated_from_redis
```

## Инструкции по настройке

### 1. Google OAuth
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
2. Создайте новый проект или выберите существующий
3. Включите Google+ API
4. Создайте OAuth 2.0 credentials
5. Добавьте authorized redirect URIs:
   - `https://your-backend-url.onrender.com/api/v1/oauth/callback`
   - `https://your-staging-backend-url.onrender.com/api/v1/oauth/callback`

### 2. GitHub OAuth
1. Перейдите в [GitHub Developer Settings](https://github.com/settings/developers)
2. Создайте новое OAuth App
3. Установите Authorization callback URL:
   - `https://your-backend-url.onrender.com/api/v1/oauth/callback`
   - `https://your-staging-backend-url.onrender.com/api/v1/oauth/callback`

### 3. OpenAI API
1. Перейдите в [OpenAI Platform](https://platform.openai.com)
2. Создайте API ключ в разделе API Keys
3. Убедитесь, что у вас есть кредиты на счету

### 4. AWS S3
1. Создайте S3 bucket в [AWS Console](https://console.aws.amazon.com)
2. Создайте IAM пользователя с правами на S3
3. Сгенерируйте Access Key и Secret Key

### 5. Email (Gmail)
1. Включите 2FA в Google аккаунте
2. Создайте App Password в настройках безопасности
3. Используйте App Password вместо обычного пароля

### 6. Sentry
1. Создайте проект в [Sentry](https://sentry.io)
2. Скопируйте DSN из настроек проекта

### 7. Google Analytics
1. Создайте свойство в [Google Analytics](https://analytics.google.com)
2. Скопируйте Measurement ID (формат: G-XXXXXXXXXX)

## Проверка после настройки

После настройки всех переменных:

1. Проверьте, что все сервисы запустились успешно
2. Откройте health check endpoints:
   - Backend: `https://your-backend-url.onrender.com/health`
   - Frontend: `https://your-frontend-url.onrender.com`
3. Протестируйте регистрацию и авторизацию
4. Проверьте генерацию контента
5. Убедитесь, что файлы загружаются в S3
6. Проверьте работу email уведомлений
