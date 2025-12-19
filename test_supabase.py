# test_validation.py
import requests
import json
from datetime import datetime

class TestAPI:
    def __init__(self):
        self.base_url = "https://tudominio.n8n.cloud/webhook/query"
        self.api_key = "test_key"  # Debe coincidir con lo que insertaste
        
    def test_successful_validation(self):
        """Prueba validación exitosa"""
        payload = {
            "api_key": self.api_key,
            "query_type": "partido_simple",
            "params": {"local": "Real Madrid", "visitante": "Barcelona"}
        }
        
        response = requests.post(self.base_url, json=payload)
        print("\n=== Prueba 1: Validación Exitosa ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        # Deberías recibir 200 o pasar al siguiente nodo
        return response.status_code in [200, 201]
    
    def test_invalid_api_key(self):
        """Prueba con API key inválida"""
        payload = {
            "api_key": "key_invalida",
            "query_type": "partido_simple",
            "params": {}
        }
        
        response = requests.post(self.base_url, json=payload)
        print("\n=== Prueba 2: API Key Inválida ===")
        print(f"Status: {response.status_code}")  # Debería ser 401
        print(f"Response: {response.text}")
        
        return response.status_code == 401
    
    def test_insufficient_balance(self):
        """Prueba con saldo insuficiente"""
        # Primero crea un cliente con saldo 0 en Supabase
        # INSERT INTO clientes (email, api_key, saldo) VALUES ('sin_saldo@test.com', 'key_sin_saldo', 0.00);
        
        payload = {
            "api_key": "key_sin_saldo",
            "query_type": "equipo_historico",  # Coste: 0.10
            "params": {"equipo": "Real Madrid"}
        }
        
        response = requests.post(self.base_url, json=payload)
        print("\n=== Prueba 3: Saldo Insuficiente ===")
        print(f"Status: {response.status_code}")  # Debería ser 402
        print(f"Response: {response.text}")
        
        return response.status_code == 402

# Ejecutar pruebas
test = TestAPI()
print("🎯 Ejecutando pruebas de validación...")
test.test_successful_validation()
test.test_invalid_api_key()
test.test_insufficient_balance()