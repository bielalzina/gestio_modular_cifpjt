# Historial de Conversación - Proyecto Gestió Modular CIFP Joan Taix

## Fecha: 16 de Marzo, 2026

### 1. Solicitud Inicial del Usuario
El usuario solicitó generar el código base completo para una aplicación web modular orientada a la gestión interna de un centro educativo (CIFP Joan Taix).
**Requisitos clave:**
- Backend: Python/Flask.
- Base de Datos: Google Cloud Firestore (Modo Nativo).
- Despliegue: Docker / Google Cloud Run.
- Frontend: Tailwind CSS con identidad visual corporativa (#492565 y #9578A6).
- Autenticación: Google OAuth 2.0.
- Autorización: RBAC mediante Google Groups (Admin SDK).
- Módulo 1: Registro de Correspondencia (Entrada/Salida) con IDs incrementales automáticos.

---

### 2. Plan de Implementación
Se definió una arquitectura con los siguientes componentes:
- `app.py`: Lógica de rutas y Flask.
- `database.py`: Operaciones CRUD y gestión de contadores atómicos en Firestore.
- `auth.py`: Gestión de sesiones, OAuth y verificación de grupos.
- `templates/`: Plantillas representativas con Tailwind.
- `Dockerfile` / `requirements.txt`: Configuración de entorno.

---

### 3. Código Generado

#### [database.py]
Implementación de `get_next_id` usando `@firestore.transactional` para garantizar que los números de registro sean únicos y correlativos. Funciones para añadir y recuperar los últimos 5 registros.

#### [auth.py]
Implementación de decoradores `@login_required` y `@group_required`. Integración con `google-api-python-client` para consultar la API de Directory de Google Admin SDK.

#### [app.py]
Rutas para `/login`, `/callback`, `/logout` y el módulo `/registre`. Restricción de acceso por dominio (@cifpjoantaix.cat) y por grupo de seguridad.

#### [templates/base.html]
Diseño con Navbar morado oscuro, fuente moderna y área de mensajes flash para notificaciones al usuario.

#### [templates/registre.html]
Formulario interactivo que cambia campos entre "Procedencia" y "Destinatario" dinámicamente según la elección del usuario (Entrada/Salida). Tabla de historial integrada.

---

### 4. Entregables de Configuración
- **Dockerfile**: Imagen base Python 3.11-slim.
- **requirements.txt**: Flask, google-cloud-firestore, google-auth-oauthlib, etc.
- **.env.example**: Plantilla para secretos y variables de entorno.

---

### 5. Resultado Final
Se entregó una base sólida, modular y escalable que cumple con los estándares de seguridad y diseño requeridos por el centro educativo CIFP Joan Taix.
