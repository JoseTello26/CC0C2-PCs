# Usa la imagen base oficial de Hugging Face
FROM huggingface/transformers-pytorch-cpu

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala dependencias adicionales necesarias para tu proyecto

RUN pip install --no-cache-dir fastapi uvicorn datasets

# Copia los archivos de la aplicación al contenedor
COPY . .

# Expone el puerto que usará FastAPI
EXPOSE 8000

# Comando para iniciar la aplicación FastAPI con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
