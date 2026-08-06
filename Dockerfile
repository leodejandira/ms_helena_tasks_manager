# Imagem base oficial do Python leve (Alpine/Slim)
FROM python:3.11-slim

# Evita que o Python escreva arquivos .pyc e força stdout sem buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretorio de trabalho no container
WORKDIR /app

# Instala as dependencias do sistema necessarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependencias do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do codigo para o container
COPY . .

# Porta padrao que a aplicacao vai expor
EXPOSE 8000

# Comando para iniciar a API no ambiente de producao/container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]