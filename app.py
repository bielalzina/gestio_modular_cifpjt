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
    redirect_uri = url_for('callback', _external=True)
    scope = "openid email profile"
    auth_url = (f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={client_id}&response_type=code&scope={scope}&"
                f"redirect_uri={redirect_uri}&prompt=select_account")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error en la autenticación", 400
    
    # Exchange code for tokens
    config = get_google_auth_config()
    token_url = config['web']['token_uri']
    data = {
        'code': code,
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': url_for('callback', _external=True),
        'grant_type': 'authorization_code'
    }
    
    r = requests.post(token_url, data=data)
    tokens = r.json()
    
    # Get user info
    userinfo_url = config['web']['userinfo_endpoint']
    user_info = requests.get(userinfo_url, headers={'Authorization': f"Bearer {tokens['access_token']}"}).json()
    
    # Domain restriction
    if not user_info.get('email', '').endswith(f'@{DOMAIN}'):
        flash(f"Solo se permiten usuarios del dominio @{DOMAIN}", "error")
        return redirect(url_for('index'))
    
    session['user'] = user_info
    flash(f"Bienvenido, {user_info.get('name')}", "success")
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
        # Collect data from form
        data = {
            'tipo': request.form.get('tipo'),
            'municipio': request.form.get('municipio'),
            'procedencia': request.form.get('procedencia') if request.form.get('tipo') == 'entrada' else None,
            'destinatario': request.form.get('destinatario') if request.form.get('tipo') == 'salida' else None,
            'tipo_documento': request.form.get('tipo_documento'),
            'asunto': request.form.get('asunto'),
            'observaciones': request.form.get('observaciones'),
            'usuario_email': session['user']['email']
        }
        
        try:
            reg_id = add_registre(data)
            flash(f"Registro guardado correctamente con el número {reg_id}", "success")
        except Exception as e:
            flash(f"Error al guardar el registro: {str(e)}", "error")
            
        return redirect(url_for('registre'))
    
    # GET: Show table
    registros = get_recent_registres(5)
    return render_template('registre.html', registros=registros)

if __name__ == '__main__':
    # Use waitress as a production-ready server for local testing if needed
    from waitress import serve
    port = int(os.environ.get("PORT", 8080))
    print(f"Server starting on port {port}...")
    serve(app, host='0.0.0.0', port=port)
