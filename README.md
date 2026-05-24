# Email Scheduler

A scalable email scheduling service built with **FastAPI**, **Celery**, **Redis**, **PostgreSQL** **stripe**, and **Docker**.
The system allows users to connect their email account, schedule messages for future delivery, and process email sending asynchronously through background workers.

The project demonstrates a modern backend architecture used in production systems that require job queues, distributed workers, authentication, and containerized infrastructure.

---

# Features

* **User Authentication**

  * JWT-based authentication
  * secure password hashing

* **OAuth Integration**

  * users can connect their GitHub account using OAuth
  * emails are sent from the user’s own account

* **Email Scheduling**

  * schedule emails for future delivery
  * edit or cancel scheduled messages

* **Background Processing**

  * Celery workers process email jobs asynchronously
  * Redis acts as the message broker for task queues

* **Caching Layer**

  * Redis used for caching and task coordination

* **Containerized Infrastructure**

  * Docker and Docker Compose run all services together

---

# Technology Stack

**Backend** * FastAPI
            * Python
**Task Processing*** Celery
                    * Redis
**Authentication**  * JWT
                    *OAuth (GitHub)
**Database**    * PostgreSQL
                * SQLAlchemy
**Infrastructure**  * Docker
                    * Docker Compose
---

# Running the Project

Start all services:

```
docker compose up --build
```

This starts:

* FastAPI API server
* Celery worker
* Redis
* PostgreSQL

---

# Example Capabilities

* register and authenticate users
* connect a GitHub account through OAuth
* schedule emails to be sent at a specific time
* process email delivery through background workers
* manage scheduled emails through API endpoints

---

# Architecture Overview

The API receives scheduling requests and stores them in the database.
Celery workers monitor the task queue and process email delivery jobs asynchronously using Redis as the message broker.

This architecture allows the system to scale horizontally by adding additional workers as the email workload grows.

---

# Project Purpose

This project demonstrates the implementation of a distributed backend system capable of handling asynchronous workloads, authentication, and external service integrations using modern Python infrastructure.
