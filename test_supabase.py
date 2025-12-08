import os
import requests
from urllib.parse import urlparse

def check_supabase_credentials():
    """Diagnóstico completo de credenciales Supabase"""
    
    print("🔍 DIAGNÓSTICO SUPABASE")
    print("=" * 50)
    
    # 1. Verificar que existan
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print("1. Variables de entorno:")
    print(f"   SUPABASE_URL: {'✅ Seteada' if url else '❌ No set'}")
    print(f"   SUPABASE_KEY: {'✅ Seteada' if key else '❌ No set'}")
    
    if not url or not key:
        return False
    
    # 2. Analizar formato de URL
    print("\n2. Análisis de URL:")
    try:
        parsed = urlparse(url)
        print(f"   Esquema: {parsed.scheme}")
        print(f"   Dominio: {parsed.netloc}")
        print(f"   Ruta: {parsed.path}")
        
        if not parsed.netloc.endswith(".supabase.co"):
            print("   ⚠️  La URL no termina en .supabase.co")
        else:
            print("   ✅ Formato de URL correcto")
    except:
        print("   ❌ URL no válida")
    
    # 3. Analizar formato de KEY
    print("\n3. Análisis de API Key:")
    print(f"   Longitud: {len(key)} caracteres")
    
    # Un JWT típico tiene 3 partes separadas por puntos
    parts = key.split(".")
    if len(parts) == 3:
        print("   ✅ Formato JWT válido (3 partes)")
        
        # Intentar decodificar el payload (parte 2)
        import base64
        import json
        try:
            # Añadir padding si es necesario
            payload_b64 = parts[1]
            payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
            payload_json = base64.b64decode(payload_b64).decode('utf-8')
            payload = json.loads(payload_json)
            
            print(f"   Issuer: {payload.get('iss', 'N/A')}")
            print(f"   Role: {payload.get('role', 'N/A')}")
            print(f"   Exp: {payload.get('exp', 'N/A')}")
        except:
            print("   ⚠️  No se pudo decodificar payload")
    else:
        print("   ❌ Formato JWT no válido (debe tener 3 partes separadas por .)")
    
    # 4. Probar conexión HTTP
    print("\n4. Prueba de conexión HTTP:")
    try:
        # Endpoint simple de Supabase
        test_url = f"{url}/rest/v1/"
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Conexión HTTP exitosa!")
            print(f"   Response: {response.text[:100]}...")
            return True
        elif response.status_code == 401:
            print("   ❌ Error 401: API Key no autorizada")
            print("   Posibles causas:")
            print("   - Key incorrecta/revocada")
            print("   - No es la key 'anon/public'")
            print("   - Proyecto deshabilitado")
        else:
            print(f"   ⚠️  Status inesperado: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ No se puede conectar al servidor")
        print("   Verifica tu conexión a internet")
    except requests.exceptions.Timeout:
        print("   ❌ Timeout - Servidor no responde")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
    
    return False

if __name__ == "__main__":
    # Cargar .env
    from dotenv import load_dotenv
    load_dotenv()
    
    success = check_supabase_credentials()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Tus credenciales son VÁLIDAS!")
        print("   Ya puedes usarlas en Render")
    else:
        print("🔧 PROBLEMAS DETECTADOS")
        print("\nSolución:")
        print("1. Ve a https://app.supabase.com")
        print("2. Selecciona tu proyecto")
        print("3. Settings ⚙️ > API")
        print("4. Copia 'Project URL' como SUPABASE_URL")
        print("5. Copia 'anon public' como SUPABASE_KEY")
        print("6. Asegúrate de que tu proyecto esté activo")