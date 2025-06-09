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
from typing import Dict, List, Tuple, Optional
import logging
import getpass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="TAO Service Account Portal",
    page_icon="👤",
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
    .tao-header {
        font-size: 1.8rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .service-account-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .expiring-soon {
        background-color: #fff3cd;
        border-color: #ffeaa7;
    }
    .expired {
        background-color: #f8d7da;
        border-color: #f5c6cb;
    }
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    .status-expiring {
        color: #ffc107;
        font-weight: bold;
    }
    .status-expired {
        color: #dc3545;
        font-weight: bold;
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

# Mock data for testing
MOCK_TAO_DATA = {
    "john.doe": {
        "name": "John Doe",
        "email": "john.doe@company.com",
        "department": "Data Analytics",
        "ad_groups": ["SNOWFLAKE_USERS", "TABLEAU_USERS", "DATA_ANALYSTS"],
        "service_accounts": [
            {
                "username": "svc_tableau_prod_analytics",
                "purpose": "Tableau Production Dashboards",
                "environment": "PROD",
                "snowflake_role": "ANALYTICS_ROLE",
                "created_date": "2024-01-15",
                "key_expiry": "2024-07-15",
                "status": "active",
                "last_rotation": "2024-01-15",
                "has_key": True
            },
            {
                "username": "svc_powerbi_dev_analytics", 
                "purpose": "PowerBI Development Reports",
                "environment": "DEV",
                "snowflake_role": "DEV_ANALYTICS_ROLE",
                "created_date": "2024-02-01",
                "key_expiry": "2024-08-01",
                "status": "active",
                "last_rotation": "2024-02-01",
                "has_key": True
            },
            {
                "username": "svc_python_etl_analytics",
                "purpose": "Python ETL Scripts",
                "environment": "PROD", 
                "snowflake_role": "ETL_ROLE",
                "created_date": "2023-12-01",
                "key_expiry": "2024-06-20",
                "status": "expiring_soon",
                "last_rotation": "2023-12-01",
                "has_key": True
            }
        ]
    },
    "jane.smith": {
        "name": "Jane Smith",
        "email": "jane.smith@company.com", 
        "department": "Business Intelligence",
        "ad_groups": ["SNOWFLAKE_USERS", "POWERBI_USERS", "BI_DEVELOPERS"],
        "service_accounts": [
            {
                "username": "svc_powerbi_prod_bi",
                "purpose": "PowerBI Production Reports",
                "environment": "PROD",
                "snowflake_role": "BI_ROLE",
                "created_date": "2024-03-01",
                "key_expiry": "2024-09-01", 
                "status": "active",
                "last_rotation": "2024-03-01",
                "has_key": True
            },
            {
                "username": "svc_datafactory_etl_bi",
                "purpose": "Azure Data Factory ETL",
                "environment": "PROD",
                "snowflake_role": "ETL_ROLE",
                "created_date": "2023-11-15",
                "key_expiry": "2024-06-10",
                "status": "expiring_soon", 
                "last_rotation": "2023-11-15",
                "has_key": True
            }
        ]
    },
    "test.user": {
        "name": "Test User",
        "email": "test.user@company.com",
        "department": "Platform Team",
        "ad_groups": ["SNOWFLAKE_ADMINS", "PLATFORM_TEAM"],
        "service_accounts": [
            {
                "username": "svc_test_account",
                "purpose": "Testing Platform Features",
                "environment": "TEST",
                "snowflake_role": "PUBLIC",
                "created_date": "2024-06-01",
                "key_expiry": "2024-12-01",
                "status": "active",
                "last_rotation": "2024-06-01", 
                "has_key": False
            }
        ]
    }
}

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
    """Mock Snowflake manager for local testing"""
    
    def __init__(self):
        self.connection = None
        self.is_connected = False
    
    def connect(self, account: str, user: str, password: str, warehouse: str = None, database: str = None):
        """Simulate connection to Snowflake"""
        try:
            if account and user and password:
                self.is_connected = True
                logger.info(f"Mock connection established for {user}@{account}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Mock Snowflake connection error: {str(e)}")
            return False
    
    def update_service_account_key(self, username: str, public_key: str) -> bool:
        """Mock updating service account with new public key"""
        try:
            if not self.is_connected:
                return False
            
            logger.info(f"Mock: Updating service account '{username}' with new public key")
            
            # Simulate key update
            update_sql = f"""
            ALTER USER {username} SET RSA_PUBLIC_KEY = '[CLEANED_PUBLIC_KEY]'
            """
            
            logger.info(f"Mock SQL: {update_sql}")
            return True
            
        except Exception as e:
            logger.error(f"Mock error updating service account: {str(e)}")
            return False

def get_current_user() -> str:
    """Get current user - in production this would use AD authentication"""
    if 'current_user' not in st.session_state:
        # In production, this would come from AD/SSO
        # For testing, allow user selection
        return None
    return st.session_state.current_user

def get_user_service_accounts(username: str) -> List[Dict]:
    """Get service accounts owned by the current TAO"""
    user_data = MOCK_TAO_DATA.get(username, {})
    return user_data.get('service_accounts', [])

def get_user_info(username: str) -> Dict:
    """Get TAO information"""
    return MOCK_TAO_DATA.get(username, {})

def calculate_days_until_expiry(expiry_date: str) -> int:
    """Calculate days until key expiry"""
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        today = datetime.now()
        return (expiry - today).days
    except:
        return 0

def get_status_color(status: str) -> str:
    """Get CSS class for status"""
    if status == "active":
        return "status-active"
    elif status == "expiring_soon":
        return "status-expiring"
    elif status == "expired":
        return "status-expired"
    return ""

def display_service_account_card(account: Dict, index: int):
    """Display a service account card with key management options"""
    days_until_expiry = calculate_days_until_expiry(account['key_expiry'])
    
    # Determine card styling based on expiry
    card_class = "service-account-card"
    if days_until_expiry <= 7:
        card_class += " expired"
        account['status'] = "expired"
    elif days_until_expiry <= 30:
        card_class += " expiring-soon"
        account['status'] = "expiring_soon"
    
    with st.container():
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            st.markdown(f"**{account['username']}**")
            st.write(f"📌 {account['purpose']}")
            st.write(f"🌍 {account['environment']} | 🔐 {account['snowflake_role']}")
        
        with col2:
            st.write(f"**Created:** {account['created_date']}")
            st.write(f"**Key Expires:** {account['key_expiry']}")
            if days_until_expiry <= 0:
                st.markdown(f'<span class="status-expired">🔴 EXPIRED</span>', unsafe_allow_html=True)
            elif days_until_expiry <= 7:
                st.markdown(f'<span class="status-expired">🟠 {days_until_expiry} days left</span>', unsafe_allow_html=True)
            elif days_until_expiry <= 30:
                st.markdown(f'<span class="status-expiring">🟡 {days_until_expiry} days left</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="status-active">🟢 {days_until_expiry} days left</span>', unsafe_allow_html=True)
        
        with col3:
            if account['has_key']:
                if days_until_expiry <= 30:
                    if st.button(f"🔄 Rotate Key", key=f"rotate_{index}"):
                        st.session_state.selected_account = account
                        st.session_state.action = "rotate"
                        st.rerun()
                
                if st.button(f"📥 Download Key", key=f"download_{index}"):
                    st.session_state.selected_account = account
                    st.session_state.action = "download"
                    st.rerun()
            else:
                if st.button(f"🔑 Generate Key", key=f"generate_{index}"):
                    st.session_state.selected_account = account
                    st.session_state.action = "generate"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">👤 TAO Service Account Portal</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_account' not in st.session_state:
        st.session_state.selected_account = None
    if 'action' not in st.session_state:
        st.session_state.action = None
    if 'snowflake_connected' not in st.session_state:
        st.session_state.snowflake_connected = False
    
    # User authentication simulation
    current_user = get_current_user()
    
    if not current_user:
        st.markdown("""
        <div class="info-box">
            <strong>🧪 LOCAL TESTING MODE</strong><br>
            In production, user authentication would be handled by AD/SSO integration.
            Select a test user to simulate the TAO experience.
        </div>
        """, unsafe_allow_html=True)
        
        test_users = list(MOCK_TAO_DATA.keys())
        selected_user = st.selectbox("Select Test User (TAO)", test_users)
        
        if st.button("Login as TAO"):
            st.session_state.current_user = selected_user
            st.rerun()
        return
    
    # Get user information
    user_info = get_user_info(current_user)
    user_accounts = get_user_service_accounts(current_user)
    
    # Sidebar for user info and Snowflake connection
    with st.sidebar:
        st.markdown('<div class="tao-header">👤 TAO Information</div>', unsafe_allow_html=True)
        st.write(f"**Name:** {user_info.get('name', 'Unknown')}")
        st.write(f"**Email:** {user_info.get('email', 'Unknown')}")
        st.write(f"**Department:** {user_info.get('department', 'Unknown')}")
        
        st.write("**AD Groups:**")
        for group in user_info.get('ad_groups', []):
            st.write(f"• {group}")
        
        if st.button("🚪 Logout"):
            st.session_state.current_user = None
            st.session_state.selected_account = None
            st.session_state.action = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Mock Snowflake Connection**")
        st.info("🧪 Testing Mode: Auto-connected")
        st.session_state.snowflake_connected = True
        st.session_state.sf_manager = MockSnowflakeManager()
        st.session_state.sf_manager.is_connected = True
    
    # Main content
    if st.session_state.action and st.session_state.selected_account:
        account = st.session_state.selected_account
        action = st.session_state.action
        
        if action == "generate":
            st.markdown(f'### 🔑 Generate Key Pair for {account["username"]}')
            
            col1, col2 = st.columns(2)
            with col1:
                key_size = st.selectbox("Key Size", [2048, 4096], index=0)
                expiry_days = st.number_input("Key Expiry (days)", min_value=30, max_value=365, value=90)
            
            if st.button("Generate Key Pair", type="primary"):
                try:
                    key_gen = KeyPairGenerator()
                    private_key, public_key = key_gen.generate_key_pair(key_size)
                    
                    # Mock update in Snowflake
                    if st.session_state.sf_manager.update_service_account_key(account['username'], public_key):
                        st.success(f"✅ Key pair generated and updated for {account['username']}!")
                        
                        # Update mock data
                        for user_account in user_accounts:
                            if user_account['username'] == account['username']:
                                user_account['has_key'] = True
                                user_account['last_rotation'] = datetime.now().strftime("%Y-%m-%d")
                                user_account['key_expiry'] = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
                                user_account['status'] = "active"
                        
                        # Download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download Private Key",
                                data=private_key,
                                file_name=f"{account['username']}_private_key.pem",
                                mime="application/x-pem-file"
                            )
                        with col2:
                            st.download_button(
                                label="📥 Download Public Key", 
                                data=public_key,
                                file_name=f"{account['username']}_public_key.pem",
                                mime="application/x-pem-file"
                            )
                    else:
                        st.error("❌ Failed to update key in Snowflake")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        elif action == "rotate":
            st.markdown(f'### 🔄 Rotate Key Pair for {account["username"]}')
            
            days_left = calculate_days_until_expiry(account['key_expiry'])
            
            if days_left <= 0:
                st.error("🔴 This key has EXPIRED and must be rotated immediately!")
            elif days_left <= 7:
                st.warning(f"🟠 This key expires in {days_left} days and should be rotated soon.")
            elif days_left <= 30:
                st.info(f"🟡 This key expires in {days_left} days. Rotation recommended.")
            
            st.write("**Current Key Information:**")
            st.write(f"• Last Rotation: {account['last_rotation']}")
            st.write(f"• Expires: {account['key_expiry']}")
            st.write(f"• Days Remaining: {days_left}")
            
            col1, col2 = st.columns(2)
            with col1:
                key_size = st.selectbox("New Key Size", [2048, 4096], index=0)
                expiry_days = st.number_input("New Key Expiry (days)", min_value=30, max_value=365, value=90)
            
            with col2:
                st.write("**Rotation Process:**")
                st.write("1. Generate new key pair")
                st.write("2. Update Snowflake with new public key")
                st.write("3. Download new private key")
                st.write("4. Update applications with new key")
                st.write("5. Old key remains valid for 24 hours")
            
            if st.button("🔄 Generate New Key Pair", type="primary"):
                try:
                    key_gen = KeyPairGenerator()
                    private_key, public_key = key_gen.generate_key_pair(key_size)
                    
                    # Mock update in Snowflake
                    if st.session_state.sf_manager.update_service_account_key(account['username'], public_key):
                        st.success(f"✅ Key pair rotated successfully for {account['username']}!")
                        st.info("ℹ️ Old key will remain valid for 24 hours to allow for application updates.")
                        
                        # Update mock data
                        for user_account in user_accounts:
                            if user_account['username'] == account['username']:
                                user_account['last_rotation'] = datetime.now().strftime("%Y-%m-%d")
                                user_account['key_expiry'] = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
                                user_account['status'] = "active"
                        
                        # Download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download New Private Key",
                                data=private_key,
                                file_name=f"{account['username']}_private_key_new.pem",
                                mime="application/x-pem-file"
                            )
                        with col2:
                            st.download_button(
                                label="📥 Download New Public Key",
                                data=public_key,
                                file_name=f"{account['username']}_public_key_new.pem",
                                mime="application/x-pem-file"
                            )
                    else:
                        st.error("❌ Failed to rotate key in Snowflake")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        elif action == "download":
            st.markdown(f'### 📥 Download Existing Key for {account["username"]}')
            st.info("In production, this would retrieve the stored private key from the secure database.")
            st.write("**Security Note:** Private keys are encrypted at rest with row-level security.")
            
            # Mock download (in production, retrieve from secure storage)
            mock_private_key = f"""-----BEGIN PRIVATE KEY-----
[MOCK PRIVATE KEY DATA FOR {account['username']}]
This would be the actual encrypted private key retrieved from secure storage
-----END PRIVATE KEY-----"""
            
            st.download_button(
                label="📥 Download Private Key",
                data=mock_private_key,
                file_name=f"{account['username']}_private_key.pem",
                mime="application/x-pem-file"
            )
        
        if st.button("← Back to Service Accounts"):
            st.session_state.selected_account = None
            st.session_state.action = None
            st.rerun()
    
    else:
        # Main dashboard
        st.markdown(f'<div class="tao-header">Service Accounts for {user_info.get("name", "Unknown")}</div>', unsafe_allow_html=True)
        
        if not user_accounts:
            st.info("No service accounts found for your TAO account. Contact the platform team if you need service accounts provisioned.")
            return
        
        # Summary metrics
        total_accounts = len(user_accounts)
        active_accounts = sum(1 for acc in user_accounts if acc['status'] == 'active')
        expiring_accounts = sum(1 for acc in user_accounts if acc['status'] == 'expiring_soon')
        expired_accounts = sum(1 for acc in user_accounts if acc['status'] == 'expired')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Accounts", total_accounts)
        with col2:
            st.metric("Active", active_accounts)
        with col3:
            st.metric("⚠️ Expiring Soon", expiring_accounts)
        with col4:
            st.metric("🔴 Expired", expired_accounts)
        
        # Service accounts list
        st.markdown("### Your Service Accounts")
        
        for index, account in enumerate(user_accounts):
            display_service_account_card(account, index)

if __name__ == "__main__":
    main()