# SDA Church Manager — Implementation Plan

## Overview
Web-based church management system for Seventh-day Adventist churches in Kenya.
Track members, tithes, Sabbath School, baptisms, officers, events, and generate reports.

## Tech Stack
- **Backend:** Python Flask + SQLite (zero external DB dependencies)
- **Frontend:** Bootstrap 5 (responsive — works on mobile/tablet in Kenyan churches)
- **Infrastructure:** Docker Compose → Dokploy on `sda-church.spidmax.win`

## Modules
1. **Dashboard** — Key metrics, charts, recent activity
2. **Members** — CRUD with SDA fields (baptism, membership status, tribe, district, region)
3. **Tithes & Offerings** — Weekly recording, member statements, monthly/annual reports
4. **Sabbath School** — Class divisions, lesson tracking, attendance
5. **Baptism** — Records, certificates, baptismal candidates
6. **Church Officers** — Elders, deacons, departmental leaders, term management
7. **Events** — Church calendar, evangelistic campaigns, youth programs
8. **Reports** — Quarterly statistical returns, financial summaries, membership growth

## File Structure
```
sda-church-manager/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── db.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── members.py
│   │   ├── finances.py
│   │   ├── sabbath_school.py
│   │   ├── baptisms.py
│   │   ├── officers.py
│   │   ├── events.py
│   │   └── reports.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── members/
│   │   ├── finances/
│   │   ├── sabbath_school/
│   │   ├── baptisms/
│   │   ├── officers/
│   │   ├── events/
│   │   └── reports/
│   └── static/
│       └── css/
│           └── style.css
└── data/           (persisted via Docker volume)
    └── church.db
```

## Deployment
- GitHub repo: `jawg-zz/sda-church-manager`
- App domain: `sda-church.spidmax.win`
- Port: 5000 (Flask default)
