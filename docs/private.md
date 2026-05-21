POST /auth/forgot-password
POST /auth/reset-password
POST /auth/resend-verification
GET /auth/verify-email

python-multipart
@router.post("/upload")
@router.post("/upload/multiple")
@router.get("/files/{id}")
@router.get("/files/{id}/download")
@router.delete("/files/{id}")

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


verify_email_page = st.Page(
    "pages/verify_email.py",
    title="Verify Email",
    url_path="verify-email",
)

reset_password_page = st.Page(
    "pages/reset_password.py",
    title="Reset Password",
    url_path="reset-password",
)

pg = st.navigation([
    verify_email_page,
    reset_password_page,
])

pg.run()
