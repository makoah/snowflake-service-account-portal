import streamlit as st
import pandas as pd
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import base64
import io
import zipfile
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Snowflake Service Account Portal (Local Testing)",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #cce7ff;
        border: 1px solid #007acc;
        color: #004080;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class KeyPairGenerator:
    """Handles RSA key pair generation"""
    
    @staticmethod
    def generate_key_pair(key_size: int = 2048) -> Tuple[str, str]:
        """Generate RSA key pair and return private/public keys as strings"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Serialize public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"Error generating key pair: {str(e)}")
            raise

class MockSnowflakeManager:
    """Mock Snowflake manager for local testing - simulates Snowflake operations"""
    
    def __init__(self):
        self.connection = None
        self.is_connected = False
    
    def connect(self, account: str, user: str, password: str, warehouse: str = None, database: str = None):
        """Simulate connection to Snowflake"""
        try:
            # Mock validation - just check if fields are provided
            if account and user and password:
                self.is_connected = True
                logger.info(f"Mock connection established for {user}@{account}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Mock Snowflake connection error: {str(e)}")
            return False
    
    def create_service_account(self, username: str, public_key: str, role: str = None) -> bool:
        """Mock service account creation - always succeeds for testing"""
        try:
            if not self.is_connected:
                return False
            
            # Simulate account creation
            logger.info(f"Mock: Creating service account '{username}' with role '{role}'")
            
            # Mock SQL execution
            create_user_sql = f"""
            CREATE USER IF NOT EXISTS {username}
            RSA_PUBLIC_KEY = '[CLEANED_PUBLIC_KEY]'
            DEFAULT_WAREHOUSE = 'COMPUTE_WH'
            MUST_CHANGE_PASSWORD = FALSE
            """
            
            if role:
                grant_role_sql = f"GRANT ROLE {role} TO USER {username}"
                logger.info(f"Mock SQL: {grant_role_sql}")
            
            logger.info(f"Mock SQL: {create_user_sql}")
            
            # Always return success for testing
            return True
            
        except Exception as e:
            logger.error(f"Mock error creating service account: {str(e)}")
            return False

def create_download_zip(accounts_data: List[Dict]) -> bytes:
    """Create a ZIP file containing all private keys and account info"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Create summary file
        summary_data = []
        for account in accounts_data:
            summary_data.append({
                'username': account['username'],
                'created_date': account.get('created_date', datetime.now().isoformat()),
                'role': account.get('role', 'N/A'),
                'purpose': account.get('purpose', 'N/A')
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_csv = summary_df.to_csv(index=False)
        zip_file.writestr('account_summary.csv', summary_csv)
        
        # Add individual private keys
        for account in accounts_data:
            filename = f"{account['username']}_private_key.pem"
            zip_file.writestr(filename, account['private_key'])
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    st.markdown('<h1 class="main-header">❄️ Snowflake Service Account Portal (Local Testing)</h1>', unsafe_allow_html=True)
    
    # Testing mode notice
    st.markdown("""
    <div class="info-box">
        <strong>🧪 LOCAL TESTING MODE</strong><br>
        This version is configured for local testing without requiring actual Snowflake connectivity.
        All Snowflake operations are mocked. Key generation is fully functional.
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'accounts_created' not in st.session_state:
        st.session_state.accounts_created = []
    if 'snowflake_connected' not in st.session_state:
        st.session_state.snowflake_connected = False
    
    # Sidebar for Snowflake connection (Mock)
    with st.sidebar:
        st.markdown('<div class="section-header">Mock Snowflake Connection</div>', unsafe_allow_html=True)
        st.info("🧪 Testing Mode: Enter any values to simulate connection")
        
        account = st.text_input("Account Name", placeholder="test.snowflakecomputing.com", value="test-account")
        user = st.text_input("Admin Username", value="test_admin")
        password = st.text_input("Password", type="password", value="test_password")
        warehouse = st.text_input("Warehouse (optional)", placeholder="COMPUTE_WH", value="COMPUTE_WH")
        database = st.text_input("Database (optional)", value="TEST_DB")
        
        if st.button("Connect to Snowflake (Mock)"):
            sf_manager = MockSnowflakeManager()
            if sf_manager.connect(account, user, password, warehouse, database):
                st.session_state.snowflake_connected = True
                st.session_state.sf_manager = sf_manager
                st.success("✅ Mock connection established!")
                st.info("All Snowflake operations will be simulated.")
            else:
                st.error("❌ Mock connection failed - please fill in all fields")
        
        if st.session_state.snowflake_connected:
            st.success("🔗 Mock Snowflake Connected")
            st.caption("Service accounts will be simulated")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🆕 Single Account", "📊 Bulk Creation", "📋 Account Status", "🔧 Settings"])
    
    with tab1:
        st.markdown('<div class="section-header">Create Single Service Account</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Service Account Username", placeholder="svc_tableau_prod")
            purpose = st.selectbox("Purpose", ["Tableau", "PowerBI", "Data Factory", "Python/Scripts", "Other"])
            if purpose == "Other":
                purpose = st.text_input("Specify purpose")
            
            role = st.selectbox("Snowflake Role", ["PUBLIC", "SYSADMIN", "ACCOUNTADMIN", "Custom"])
            if role == "Custom":
                role = st.text_input("Custom Role Name")
            
            expiry_days = st.number_input("Key Expiry (days)", min_value=30, max_value=365, value=90)
        
        with col2:
            requestor_name = st.text_input("Requestor Name")
            requestor_email = st.text_input("Requestor Email")
            business_justification = st.text_area("Business Justification")
        
        if st.button("🔑 Generate Account & Keys", type="primary"):
            if username and requestor_name and requestor_email:
                try:
                    # Generate key pair
                    key_gen = KeyPairGenerator()
                    private_key, public_key = key_gen.generate_key_pair()
                    
                    account_data = {
                        'username': username,
                        'purpose': purpose,
                        'role': role,
                        'requestor_name': requestor_name,
                        'requestor_email': requestor_email,
                        'business_justification': business_justification,
                        'private_key': private_key,
                        'public_key': public_key,
                        'created_date': datetime.now().isoformat(),
                        'expiry_date': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
                        'created_in_snowflake': False
                    }
                    
                    # Create in Snowflake if connected (Mock)
                    if st.session_state.snowflake_connected:
                        if st.session_state.sf_manager.create_service_account(username, public_key, role):
                            account_data['created_in_snowflake'] = True
                            st.success(f"✅ Service account '{username}' created in Snowflake! (Simulated)")
                        else:
                            st.warning("⚠️ Keys generated but failed to create account in Snowflake (Simulated)")
                    else:
                        st.info("🔗 Connect to Snowflake to enable automatic account creation")
                    
                    st.session_state.accounts_created.append(account_data)
                    
                    # Display success
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.write(f"**Account Created:** {username}")
                    st.write(f"**Purpose:** {purpose}")
                    st.write(f"**Role:** {role}")
                    st.write(f"**Expires:** {account_data['expiry_date'][:10]}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Display key previews (first 100 characters for security)
                    with st.expander("🔍 View Key Previews (First 100 characters)"):
                        st.text("Private Key Preview:")
                        st.code(private_key[:100] + "...", language="text")
                        st.text("Public Key Preview:")
                        st.code(public_key[:100] + "...", language="text")
                    
                    # Download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download Private Key",
                            data=private_key,
                            file_name=f"{username}_private_key.pem",
                            mime="application/x-pem-file"
                        )
                    with col2:
                        st.download_button(
                            label="📥 Download Public Key",
                            data=public_key,
                            file_name=f"{username}_public_key.pem",
                            mime="application/x-pem-file"
                        )
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.markdown('<div class="section-header">Bulk Account Creation</div>', unsafe_allow_html=True)
        
        # Template download
        st.write("**Step 1:** Download the template CSV and fill in your service account requirements")
        
        template_data = {
            'username': ['svc_tableau_prod', 'svc_powerbi_dev', 'svc_datafactory_etl'],
            'purpose': ['Tableau', 'PowerBI', 'Data Factory'],
            'role': ['SYSADMIN', 'PUBLIC', 'SYSADMIN'],
            'requestor_name': ['John Doe', 'Jane Smith', 'Bob Wilson'],
            'requestor_email': ['john.doe@company.com', 'jane.smith@company.com', 'bob.wilson@company.com'],
            'business_justification': ['Production Tableau dashboards', 'Development PowerBI reports', 'ETL data pipelines'],
            'expiry_days': [90, 60, 120]
        }
        template_df = pd.DataFrame(template_data)
        
        st.download_button(
            label="📥 Download Template CSV",
            data=template_df.to_csv(index=False),
            file_name="service_accounts_template.csv",
            mime="text/csv"
        )
        
        st.write("**Step 2:** Upload your completed CSV file")
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("**Preview:**")
                st.dataframe(df.head())
                
                if st.button("🚀 Create All Accounts", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    bulk_accounts = []
                    
                    for idx, row in df.iterrows():
                        progress = (idx + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Creating account {idx + 1}/{len(df)}: {row['username']}")
                        
                        # Generate keys
                        key_gen = KeyPairGenerator()
                        private_key, public_key = key_gen.generate_key_pair()
                        
                        account_data = {
                            'username': row['username'],
                            'purpose': row['purpose'],
                            'role': row['role'],
                            'requestor_name': row['requestor_name'],
                            'requestor_email': row['requestor_email'],
                            'business_justification': row['business_justification'],
                            'private_key': private_key,
                            'public_key': public_key,
                            'created_date': datetime.now().isoformat(),
                            'expiry_date': (datetime.now() + timedelta(days=row['expiry_days'])).isoformat(),
                            'created_in_snowflake': False
                        }
                        
                        # Create in Snowflake if connected (Mock)
                        if st.session_state.snowflake_connected:
                            if st.session_state.sf_manager.create_service_account(row['username'], public_key, row['role']):
                                account_data['created_in_snowflake'] = True
                        
                        bulk_accounts.append(account_data)
                    
                    # Add to session state
                    st.session_state.accounts_created.extend(bulk_accounts)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ All accounts created!")
                    
                    st.success(f"Successfully created {len(bulk_accounts)} service accounts!")
                    
                    # Download ZIP with all keys
                    zip_data = create_download_zip(bulk_accounts)
                    st.download_button(
                        label="📦 Download All Keys (ZIP)",
                        data=zip_data,
                        file_name=f"service_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
    
    with tab3:
        st.markdown('<div class="section-header">Account Status & Management</div>', unsafe_allow_html=True)
        
        if st.session_state.accounts_created:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_accounts = len(st.session_state.accounts_created)
            snowflake_accounts = sum(1 for acc in st.session_state.accounts_created if acc['created_in_snowflake'])
            
            with col1:
                st.metric("Total Accounts", total_accounts)
            with col2:
                st.metric("Created in Snowflake", snowflake_accounts)
            with col3:
                st.metric("Pending Creation", total_accounts - snowflake_accounts)
            with col4:
                success_rate = (snowflake_accounts/total_accounts*100) if total_accounts > 0 else 0
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Accounts table
            st.write("**Account Details:**")
            
            display_data = []
            for acc in st.session_state.accounts_created:
                display_data.append({
                    'Username': acc['username'],
                    'Purpose': acc['purpose'],
                    'Role': acc['role'],
                    'Requestor': acc['requestor_name'],
                    'Created Date': acc['created_date'][:10],
                    'Expires': acc['expiry_date'][:10],
                    'Snowflake Status': '✅ Created (Mock)' if acc['created_in_snowflake'] else '⏳ Pending'
                })
            
            df_display = pd.DataFrame(display_data)
            st.dataframe(df_display, use_container_width=True)
            
            # Bulk download option
            if st.button("📦 Download All Account Data"):
                zip_data = create_download_zip(st.session_state.accounts_created)
                st.download_button(
                    label="📥 Download ZIP",
                    data=zip_data,
                    file_name=f"all_service_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
        else:
            st.info("No service accounts created yet. Use the other tabs to create accounts.")
    
    with tab4:
        st.markdown('<div class="section-header">Settings & Configuration</div>', unsafe_allow_html=True)
        
        st.write("**Default Settings:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_key_size = st.selectbox("Default Key Size", [2048, 4096], index=0)
            default_expiry = st.number_input("Default Expiry (days)", min_value=30, max_value=365, value=90)
            auto_create_snowflake = st.checkbox("Auto-create in Snowflake when connected", value=True)
        
        with col2:
            notification_email = st.text_input("Notification Email (for platform team)")
            audit_retention = st.number_input("Audit Log Retention (days)", min_value=90, max_value=2555, value=365)
        
        st.write("**Local Testing Features:**")
        st.info("🧪 This local version includes mock Snowflake operations for testing the UI and key generation without requiring actual Snowflake connectivity.")
        
        if st.button("📊 Show Session Statistics"):
            st.json({
                "accounts_created": len(st.session_state.accounts_created),
                "snowflake_connected": st.session_state.snowflake_connected,
                "session_start_time": st.session_state.get('session_start', 'N/A')
            })
        
        st.write("**Cleanup Actions:**")
        if st.button("🗑️ Clear All Session Data", type="secondary"):
            if st.checkbox("I confirm I want to clear all data"):
                st.session_state.accounts_created = []
                st.session_state.snowflake_connected = False
                st.success("✅ Session data cleared")

if __name__ == "__main__":
    main()