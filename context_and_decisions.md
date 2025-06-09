# Context and Design Decisions

## Business Context

### Technical Application Owners (TAOs)
- **Definition**: TAOs own AD service accounts and passwords
- **Relationship**: One TAO can own multiple Snowflake service accounts (1-60 range)
- **Access**: TAOs have requested membership to specific AD groups
- **Technical Level**: Most work on Windows, lack crypto knowledge/tools

### Current Challenge
- Hundreds of service accounts need to be created
- Manual key pair generation is a barrier for Windows users
- Need centralized, automated solution for the platform team

## Design Decisions

### 1. TAO-Centric Authentication Model
**Decision**: Move from request-based to ownership-based model
- App recognizes current user (TAO) via AD/SSO integration
- Shows only service accounts owned by logged-in TAO
- Eliminates request approval workflow for owned accounts

### 2. Key Storage Strategy
**Decision**: Store keys in database with Row Level Security (RLS)
**Rationale**:
- ✅ More secure than email/file distribution
- ✅ Eliminates key handling risks
- ✅ Complete audit trail of all access
- ✅ Enables automated rotation workflows
- ⚠️ Requires encryption at rest
- ⚠️ Needs proper RLS implementation

### 3. Key Expiration & Rotation Process
**Decision**: Automated monitoring with self-service rotation
**Process**:
1. **Monitoring**: Daily job checks keys expiring in 30/7 days
2. **Notification**: Email alerts to TAOs with portal link
3. **Rotation**: TAO initiates rotation via portal
4. **Grace Period**: Keep old key active for 24-48 hours
5. **Cleanup**: Automated removal after confirmation

### 4. User Experience Design
**Decision**: Dashboard-style interface showing account health
- Color-coded status indicators (Green/Yellow/Red)
- Action buttons based on account status
- Self-service key management
- Download capabilities for immediate use

## Mock Data Structure

### TAO Profile
```json
{
  "username": "john.doe",
  "name": "John Doe", 
  "email": "john.doe@company.com",
  "department": "Data Analytics",
  "ad_groups": ["SNOWFLAKE_USERS", "TABLEAU_USERS"],
  "service_accounts": [...]
}
```

### Service Account
```json
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

## Security Considerations

### Database Storage
- Private keys encrypted at rest
- Row Level Security ensures TAOs only see their keys
- Audit logging for all key access/generation
- Secure connection to Snowflake for public key updates

### Key Rotation Security
- Old keys remain valid during grace period
- Automated cleanup prevents key sprawl
- Notification system alerts TAOs of upcoming expirations
- Self-service reduces platform team workload

## Future Enhancements

### Automation Opportunities
1. **Automated Rotation**: System-initiated rotation for critical accounts
2. **Application Integration**: Direct API updates to applications
3. **Monitoring Dashboards**: Platform team oversight of all TAO activities
4. **Compliance Reporting**: Automated reports for security/audit teams

### Scalability Features
1. **Bulk Operations**: TAO-initiated bulk rotation for multiple accounts
2. **Template Management**: Standardized account types with pre-configured settings
3. **Integration APIs**: Connect with ITSM systems for change management
4. **Advanced Analytics**: Usage patterns and optimization recommendations