# POLLOS ANA — Entrega hasta Sprint 2

Proyecto académico Django. **Sprint 1:** autenticación, dashboard, categorías y productos. **Sprint 2:** POS, ventas, pedidos y cocina.

## Instalación (Windows 11, PowerShell)
1. Instalar Python 3.11 o superior y abrir esta carpeta en VS Code.
2. Ejecutar:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
3. Abrir http://127.0.0.1:8000/ e iniciar sesión con el superusuario.
4. Crear categorías y productos, luego registrar una venta en POS y consultar Cocina.

Si PowerShell bloquea la activación, ejecutar `.venv\Scripts\python.exe` en lugar de `python` en cada comando y `.venv\Scripts\pip.exe` para instalar.

## Demostración
- Sprint 1: login, dashboard, nueva categoría, nuevo producto y edición.
- Sprint 2: agregar productos al carrito, registrar venta, consultar historial y avanzar estados en cocina.

## Límites actuales
- Base SQLite local para la primera entrega; MySQL se configurará después.
- No hay control de inventario, descuento de recetas, caja, delivery avanzado ni gráficos reales.
- No se debe desplegar en producción con DEBUG activo ni SECRET_KEY de desarrollo.
- Requiere acceso a internet para cargar Bootstrap desde CDN.
- El superusuario gestiona productos; las cuentas normales pueden acceder a POS y cocina. Los permisos detallados por rol se implementarán más adelante.
