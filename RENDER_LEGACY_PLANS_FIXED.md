# Render Legacy Plans - ИСПРАВЛЕНО ✅

## Проблема
Render Blueprint показывал ошибки:
- `databases[0].plan Legacy Postgres plans, including 'standard', are no longer supported`
- `databases[1].plan Legacy Postgres plans, including 'starter', are no longer supported`

## Решение
✅ **Все legacy планы заменены на современные:**

### Базы данных:
```yaml
databases:
  - name: ai-writer-db
    postgresMajorVersion: 15
    databaseName: ai_writer_db
    user: ai_writer_user
    region: oregon
    plan: basic-4gb  # ✅ Заменено с 'standard'
    ipAllowList: []
  - name: ai-writer-db-staging
    postgresMajorVersion: 15
    databaseName: ai_writer_db_staging
    user: ai_writer_user_staging
    region: oregon
    plan: basic-1gb  # ✅ Заменено с 'starter'
    ipAllowList: []
```

### Все сервисы:
- **Production**: `plan: basic-4gb` (вместо `standard`)
- **Staging**: `plan: basic-1gb` (вместо `starter`)

## Проверка
```bash
# В файле НЕТ legacy планов:
type render.yaml | findstr /C:"plan:" | findstr /C:"standard" /C:"starter"
# Результат: пустой (нет совпадений) ✅
```

## Статус
🟢 **ФАЙЛ ГОТОВ К ДЕПЛОЮ**

Если Render все еще показывает ошибки с legacy планами:
1. **Обновите страницу** Render Dashboard
2. **Создайте новый Blueprint** 
3. **Убедитесь**, что используется ветка `main`
4. **Проверьте**, что файл синхронизирован с GitHub

## Коммиты
- `28b8544` - Add postgresMajorVersion and ipAllowList to database configuration
- `891996a` - Force update render.yaml to clear cache

---
**Дата**: $(Get-Date)
**Статус**: ✅ ИСПРАВЛЕНО
