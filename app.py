import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from dotenv import load_dotenv
from auth import login_required, group_required, get_google_auth_config
from database import add_registre, get_recent_registres

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_key')

# --- CONFIG ---
REGISTRE_GROUP = "users.registre@cifpjoantaix.cat"
DOMAIN = os.getenv('DOMAIN_ORGANIZATION', 'cifpjoantaix.cat')

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login')
def login():
    # Simple redirect to Google OAuth 2.0 (Simplified for boilerplate)
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    # Priorizar REDIRECT_URI de .env, si no, generarla automáticamente
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI') or url_for('callback', _external=True)
    scope = "openid email profile"
    auth_url = (f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={client_id}&response_type=code&scope={scope}&"
                f"redirect_uri={redirect_uri}&prompt=select_account")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error en l'autenticació", 400
    
    # Exchange code for tokens
    config = get_google_auth_config()
    token_url = config['web']['token_uri']
    data = {
        'code': code,
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI') or url_for('callback', _external=True),
        'grant_type': 'authorization_code'
    }
    
    r = requests.post(token_url, data=data)
    tokens = r.json()
    
    # Get user info
    userinfo_url = config['web']['userinfo_endpoint']
    user_info = requests.get(userinfo_url, headers={'Authorization': f"Bearer {tokens['access_token']}"}).json()
    
    # Domain restriction
    if not user_info.get('email', '').endswith(f'@{DOMAIN}'):
        flash(f"Només es permeten usuaris del domini @{DOMAIN}", "error")
        return redirect(url_for('index'))
    
    session['user'] = user_info
    flash(f"Benvingut/da, {user_info.get('name')}", "success")
    return redirect(url_for('registre'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/registre', methods=['GET', 'POST'])
@login_required
@group_required(REGISTRE_GROUP)
def registre():
    if request.method == 'POST':
        # Recollida de dades segons el nou format de la imatge
        data = {
            'tipo': request.form.get('tipo'),
            'data_manual': request.form.get('data_manual'),
            'municipi': request.form.get('municipi'),
            'agent': request.form.get('agent'), # Remitent o Destinatari segons UI
            'tipo_documento': request.form.get('tipo_documento'),
            'asunto': request.form.get('asunto'),
            'observaciones': request.form.get('observaciones'),
            'usuario_email': session['user']['email']
        }
        
        try:
            reg_id = add_registre(data)
            flash(f"Registre desat correctament amb el número {reg_id}", "success")
        except Exception as e:
            flash(f"Error en desar el registre: {str(e)}", "error")
            
        return redirect(url_for('registre'))
    
    # GET: Mostrar taula
    registros = get_recent_registres(5)
    from datetime import datetime
    now_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('registre.html', registros=registros, now_date=now_date)

if __name__ == '__main__':
    # Use waitress as a production-ready server for local testing if needed
    from waitress import serve
    port = int(os.environ.get("PORT", 8080))
    print(f"Server starting on port {port}...")
    serve(app, host='0.0.0.0', port=port)
