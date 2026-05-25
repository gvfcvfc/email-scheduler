premium_dashboard
export_csv
priority_support
websocket_notifications

GET /track/open/{token}.gif
GET /track/click/{token}
POST /track/event

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
notification
job


git rm --cached docs/private.md
git commit --amend --no-edit
git push --force-with-lease
git rebase -i HEAD~N