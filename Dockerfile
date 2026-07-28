FROM python:3.13-slim

# Configuramos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos de dependencias
COPY requirements.txt .

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código de nuestra app a la imagen
COPY . .

# Exponemos el puerto 7860 (requerido por Hugging Face Spaces)
EXPOSE 7860

# Damos permisos a la carpeta de la app para que SQLite pueda crear/modificar la BD
RUN chmod -R 777 /app

# Comando para iniciar la aplicación SIN certificados SSL locales (Hugging Face ya pone el SSL)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
