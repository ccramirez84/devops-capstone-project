# Usar una imagen base oficial de Python para una imagen pequeña.
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor.
# Esto hace que todos los comandos posteriores (COPY, RUN, etc.) se ejecuten dentro de /app.
WORKDIR /app

# Copiar el archivo de requisitos e instalar las dependencias.
# Usar --no-cache-dir ayuda a mantener la imagen final lo más pequeña posible.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el paquete 'service' que contiene el código de la aplicación
# desde el host al directorio de trabajo en la imagen.
COPY service/ ./service/

# Cambiar a un usuario no root por motivos de seguridad.
# 1. Crear el usuario 'theia' con UID 1000.
# 2. Cambiar la propiedad de la carpeta /app (y su contenido) al nuevo usuario.
# 3. Cambiar el usuario por defecto del contenedor a 'theia'.
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

# El servicio se ejecutará en el puerto 8080 (configurado en el comando CMD).
# EXPOSE simplemente documenta el puerto que se debe abrir.
EXPOSE 8080

# Definir el comando por defecto (Entrypoint) que se ejecutará cuando se inicie el contenedor.
# Ejecuta Gunicorn, enlazado a todas las interfaces (0.0.0.0) en el puerto 8080,
# usando el módulo 'service' y la aplicación Flask 'app'.
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]
