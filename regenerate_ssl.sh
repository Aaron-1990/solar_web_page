#!/bin/bash
echo "🔧 Regenerando certificado SSL para Nova Solar MX..."

# Step 0: Verificar conexión
echo "0. Verificando conexión a Railway..."
railway whoami
railway status

# Step 1: Listar dominios actuales
echo "1. Dominios actuales:"
railway domain list

# Step 2: Remove domain
echo "2. Removiendo dominio novasolarmx.com..."
railway domain remove novasolarmx.com

# Step 3: Wait
echo "3. Esperando 30 segundos..."
sleep 30

# Step 4: Re-add domain
echo "4. Re-agregando dominio..."
railway domain add novasolarmx.com

# Step 5: Set environment variables
echo "5. Configurando variables de entorno..."
railway variables set PREFERRED_URL_SCHEME=https
railway variables set SESSION_COOKIE_SECURE=true
railway variables set SITE_URL=https://novasolarmx.com

# Step 6: Verificar variables
echo "6. Variables configuradas:"
railway variables | grep -E "(SCHEME|SECURE|SITE_URL)"

# Step 7: Deploy
echo "7. Forzando redeploy..."
railway up --detach

echo "✅ Proceso completado!"
echo "⏰ Espera 5-15 minutos para que el certificado se genere."
echo "🔍 Verifica en: https://www.ssllabs.com/ssltest/analyze.html?d=novasolarmx.com"
echo "🌐 Test directo: https://novasolarmx.com"
