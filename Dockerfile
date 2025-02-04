# Usa una imagen base de Python
FROM python:3.9-slim

# Configurar el directorio de trabajo
WORKDIR /app

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    awscli \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Pulumi
RUN curl -fsSL https://get.pulumi.com | sh && \
    export PATH=$PATH:/root/.pulumi/bin && \
    echo 'export PATH=$PATH:/root/.pulumi/bin' >> /etc/bash.bashrc && \
    echo 'export PATH=$PATH:/root/.pulumi/bin' >> ~/.bashrc

# Crear y asignar permisos a /custom_tmp
RUN mkdir -p /custom_tmp && chmod -R 777 /custom_tmp

# Configurar PATH para Pulumi
ENV PATH="/root/.pulumi/bin:${PATH}"

# Configurar la variable TMPDIR para Pulumi
ENV TMPDIR="/custom_tmp"

# Copiar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ .

# Exponer el puerto 8000
EXPOSE 8000

# Comando de inicio
CMD ["python3", "main.py"]
