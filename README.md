# EduConnect D1

Prototipo académico desarrollado con Python, Flask y SQLite para demostrar la protección de datos estudiantiles mediante los patrones **Proxy** y **Decorator**.

## Arquitectura organizada

- `app.py`: punto de entrada y creación de la aplicación Flask.
- `controllers/`: controladores HTTP y coordinación de solicitudes.
- `services/`: autenticación, gestión de contraseñas y acceso a estudiantes.
- `repositories/`: persistencia de los datos académicos en SQLite.
- `patterns/`: implementaciones de `StudentProxy` y `EncryptionDecorator`.
- `database.py`: conexión y creación del esquema SQLite.
- `templates/` y `static/`: interfaz web.
- `docs/`: página estática de presentación para GitHub Pages.

## Requisitos y ejecución local

Se recomienda Python 3.10 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000`.

## Cuentas de demostración

- Administrador: `admin` / `Admin123!`
- Estudiante: `carlos` / `Estudiante123!` (si la base de datos entregada conserva la cuenta inicial).

## Archivos locales sensibles

`educonnect.db` y `security/encryption.key` se mantienen localmente para conservar los datos existentes y poder descifrar los registros. **No deben subirse al repositorio público.** El archivo `.gitignore` ya los excluye. No elimines ni regeneres la clave si necesitas leer los datos académicos cifrados que ya existen.

En una instalación nueva, la aplicación crea la base de datos y una clave si no existen.

## GitHub Pages

La carpeta `docs/` contiene una página estática de presentación. Para publicarla: en GitHub entra a **Settings → Pages**, selecciona **Deploy from a branch**, elige `main` y la carpeta `/docs`, y guarda. La página de Pages no ejecuta Flask; el backend requiere un servicio de hosting compatible.
