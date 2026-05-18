## Schedule Email Flow
1. User sends request to /email
2. Route validates input
3. Email stored in DB
4. Task sent to Celery
5. Worker processes task
6. Email sent via SMTP