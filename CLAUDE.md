# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Architecture

This repository contains a Streamlit-based portal for automating Snowflake service account creation and RSA key pair management. There are three main application variants:

### Core Applications
- **`streamlit_app.py`** - Production version with full Snowflake integration using `snowflake-connector-python`
- **`streamlit_app_local.py`** - Local testing version with mock Snowflake operations (no Snowflake dependency)
- **`streamlit_app_tao.py`** - Technical Application Owner (TAO) centric version with user authentication and service account ownership model

### Key Architectural Patterns
- **Mock vs Real Integration**: Local versions use `MockSnowflakeManager` class to simulate Snowflake operations for testing without requiring actual Snowflake connectivity
- **Session State Management**: All applications use Streamlit session state to maintain user data, connection status, and created accounts across page interactions
- **Modular Key Generation**: `KeyPairGenerator` class handles RSA key pair creation using the `cryptography` library, consistent across all versions
- **TAO Ownership Model**: `streamlit_app_tao.py` implements a user-centric approach where Technical Application Owners manage their own service accounts rather than a request-based workflow

## Common Development Commands

### Running Applications
```bash
# Production version (requires Snowflake connectivity)
streamlit run streamlit_app.py

# Local testing version (no external dependencies)
pip install -r requirements_local.txt
streamlit run streamlit_app_local.py

# TAO-centric version (includes mock authentication)
streamlit run streamlit_app_tao.py
```

### Dependency Management
```bash
# Production dependencies (includes snowflake-connector-python)
pip install -r requirements.txt

# Local testing dependencies (minimal set)
pip install -r requirements_local.txt
```

## Business Context and Design Decisions

### TAO (Technical Application Owner) Model
- TAOs own AD service accounts and can have 1-60 Snowflake service accounts
- The TAO-centric app (`streamlit_app_tao.py`) shows only accounts owned by the logged-in user
- Mock data structure includes TAO profiles with department, AD groups, and owned service accounts
- Key rotation includes 24-48 hour grace periods where both old and new keys remain valid

### Key Storage Strategy
The architecture supports two key storage approaches:
- **Session-based**: Keys generated and downloaded immediately (current implementation)
- **Database with RLS**: Future enhancement storing encrypted keys in database with Row Level Security for centralized management and automated rotation

### Application Integration
Generated RSA key pairs work universally across:
- PowerBI (connection strings and gateway configurations)
- Tableau (connector configuration)
- Python scripts (snowflake-connector-python)
- Azure Data Factory (linked services)
- Any ODBC/JDBC client

## Mock Data Structure

### TAO Profile Structure
```python
{
    "username": "john.doe",
    "name": "John Doe",
    "email": "john.doe@company.com", 
    "department": "Data Analytics",
    "ad_groups": ["SNOWFLAKE_USERS", "TABLEAU_USERS"],
    "service_accounts": [...]
}
```

### Service Account Structure
```python
{
    "username": "svc_tableau_prod_analytics",
    "purpose": "Tableau Production Dashboards",
    "environment": "PROD",
    "snowflake_role": "ANALYTICS_ROLE",
    "created_date": "2024-01-15",
    "key_expiry": "2024-07-15", 
    "status": "active|expiring_soon|expired",
    "last_rotation": "2024-01-15",
    "has_key": true
}
```

## Security Implementation

### Key Generation
- Uses Python `cryptography` library with RSA 2048/4096 bit keys
- Private keys serialized as PEM format with PKCS8 encoding
- Public keys cleaned (headers removed) before Snowflake storage
- No encryption algorithm applied to private keys for application compatibility

### Snowflake Integration
- Service accounts created with `CREATE USER` and `RSA_PUBLIC_KEY` parameter
- Role assignment via `GRANT ROLE` statements
- Key rotation updates existing users with `ALTER USER SET RSA_PUBLIC_KEY`

### Future Azure Key Vault Integration
The architecture is designed to support Azure Key Vault integration where:
- Applications reference Key Vault secrets instead of storing private keys directly
- Key rotation updates only the Key Vault secret
- Applications automatically fetch updated keys at runtime

## Process Workflow Integration

The `process_workflow.md` file documents the complete enterprise process from request initiation through lifecycle management. The Streamlit applications implement Phase 3 (Provisioning) and support Phase 4 (Distribution) of this workflow.

Key workflow phases:
1. Request Initiation (manual/TAO-driven)
2. Validation & Approval (manual/future automation)
3. Provisioning (automated via Streamlit apps)
4. Secure Distribution (download/future Key Vault)
5. Ongoing Management (rotation/monitoring)