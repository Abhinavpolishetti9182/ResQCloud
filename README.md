# 🛡️ ResQCloud — Automated Backup, Disaster Recovery & Incident Response Platform

> **Detect fast. Recover faster. Trust by design.**

<img width="1001" height="1570" alt="ResQCloud_ Cloud Resilience README Infographic-1" src="https://github.com/user-attachments/assets/dd3dad35-af38-45b6-bf42-d03d303b3297" />


---

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Complete System Flow](#complete-system-flow)
4. [Core Features](#core-features)
5. [Technology Stack](#technology-stack)
6. [AWS Services Used](#aws-services-used)
7. [Docker Deployment](#docker-deployment)
8. [Terraform Infrastructure](#terraform-infrastructure)
9. [Project Structure](#project-structure)
10. [Prerequisites](#prerequisites)
11. [Setup & Installation](#setup--installation)
12. [Testing & Validation](#testing--validation)
13. [Security](#security)
14. [Disaster Recovery Scenario](#disaster-recovery-scenario)
15. [Project Status](#project-status)
16. [Author](#author)

---

# 📌 Project Overview

ResQCloud is a cloud resilience platform built to bring **infrastructure monitoring, backup management, backup integrity verification, incident management, disaster recovery, and operational runbooks** into one web application.

The project is designed around a simple operational question:

> **When something fails, can we detect it, find a trusted backup, recover the resource, and verify that recovery worked?**

### Key Features

- 📊 Infrastructure monitoring
- 💾 Amazon S3 backup management
- 🔐 SHA-256 backup integrity verification
- 🚨 Incident management
- ♻️ Disaster recovery
- 📖 Incident response runbook
- 📝 Recovery and audit tracking
- 🐳 Docker-based application deployment
- 🏗️ Terraform infrastructure configuration

---

# 🏗️ Architecture Overview

## Complete ResQCloud Architecture

The architecture below shows the main components that are actually part of the current project.

<img width="310" height="191" alt="Screenshot 2026-10-08 123818" src="https://github.com/user-attachments/assets/3f00251b-6e5a-4f15-bb4b-b3fce03d944d" />


### Architecture Layers

```text
User / Operator
      ↓
ResQCloud Web Dashboard
      ↓
Python + Flask Backend
      ↓
┌────────────┬────────────┬────────────┬────────────┐
│  Backup    │ Monitoring │  Incident  │  Recovery  │
│  Service   │  Service   │  Service   │  Service   │
└─────┬──────┴──────┬─────┴──────┬─────┴──────┬─────┘
      │             │             │            │
      ▼             ▼             ▼            ▼
     S3         CloudWatch     Database       S3/EC2
      │
      ▼
SHA-256 Verification
      ↓
Recovery
      ↓
Validation
      ↓
Audit
```

---

# 🔄 Complete System Flow

```text
                 ┌─────────────────────┐
                 │ 1. Monitor          │
                 │ Infrastructure      │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ 2. Detect           │
                 │ Abnormal condition  │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ 3. Analyse         │
                 │ Incident            │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ 4. Find Backup      │
                 │ Suitable recovery   │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ 5. Verify SHA-256   │
                 │ Backup integrity    │
                 └──────────┬──────────┘
                            ↓
                       ┌────┴────┐
                       │ Valid?  │
                       └────┬────┘
                        YES │
                            ↓
                 ┌─────────────────────┐
                 │ 6. Recover          │
                 │ Restore data        │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ 7. Validate         │
                 │ Recovery health     │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ 8. Close & Audit    │
                 └─────────────────────┘

If SHA-256 verification fails:
                └──────────────→ 🛑 Stop recovery
```

---

# ⚙️ Core Features

## 1. 📊 Infrastructure Monitoring

ResQCloud uses **Amazon CloudWatch** for infrastructure monitoring.

```text
AWS / EC2 Resource
        ↓
CloudWatch Metrics
        ↓
Monitoring Service
        ↓
ResQCloud Dashboard
        ↓
Incident Investigation
```

Monitoring provides visibility into resource health and operational metrics.

---

## 2. 💾 Backup Management

Amazon S3 is used as the backup storage layer.

```text
Source Data
    ↓
Backup Service
    ↓
Generate Backup ID
    ↓
Calculate SHA-256
    ↓
Upload to Amazon S3
    ↓
Store Backup Metadata
```

Backup information includes:

- Backup ID
- Source
- S3 bucket
- Object key
- SHA-256 checksum
- Creation time
- Status

---

## 3. 🔐 Backup Integrity Verification

ResQCloud verifies a backup before using it for recovery.

```text
Backup in S3
    ↓
Read / Download
    ↓
Calculate SHA-256
    ↓
Compare With Expected Checksum
    ↓
┌───────────────┐
│   Match?      │
└───────┬───────┘
    YES │
        ↓
 Trusted Backup
        ↓
    Recovery

If mismatch:
        ↓
   🛑 Stop Recovery
```

This provides a safety gate against restoring a backup whose contents do not match the expected checksum.

---

## 4. 🚨 Incident Management

```text
Monitoring
    ↓
Abnormal Condition
    ↓
Incident Record
    ↓
Severity / Status
    ↓
Operator Analysis
    ↓
Recovery Decision
```

The dashboard provides an Incidents section for reviewing and managing operational incidents.

---

## 5. ♻️ Disaster Recovery

```text
Incident
   ↓
Analyse
   ↓
Find Backup
   ↓
Verify Integrity
   ↓
Recovery Request
   ↓
Restore
   ↓
Validate
   ↓
Close Incident
```

The important principle is:

> **Verify the backup before recovery.**

---

## 6. 📖 Incident Response Runbook

The dashboard includes a guided runbook for handling incidents.

### Detect
Identify the affected infrastructure.

### Analyse
Review incident information and available backups.

### Recover
Select a suitable verified backup and perform recovery.

### Verify
Confirm that restoration and service/resource validation completed successfully.

```text
🔎 Detect
   ↓
🧠 Analyse
   ↓
💾 Select Backup
   ↓
🔐 Verify
   ↓
♻️ Recover
   ↓
✅ Validate
   ↓
📝 Close / Audit
```

---

# 🖥️ Dashboard

The ResQCloud dashboard provides centralized access to:

| Section | Purpose |
|---|---|
| 📊 Dashboard | Infrastructure and resilience overview |
| 💾 Backups | Backup management and verification |
| ♻️ Recovery | Recovery requests and restoration |
| 🚨 Incidents | Incident management |
| 📖 Runbook | Guided incident response |
| 📝 Audit | Operational activity |
| ⚙️ Settings | Application settings |

---

# 🧰 Technology Stack

| Category | Technology |
|---|---|
| Backend | Python |
| Framework | Flask |
| Frontend | HTML, CSS, JavaScript |
| Cloud | AWS |
| Compute | Amazon EC2 |
| Storage | Amazon S3 |
| Monitoring | Amazon CloudWatch |
| Security | AWS IAM |
| Database | SQLite / SQLAlchemy |
| Integrity | SHA-256 |
| Containerization | Docker |
| Infrastructure as Code | Terraform |
| Version Control | Git / GitHub |

Only technologies currently used in the project are listed here.

---

# ☁️ AWS Services Used

## Amazon EC2

Used to host the ResQCloud application and run the Dockerized backend.

## Amazon S3

Used as the backup object-storage layer.

## Amazon CloudWatch

Used for infrastructure monitoring and metrics.

## AWS IAM

Used for AWS access control and permissions.

### AWS flow

```text
                 AWS
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
       EC2        S3    CloudWatch
        │       Backups    Metrics
        │         │         │
        └─────────┼─────────┘
                  │
            ResQCloud
             Backend
```

---

# 🐳 Docker Deployment

Docker is used to package and run the ResQCloud application.

```text
GitHub
   ↓
Clone / Pull
   ↓
Docker Build
   ↓
Docker Image
   ↓
AWS EC2
   ↓
ResQCloud Container
   ↓
Flask Application
   ↓
Dashboard
```

Example:

```bash
docker compose build --no-cache resqcloud-backend
docker compose up -d --force-recreate resqcloud-backend
```

---

# 🏗️ Terraform Infrastructure

Terraform is used for Infrastructure as Code.

```text
Terraform Configuration
          ↓
     AWS Resources
          ↓
 ┌────────┼────────┐
 │        │        │
EC2      S3       IAM
 │        │        │
 └────────┼────────┘
          ↓
 ResQCloud Deployment
```

Terraform state and plan artifacts are excluded from Git.

---

# 📁 Project Structure

```text
ResQCloud/
│
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── requirements.txt
│   │
│   ├── services/
│   │   ├── backup/
│   │   │   ├── __init__.py
│   │   │   ├── backup_service.py
│   │   │   └── backup_verifier.py
│   │   │
│   │   ├── incident/
│   │   │   └── incident_detector.py
│   │   │
│   │   ├── monitoring/
│   │   │   ├── cloudwatch_monitor.py
│   │   │   └── cloudwatch_monitoring.py
│   │   │
│   │   ├── notification/
│   │   └── recovery/
│   │
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │
│   └── templates/
│       └── index.html
│
├── infrastructure/
├── scripts/
├── tests/
├── docs/
│   └── images/
│       └── ResQCloud-Architecture.png
│
├── infrastructure.tfvars.example
├── outputs.tf
├── .gitignore
└── README.md
```

---

# 📋 Prerequisites

- Python 3.x
- Git
- AWS account
- AWS CLI
- Docker
- Terraform
- VS Code or another code editor

---

# ⚙️ Setup & Installation

## 1. Clone the repository

```bash
git clone https://github.com/Abhinavpolishetti9182/ResQCloud.git
cd ResQCloud
```

## 2. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
cd backend
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a local `.env` file.

Example:

```env
AWS_REGION=ap-south-2
S3_BACKUP_BUCKET=your-backup-bucket
```

Never commit `.env` to GitHub.

## 5. Run the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Health check:

```text
http://127.0.0.1:5000/health
```

---

# 🧪 Testing & Validation

### Python validation

```powershell
python -m compileall -q .
```

### Application health

```powershell
Invoke-WebRequest http://127.0.0.1:5000/health
```

### Resilience workflow

```text
Create Backup
      ↓
Confirm S3 Object
      ↓
Verify SHA-256
      ↓
Restore Backup
      ↓
Validate Restored Data
      ↓
Review Recovery
      ↓
Review Incident
      ↓
Review Audit
```

---

# 🔒 Security

ResQCloud uses:

- AWS IAM access control
- S3 server-side encryption
- SHA-256 backup verification
- Environment variables for sensitive configuration
- `.gitignore` protection
- Terraform state exclusion
- Terraform plan exclusion
- Private key exclusion

### Never commit

```text
.env
*.pem
*.key
*.db
*.tfstate
*.tfplan
terraform.tfvars
```

---

# 🚨 Disaster Recovery Scenario

Imagine a protected resource becomes unavailable.

```text
Protected Resource
       ↓
Failure / Anomaly
       ↓
CloudWatch Monitoring
       ↓
Incident
       ↓
Analyse
       ↓
Find Backup
       ↓
SHA-256 Verification
       ↓
Backup Trusted?
       ↓
Restore
       ↓
Validate
       ↓
Close Incident
       ↓
Audit
```

If the checksum does not match:

```text
Backup
  ↓
SHA-256 Verification
  ↓
Mismatch
  ↓
🛑 Recovery stopped
```

---

# 🛠️ Troubleshooting

## Flask application does not start

```powershell
python --version
pip install -r requirements.txt
python -m compileall -q .
python app.py
```

## Docker container issue

```bash
docker ps
docker logs resqcloud-backend
docker compose ps
docker compose logs resqcloud-backend
```

## AWS issue

Check identity:

```bash
aws sts get-caller-identity
```

Check configuration:

```bash
aws configure list
```

Then verify the IAM permissions required for the specific AWS operation.

## S3 backup issue

Check:

- AWS credentials / IAM role
- AWS region
- S3 bucket name
- S3 permissions
- `S3_BACKUP_BUCKET`
- Network connectivity

---

# 📌 Project Status

## Current implementation

ResQCloud currently contains:

- ✅ Flask backend
- ✅ Web dashboard
- ✅ Backup management
- ✅ Amazon S3 integration
- ✅ SHA-256 backup integrity verification
- ✅ Incident management
- ✅ Recovery workflow
- ✅ CloudWatch monitoring integration
- ✅ Incident response runbook
- ✅ Docker deployment
- ✅ AWS EC2 deployment
- ✅ Terraform infrastructure
- ✅ Git / GitHub source control

This README intentionally lists only the technologies and components currently used in the project.

---

# 🤝 Contributing

```bash
git clone https://github.com/Abhinavpolishetti9182/ResQCloud.git
cd ResQCloud
git checkout -b feature/your-feature-name
```

After making and testing changes:

```bash
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name
```

Then create a Pull Request.

---

# 👨‍💻 Author

## Abhinav Polishetti

**B.Tech — Computer Science & Engineering**

### Focus Areas

- ☁️ Cloud Computing
- AWS
- DevOps
- Cloud Security
- Infrastructure Automation
- Backup & Disaster Recovery
- Monitoring & Incident Response

### Project

**ResQCloud — Automated Backup, Disaster Recovery & Incident Response Platform**

GitHub:

https://github.com/Abhinavpolishetti9182/ResQCloud

---

# ⭐ ResQCloud

> **Detect fast. Recover faster. Trust by design.**
