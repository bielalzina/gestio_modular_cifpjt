import os
import json
from functools import wraps
from flask import session, redirect, url_for, request, abort
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

# Admin SDK setup
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_ADMIN_SDK_SERVICE_ACCOUNT_JSON')
SCOPES = ['https://www.googleapis.com/auth/admin.directory.group.member.readonly']

def get_admin_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return None
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # La API de Directorio requiere impersonar a un usuario administrador del dominio
    admin_email = os.getenv('GOOGLE_ADMIN_EMAIL')
    if admin_email:
        creds = creds.with_subject(admin_email)
        
    return build('admin', 'directory_v1', credentials=creds)

def is_user_in_group(user_email, group_email):
    """
    Checks if a user belongs to a specific Google Group using Admin SDK.
    """
    service = get_admin_service()
    if not service:
        # Fallback if service account not configured (disable in prod)
        return False
        
    try:
        results = service.members().hasMember(groupKey=group_email, memberKey=user_email).execute()
        return results.get('isMember', False)
    except Exception as e:
        print(f"Error checking group membership: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def group_required(group_email):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            
            user_email = session['user'].get('email')
            if not is_user_in_group(user_email, group_email):
                abort(403, description="No teniu permís per accedir a aquest mòdul.")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_google_auth_config():
    return {
        "web": {
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "issuer": "https://accounts.google.com",
            "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo"
        }
    }
