POST /auth/forgot-password
POST /auth/reset-password
POST /auth/resend-verification
GET /auth/verify-email

Audit logging
GET /admin/audit-logs
GET /admin/jobs
GET /admin/jobs/{id}

Application logging
Grafana + Loki + Alloy

Admin routes
GET /admin/jobs
GET /admin/logs
GET /admin/system-health

docker compose services
nginx
prometheus
pgadmin
minio

utils
pagination
retry
permissions
startup_checks
logger
event_bus
health_checks
id_generator

models
audit_log
password_reset
EmailVerification
notification
job


git rm --cached docs/private.md
git commit --amend --no-edit
git push --force-with-lease
git rebase -i HEAD~N

