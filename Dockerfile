# Dockerfile para n8n + scraper Flashscore
FROM node:18-bullseye-slim

# 1. Instalar Python y Chrome
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    gnupg \
    curl \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar n8n (versión específica que funciona)
RUN npm install -g n8n@1.43.0

# 3. Crear directorio de trabajo
WORKDIR /app

# 4. Copiar el scraper completo
COPY scraper/ /app/scraper/

# 5. Instalar dependencias Python
RUN pip3 install --no-cache-dir -r /app/scraper/requirements.txt

# 6. Fijar versión específica de webdriver-manager que funciona
RUN pip3 install --no-cache-dir webdriver-manager==3.8.6

# 7. Crear script de inicio CORREGIDO
RUN echo '#!/bin/bash\n\
echo "=========================================="\n\
echo "🚀 Iniciando Sistema n8n + Flashscore Scraper"\n\
echo "=========================================="\n\
\n\
# Configurar ChromeDriver MANUALMENTE (evitar error de formato)\n\
echo "🔧 Configurando ChromeDriver..."\n\
CHROME_VERSION=$(google-chrome --version | awk '\''{print $3}'\'')\n\
echo "Chrome version: $CHROME_VERSION"\n\
MAJOR_VERSION=${CHROME_VERSION%.*}\n\
echo "Major version: $MAJOR_VERSION"\n\
\n\
# Descargar ChromeDriver específico\n\
cd /tmp\n\
wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$MAJOR_VERSION" -O chromedriver_version.txt\n\
CHROMEDRIVER_VERSION=$(cat chromedriver_version.txt)\n\
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"\n\
\n\
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"\n\
unzip -o chromedriver_linux64.zip\n\
chmod +x chromedriver\n\
mv chromedriver /usr/local/bin/\n\
\n\
echo "✅ ChromeDriver instalado correctamente"\n\
\n\
# Crear archivo de configuración para n8n\n\
mkdir -p /root/.n8n\n\
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" > /root/.n8n/config\n\
\n\
# Iniciar n8n CORRECTAMENTE\n\
echo "🌐 Iniciando n8n..."\n\
n8n start --tunnel --host=0.0.0.0 --port=5678 > /var/log/n8n.log 2>&1 &\n\
N8N_PID=$!\n\
\n\
# Esperar a que n8n inicie\n\
sleep 10\n\
\n\
echo "✅ Sistema iniciado correctamente!"\n\
echo "=========================================="\n\
echo "🔗 n8n Web UI: http://localhost:5678"\n\
echo "📁 Scraper path: /app/scraper/flashscore_scraper.py"\n\
echo "🔧 Test scraper: docker exec [container] python3 /app/scraper/n8n_integration.py"\n\
echo "=========================================="\n\
\n\
# Mostrar logs\n\
tail -f /var/log/n8n.log\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 5678

CMD ["/app/start.sh"]