import requests
import sys

API_URL = "https://prueba-n8n-e4s3.onrender.com/"  # Cambia por tu URL real

def check_endpoint(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=10)
        print(f"🔍 {endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ OK - {response.json().get('message', '')}")
            return True
        else:
            print(f"   ❌ Error: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

print("🚀 Verificando despliegue en Render...")
print("=" * 50)

endpoints = [
    "/",
    "/health",
    "/leagues"
]

success = True
for endpoint in endpoints:
    if not check_endpoint(endpoint):
        success = False

print("=" * 50)
if success:
    print("🎉 ¡API desplegada correctamente en Render!")
    print(f"📚 Documentación: {API_URL}/docs")
else:
    print("⚠️  Hay problemas con el despliegue")
    print("   Revisa los logs en Render Dashboard")