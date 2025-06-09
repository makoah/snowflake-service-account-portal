# Snowflake Service Account Portal

A Streamlit application for automating Snowflake service account creation and RSA key pair generation.

## Features

- **Self-Service Portal**: Technical owners can request service accounts through a web interface
- **Automated Key Generation**: RSA key pairs generated automatically with configurable key sizes
- **Bulk Provisioning**: Upload CSV files to create multiple accounts at once
- **Snowflake Integration**: Direct API integration to create service accounts
- **Secure Distribution**: Download individual keys or bulk ZIP packages
- **Audit Trail**: Track all account creations and requests
- **Role Management**: Assign appropriate Snowflake roles during creation

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run streamlit_app.py
```

3. Connect to Snowflake using admin credentials in the sidebar

4. Start creating service accounts!

## Usage Scenarios

### Single Account Creation
- Use the "Single Account" tab for individual requests
- Fill in username, purpose, role, and requestor details
- Generate and download private/public key pairs
- Account is automatically created in Snowflake if connected

### Bulk Account Creation
- Download the CSV template
- Fill in multiple account details
- Upload and process all accounts at once
- Download ZIP file containing all private keys

### Account Management
- View all created accounts in the "Account Status" tab
- Track which accounts were successfully created in Snowflake
- Download historical account data

## Security Features

- Private keys are generated locally and never stored permanently
- Secure ZIP packaging for bulk key distribution
- Audit logging of all account creation activities
- Configurable key expiration dates
- Role-based access control integration

## Configuration

Configure default settings in the Settings tab:
- Default RSA key size (2048 or 4096 bits)
- Default key expiration period
- Notification emails for the platform team
- Audit log retention periods

## Snowflake Setup

Ensure your Snowflake admin account has permissions to:
- Create users (`CREATE USER`)
- Grant roles (`GRANT ROLE`)
- Manage RSA public keys

## Deployment Options

### Local Development
```bash
streamlit run streamlit_app.py
```

### Snowflake Native Apps
Deploy as a Streamlit in Snowflake app for centralized access

### Docker Deployment
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Benefits for Platform Teams

1. **Reduced Manual Work**: Automates key generation and account creation
2. **Standardized Process**: Consistent account naming and role assignment
3. **Self-Service**: Reduces tickets and support burden
4. **Audit Compliance**: Built-in tracking and logging
5. **Scalability**: Handle hundreds of accounts efficiently
6. **User-Friendly**: No technical knowledge required for requestors

## Technical Implementation

- **RSA Key Generation**: Uses Python `cryptography` library for secure key generation
- **Snowflake API**: Direct integration using `snowflake-connector-python`
- **File Handling**: Secure ZIP packaging for bulk downloads
- **Session Management**: Streamlit session state for multi-step workflows
- **Error Handling**: Comprehensive error catching and user feedback