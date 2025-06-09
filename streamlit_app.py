import streamlit as st
import pandas as pd
import snowflake.connector
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
    page_title="Snowflake Service Account Portal",
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

class SnowflakeManager:
    """Handles Snowflake connections and operations"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self, account: str, user: str, password: str, warehouse: str = None, database: str = None):
        """Establish connection to Snowflake"""
        try:
            conn_params = {
                'account': account,
                'user': user,
                'password': password,
            }
            if warehouse:
                conn_params['warehouse'] = warehouse
            if database:
                conn_params['database'] = database
                
            self.connection = snowflake.connector.connect(**conn_params)
            return True
        except Exception as e:
            logger.error(f"Snowflake connection error: {str(e)}")
            return False
    
    def create_service_account(self, username: str, public_key: str, role: str = None) -> bool:
        """Create service account in Snowflake with public key"""
        try:
            if not self.connection:
                return False
            
            cursor = self.connection.cursor()
            
            # Clean public key (remove headers/footers for Snowflake)
            clean_key = public_key.replace('-----BEGIN PUBLIC KEY-----', '')
            clean_key = clean_key.replace('-----END PUBLIC KEY-----', '')
            clean_key = clean_key.replace('\n', '').replace('\r', '').strip()
            
            # Create user with public key authentication
            create_user_sql = f"""
            CREATE USER IF NOT EXISTS {username}
            RSA_PUBLIC_KEY = '{clean_key}'
            DEFAULT_WAREHOUSE = 'COMPUTE_WH'
            MUST_CHANGE_PASSWORD = FALSE
            """
            
            cursor.execute(create_user_sql)
            
            # Grant role if specified
            if role:
                grant_role_sql = f"GRANT ROLE {role} TO USER {username}"
                cursor.execute(grant_role_sql)
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating service account: {str(e)}")
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
    st.markdown('<h1 class="main-header">❄️ Snowflake Service Account Portal</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'accounts_created' not in st.session_state:
        st.session_state.accounts_created = []
    if 'snowflake_connected' not in st.session_state:
        st.session_state.snowflake_connected = False
    
    # Sidebar for Snowflake connection
    with st.sidebar:
        st.markdown('<div class="section-header">Snowflake Connection</div>', unsafe_allow_html=True)
        
        account = st.text_input("Account Name", placeholder="mycompany.snowflakecomputing.com")
        user = st.text_input("Admin Username")
        password = st.text_input("Password", type="password")
        warehouse = st.text_input("Warehouse (optional)", placeholder="COMPUTE_WH")
        database = st.text_input("Database (optional)")
        
        if st.button("Connect to Snowflake"):
            sf_manager = SnowflakeManager()
            if sf_manager.connect(account, user, password, warehouse, database):
                st.session_state.snowflake_connected = True
                st.session_state.sf_manager = sf_manager
                st.success("✅ Connected to Snowflake!")
            else:
                st.error("❌ Failed to connect to Snowflake")
        
        if st.session_state.snowflake_connected:
            st.success("🔗 Snowflake Connected")
    
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
                    
                    # Create in Snowflake if connected
                    if st.session_state.snowflake_connected:
                        if st.session_state.sf_manager.create_service_account(username, public_key, role):
                            account_data['created_in_snowflake'] = True
                            st.success(f"✅ Service account '{username}' created in Snowflake!")
                        else:
                            st.warning("⚠️ Keys generated but failed to create account in Snowflake")
                    
                    st.session_state.accounts_created.append(account_data)
                    
                    # Display success
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.write(f"**Account Created:** {username}")
                    st.write(f"**Purpose:** {purpose}")
                    st.write(f"**Role:** {role}")
                    st.write(f"**Expires:** {account_data['expiry_date'][:10]}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
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
            'username': ['svc_tableau_prod', 'svc_powerbi_dev'],
            'purpose': ['Tableau', 'PowerBI'],
            'role': ['SYSADMIN', 'PUBLIC'],
            'requestor_name': ['John Doe', 'Jane Smith'],
            'requestor_email': ['john.doe@company.com', 'jane.smith@company.com'],
            'business_justification': ['Production Tableau dashboards', 'Development PowerBI reports'],
            'expiry_days': [90, 60]
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
                        
                        # Create in Snowflake if connected
                        if st.session_state.snowflake_connected:
                            if st.session_state.sf_manager.create_service_account(row['username'], public_key, row['role']):
                                account_data['created_in_snowflake'] = True
                        
                        bulk_accounts.append(account_data)
                        st.session_state.accounts_created.extend(bulk_accounts)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ All accounts created!")
                    
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
                st.metric("Success Rate", f"{(snowflake_accounts/total_accounts*100):.1f}%")
            
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
                    'Snowflake Status': '✅ Created' if acc['created_in_snowflake'] else '⏳ Pending'
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
        
        st.write("**Cleanup Actions:**")
        if st.button("🗑️ Clear All Session Data", type="secondary"):
            if st.checkbox("I confirm I want to clear all data"):
                st.session_state.accounts_created = []
                st.session_state.snowflake_connected = False
                st.success("✅ Session data cleared")

if __name__ == "__main__":
    main()