# 🚗 María Alquileres

Sitio web de alquiler de autos desarrollado con Django. Permite a visitantes consultar autos disponibles, aplicar filtros por fecha, precio, categoría y sucursal, y registrarse para hacer reservas.
Este proyecto fue desarrollado por NewTech.

NewTech devs:
Tomas
Camila
Fermin
Koko

## IMPORTANTE:
Requisitos a tener instalados:

- Python 3.11+
- pip
- Virtualenv (recomendado)
- Git


##  Instalación y ejecución local

```bash
# 1. Clonar el repositorio
git clone git@github.com:Fermin-Arana/proyectoPython.git
cd proyectoPython

# 2. Instalar las dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones
python manage.py migrate

# 4. Crear superusuario (opcional)
python manage.py createsuperuser

# 5. Correr el servidor
python manage.py runserver
