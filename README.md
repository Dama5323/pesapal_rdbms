# PesaPal RDBMS Challenge
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![REST-API](https://img.shields.io/badge/REST-API-✓-success)
![Docs](https://img.shields.io/badge/Docs-Swagger-orange)
![Authentication](https://img.shields.io/badge/Auth-Custom_User_Model-important)
![Tested](https://img.shields.io/badge/Tested-Postman-blueviolet)
![Render](https://img.shields.io/badge/deployed_on-render-5363e6)
![License](https://img.shields.io/badge/License-MIT-yellow)
[👉 Try User Registration](https://pesapal-rdbms-gm67.onrender.com/register/)

## Live Demo

**Live URL:** [https://pesapal-rdbms-gm67.onrender.com](https://pesapal-rdbms-gm67.onrender.com)

**PesaPal RDBMS** is a **production-ready financial application** that solves critical problems of **data integrity, auditability, and regulatory compliance** in payment systems. Built with Django and featuring a custom immutable ledger, this system implements **core banking principles** with ACID-compliant transactions and secure financial workflows.

### 🎯 Key Innovation: Dual-Layer Architecture

The system's core innovation is its **dual-layer data architecture**:
- **Transactional Database**: PostgreSQL for high-performance operations
- **Immutable Ledger**: Custom cryptographic ledger for audit-proof records


### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **`ledger.py`** | Core immutable ledger logic (append, verify, hash chain) | `/rdbms/ledger.py` |
| **`LedgerTrackedModel`** | Django mixin for models needing ledger audit trails | Defined in `transactions/models.py` |
| **`services.py`** | Service layer coordinating ledger writes during transactions | `/services.py` |
| **`Transaction.save()`** | Overridden to auto-record `COMPLETED` transactions to ledger | `transactions/models.py` |
| **`Account.save()`** | Overridden to auto-record balance changes to ledger | `users/models.py` |


## ✨ Core Features

### 🔐 **Immutable Ledger System**
- **Cryptographic Hash Chains**: Every transaction creates an unbreakable link to previous records
- **Tamper-Evident Design**: Any modification invalidates subsequent hashes
- **Regulatory Compliance**: Meets financial audit requirements (KYC, AML)
- **Dual-Phase Recording**: All financial events stored in both database and ledger

### 💳 **Financial Transaction Engine**
- **ACID-Compliant Processing**: Atomic transfers with rollback capability
- **Multi-Currency Support**: KES, USD, EUR, GBP with real-time balance tracking
- **Transaction Types**: P2P transfers, merchant payments, bill payments, airtime
- **Fee & Tax Calculation**: Automated financial computations

### 👤 **Bank-Grade User Management**
- **Custom User Model**: Extended `AbstractUser` with email as username[citation:8]
- **KYC Verification**: Document workflow (PENDING → VERIFIED → REJECTED)
- **Financial Limits**: Daily/monthly transaction caps
- **Profile Management**: Employment, address, and preference tracking
### Data Flow Example: Money Transfer

```python
 1. User initiates transfer (Transaction created with status='PENDING')
transaction = Transaction.objects.create(...)

 2. System processes and completes transfer
transaction.status = 'COMPLETED'
transaction.save()  # Triggers ledger recording via save() override

3. Behind the scenes in save() method:
      - Generates ledger data via to_ledger_format()
      -  Calls rdbms_service.record_transaction()
      - Updates transaction.ledger_event_id and ledger_hash
      - Updates account balances (which also record to ledger)
```

![PesaPal RDBMS ERD](./pesapal_erd.drawio.png)


--- 

## Architecture
```
pesapal_rdbms/
├── web/                          # Django Web Application
│   ├── settings.py              # Project configuration
│   ├── urls.py                  # URL routing
│   ├── views.py                 # Request handlers
│   ├── rdbms_admin.py          # Custom admin interface for RDBMS
│   └── templates/               # HTML templates
├── users/                       # User Management App (Django models)
│   ├── models.py               # Custom User, Account & Profile models
│   ├── views.py                # User CRUD operations
│   └── admin.py                # Django admin customization
├── transactions/                # Financial Transactions App
│   ├── models.py               # Transaction, Invoice & AuditLog models
│   └── api/                    # REST API endpoints
├── rdbms/                       # Custom RDBMS Engine + Ledger System
│   ├── __init__.py             # Package initialization
│   ├── database.py             # Main Database class with transaction management
│   ├── table.py                # Table implementation with indexing & constraints
│   ├── parser.py               # SQL-like command parser
│   ├── ledger.py               # Core immutable ledger logic
│   ├── repl.py                 # Interactive SQL shell
│   └── storage.py              # JSON persistence layer
├── services.py                  # Orchestration layer (connects Django to RDBMS)
├── tasks/                       # Background job processing
├── data/                        # Storage for RDBMS data files
├── venv/                        # Virtual environment
├── manage.py                    # Django management
├── requirements.txt            # Dependencies
├── db.sqlite3                  # Django database (development)
└── README.md                   # This file
```

---

## Quick Start

### Verify Django Configuration

To confirm Django settings and database connectivity are correctly configured, run:

```bash
python check_config.py
```

## Installation & Setup

### **1. Prerequisites:**
- Python 3.8+
- pip (Python package manager)

### **2. Installation:**
```bash
# Clone or download the project
# Navigate to project directory
cd pesapal_rdbms

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up Django database
cd web
python manage.py migrate
```

### Usage
**1. Run the RDBMS REPL:**
```bash
cd pesapal_rdbms
python -m rdbms.repl
```

## Example REPL session:

```sql
rdbms> exec CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE)
rdbms> exec INSERT INTO users (id, name, email) VALUES (1, 'John', 'john@example.com')
rdbms> exec SELECT * FROM users
rdbms> exec UPDATE users SET name = 'Jane' WHERE id = 1
rdbms> exec DELETE FROM users WHERE id = 1
```

**2. Run the Web Application:**
```bash
cd pesapal_rdbms/web
python manage.py runserver
```

Visit http://localhost:8000 to see:

- User management interface

- Task management with JOIN demonstration

- API endpoints at /api/users/ and /api/tasks/


### Endpoints

###  Authentication
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/users/login/` | `POST` | User login with email/password | ❌ |
| `/api/users/logout/` | `POST` | User logout | ✅ |
| `/api/users/current/` | `GET` | Get current user profile | ✅ |

###  User Management
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/users/` | `GET` | List all users | ✅ (Admin) |
| `/api/users/<uuid:user_id>/` | `GET` | Get user details | ✅ |
| `/api/users/<uuid:user_id>/kyc/` | `PUT` | Update KYC status | ✅ (Admin) |
| `/api/users/<uuid:user_id>/accounts/` | `GET` | Get user's accounts | ✅ |

###  Financial Operations
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/transactions/create/` | `POST` | Create & record transaction | ✅ |
| `/api/transactions/<transaction_id>/audit/` | `GET` | Get cryptographic audit trail | ✅ |
| `/api/ledgers/verify/` | `GET` | Verify ledger chain integrity | ✅ |
| `/api/financial/report/` | `GET` | Generate financial reports | ✅ (Admin) |

### System Operations
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health/` | `GET` | System health check | ❌ |
| `/api/docs/` | `GET` | Interactive API documentation | ❌ |
| `/rdbms-admin/` | `GET` | Custom RDBMS admin interface | ✅ (Admin) |


### Live Examples
For complete API documentation with interactive examples, visit:  
**https://pesapal-rdbms-gm67.onrender.com/api/docs/**

### Authentication
All protected endpoints require a bearer token. Get your token:
```bash
curl -X POST https://pesapal-rdbms-gm67.onrender.com/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
  ```

### Demonstration of Requirements

**✅ Table Declaration:**
```python
db.create_table("users", 
    {"id": "INTEGER", "name": "TEXT", "email": "TEXT"},
    primary_key="id",
    unique_keys=["email"]
)
```

**✅ CRUD Operations:**
- Create: table.insert({"id": 1, "name": "John"})

- Read: table.select({"id": 1})

- Update: table.update({"name": "Jane"}, {"id": 1})

- Delete: table.delete({"id": 1})_

**✅ Primary & Unique Keys:**
- Primary key enforcement prevents duplicate IDs

- Unique key enforcement prevents duplicate emails

**✅ Basic Indexing:**
- Automatic indexing on primary and unique keys

- Faster lookups using indexes

**✅ JOIN Operations:**
```python
tasks.join(users, "user_id", "id", "LEFT")
```

**✅ SQL Interface:**
```sql
SELECT * FROM users WHERE id = 1
INSERT INTO users (id, name) VALUES (2, 'Alice')
UPDATE users SET name = 'Bob' WHERE id = 2
DELETE FROM users WHERE id = 2
```

**✅ REPL Mode:**
- Interactive SQL shell for testing queries

**✅ Web App Demonstration:**
Full CRUD application using the custom RDBMS

---

## Database Design


### Schema Definition

```sql
-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks Table (Demonstrates JOIN operations)
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for Performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_users_username ON users(username);
```
---

## Testing 

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test module
python -m pytest tests/test_database.py

# Run with coverage report
python -m pytest --cov=rdbms --cov-report=html
```
---

## Deployment


### **Production Deployment on Render.com**
- **Platform:** Render.com (Free Tier)
- **Database:** PostgreSQL with ACID compliance
- **URL:** https://pesapal-rdbms-gm67.onrender.com
- **Auto-deploy:** On Git push to main branch
- **SSL/HTTPS:** Automatic Let's Encrypt certificates

### **Local Development**
```bash
git clone https://github.com/Dama5323/pesapal_rdbms.git
cd pesapal_rdbms
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Authors

- **Damaris C hege Backend Developer and AWS Solutions Architect** - [GitHub](https://github.com/Dama5323) - [LinkedIn](https://linkedin.com/in/dama5323)

## Acknowledgments

- ALX Software Engineering Program for guidance

- Render.com for hosting infrastructure

- Django community for excellent documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  Made with ❤️ for the pesapal rdbms 2026 challene/add to my portfolio 
  <br>
  <sub>If you find this useful, give it a ⭐!</sub>
</div>