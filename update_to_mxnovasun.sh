#!/bin/bash
# update_to_mxnovasun.sh - Actualización completa de dominio

echo "🔄 Actualizando todas las referencias de dominio..."
echo "novasolarmx.com → mxnovasun.com"

# Paso 1: Actualizar variables de entorno en Railway
echo "1. Actualizando variables de entorno..."
railway variables set SITE_URL=https://mxnovasun.com
railway variables set DOMAIN=mxnovasun.com

# Paso 2: Actualizar sitemap.xml
echo "2. Actualizando sitemap.xml..."
if [ -f "static/sitemap.xml" ]; then
    sed -i 's/novasolarmx\.com/mxnovasun.com/g' static/sitemap.xml
    echo "✅ sitemap.xml actualizado"
else
    echo "⚠️ sitemap.xml no encontrado"
fi

# Paso 3: Actualizar robots.txt
echo "3. Actualizando robots.txt..."
if [ -f "static/robots.txt" ]; then
    sed -i 's/novasolarmx\.com/mxnovasun.com/g' static/robots.txt
    echo "✅ robots.txt actualizado"
else
    echo "⚠️ robots.txt no encontrado"
fi

# Paso 4: Actualizar templates HTML
echo "4. Actualizando templates..."
find templates/ -name "*.html" -exec sed -i 's/novasolarmx\.com/mxnovasun.com/g' {} \;
find templates/ -name "*.html" -exec sed -i 's/Nova Solar MX/MX Nova Sun/g' {} \;
echo "✅ Templates actualizados"

# Paso 5: Actualizar configuración Python
echo "5. Actualizando config/settings.py..."
if [ -f "config/settings.py" ]; then
    sed -i "s/novasolarmx\.com/mxnovasun.com/g" config/settings.py
    sed -i "s/'Nova Solar MX'/'MX Nova Sun'/g" config/settings.py
    sed -i "s/Nova Solar MX - /MX Nova Sun - /g" config/settings.py
    echo "✅ config/settings.py actualizado"
else
    echo "⚠️ config/settings.py no encontrado"
fi

# Paso 6: Actualizar app.py si tiene referencias al dominio
echo "6. Actualizando app.py..."
if [ -f "app.py" ]; then
    sed -i 's/novasolarmx\.com/mxnovasun.com/g' app.py
    echo "✅ app.py actualizado"
else
    echo "⚠️ app.py no encontrado"
fi

# Paso 7: Actualizar archivos de documentación
echo "7. Actualizando documentación..."
find . -name "*.md" -exec sed -i 's/novasolarmx\.com/mxnovasun.com/g' {} \;
find . -name "*.md" -exec sed -i 's/Nova Solar MX/MX Nova Sun/g' {} \;

# Paso 8: Verificar cambios
echo "8. Verificando cambios realizados..."
echo "📋 Archivos modificados:"
git status --porcelain

# Paso 9: Commit y deploy
echo "9. ¿Hacer commit y deploy? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "🌐 Migración completa de dominio: novasolarmx.com → mxnovasun.com

✅ DNS configurado correctamente
✅ Variables de entorno actualizadas
✅ Sitemap y robots.txt actualizados
✅ Templates y configuración actualizados
✅ Branding actualizado a MX Nova Sun

Nuevo dominio: https://mxnovasun.com"
    
    git push
    
    echo "10. Forzando redeploy..."
    railway up --detach
    
    echo "✅ ¡Migración completada!"
    echo ""
    echo "🌐 Nuevo sitio: https://mxnovasun.com"
    echo "⏰ Esperar 5-10 minutos para SSL certificate"
    echo "🔍 Verificar funcionamiento en navegador"
else
    echo "📋 Cambios preparados pero no committed."
    echo "Revisa los archivos y haz commit manualmente cuando estés listo."
fi

echo ""
echo "📊 Resumen de cambios:"
echo "• Dominio: novasolarmx.com → mxnovasun.com"
echo "• Branding: Nova Solar MX → MX Nova Sun"
echo "• Email: mxnovasun@outlook.com (ya aligned)"
echo "• SSL: Railway automático"