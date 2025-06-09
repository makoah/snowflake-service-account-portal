# Snowflake Service Account Provisioning Process

## **PHASE 1: REQUEST INITIATION**

### Step 1.1: Service Account Request
**Role:** Technical Application Owner  
**Essential Inputs:**
- Service account username (naming convention)
- Application purpose (Tableau, PowerBI, Data Factory, Python)
- Environment (prod, dev, test)
- Required Snowflake role/permissions
- Business justification
- Requestor contact details
- Expected usage patterns
- Key expiration preference

**Prerequisites:**
- Access to Streamlit portal
- Understanding of application requirements
- Business case approval (if required)

**Output:** Completed request form in portal

---

### Step 1.2: Request Review
**Role:** Platform Team  
**Essential Inputs:**
- Submitted request details
- Naming convention validation
- Security requirements check

**Prerequisites:**
- Platform team access to portal
- Snowflake naming standards documented
- Security policies defined

**Output:** Request validation (approved/rejected/needs clarification)

---

## **PHASE 2: VALIDATION & APPROVAL**

### Step 2.1: Security Review (if required)
**Role:** Security Team  
**Essential Inputs:**
- Service account purpose
- Requested permissions/roles
- Data access requirements
- Compliance requirements

**Prerequisites:**
- Security approval thresholds defined
- Risk assessment criteria
- Escalation matrix

**Output:** Security approval/rejection

---

### Step 2.2: Business Approval (if required)
**Role:** Business Stakeholder/Manager  
**Essential Inputs:**
- Business justification
- Cost implications
- Data governance requirements

**Prerequisites:**
- Approval authority matrix
- Budget approval (if applicable)

**Output:** Business approval/rejection

---

## **PHASE 3: PROVISIONING**

### Step 3.1: Key Pair Generation
**Role:** Platform Team (via Streamlit portal)  
**Essential Inputs:**
- Approved request details
- Key size preference (2048/4096)
- Expiration timeline

**Prerequisites:**
- Platform team access to portal
- Streamlit portal operational
- Snowflake admin credentials configured

**Output:** RSA key pair generated, account created in Snowflake

---

### Step 3.2: Account Configuration
**Role:** Platform Team  
**Essential Inputs:**
- Generated public key
- Role assignments
- Warehouse assignments
- Network policies (if applicable)

**Prerequisites:**
- Snowflake admin privileges
- Role/warehouse provisioning standards
- Network security policies

**Output:** Fully configured service account in Snowflake

---

## **PHASE 4: SECURE DISTRIBUTION**

### Step 4.1: Key Packaging
**Role:** Platform Team  
**Essential Inputs:**
- Generated private key
- Account documentation
- Usage instructions

**Prerequisites:**
- Secure distribution method defined
- Documentation templates

**Output:** Secure key package ready for distribution

---

### Step 4.2: Key Distribution
**Role:** Platform Team  
**Essential Inputs:**
- Requestor contact information
- Preferred delivery method
- Security requirements

**Prerequisites:**
- Secure communication channels
- Key handling procedures documented

**Output:** Private key delivered to requestor

---

### Step 4.3: Implementation Support
**Role:** Platform Team + Technical Application Owner  
**Essential Inputs:**
- Private key file
- Connection parameters
- Application-specific configuration

**Prerequisites:**
- Technical documentation for each application type
- Support procedures defined
- Testing environment available

**Output:** Working service account integration

---

## **PHASE 5: ONGOING MANAGEMENT**

### Step 5.1: Usage Monitoring
**Role:** Platform Team  
**Essential Inputs:**
- Snowflake usage logs
- Account activity monitoring
- Performance metrics

**Prerequisites:**
- Monitoring tools configured
- Alert thresholds defined
- Reporting dashboards

**Output:** Usage reports and alerts

---

### Step 5.2: Key Rotation
**Role:** Platform Team + Technical Application Owner  
**Essential Inputs:**
- Key expiration dates
- Application maintenance windows
- New key generation

**Prerequisites:**
- Key rotation schedule
- Automated rotation capabilities (future)
- Change management process

**Output:** Rotated keys and updated configurations

---

### Step 5.3: Account Lifecycle Management
**Role:** Platform Team  
**Essential Inputs:**
- Account usage patterns
- Business requirement changes
- Decommissioning requests

**Prerequisites:**
- Lifecycle policies defined
- Decommissioning procedures
- Data retention requirements

**Output:** Updated or decommissioned accounts

---

## **CRITICAL INPUTS SUMMARY**

### **For Each Request:**
1. **Service Account Name** (following naming convention)
2. **Requestor Details** (name, email, team)
3. **Application Type** (Tableau, PowerBI, etc.)
4. **Environment** (prod, dev, test)
5. **Snowflake Role Required**
6. **Business Justification**
7. **Key Expiration Preference**

### **Platform Prerequisites:**
1. **Streamlit Portal** deployed and accessible
2. **Snowflake Admin Credentials** configured
3. **Naming Conventions** documented
4. **Security Policies** defined
5. **Approval Workflows** established
6. **Support Documentation** for each application type

### **Operational Prerequisites:**
1. **Role-Based Access** to portal
2. **Secure Communication Channels** for key distribution
3. **Monitoring and Alerting** systems
4. **Change Management** processes
5. **Training Materials** for technical owners

---

## **ITERATION QUESTIONS**
1. Do you need additional approval steps for certain roles/environments?
2. Should we automate any of the approval workflows?
3. What's your preferred method for secure key distribution?
4. How do you want to handle bulk requests (1-60 accounts)?
5. What monitoring/alerting do you need for the platform team?