from supabase import create_client, Client
from config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Configurar para usar pg8000 en lugar de psycopg2
os.environ['SUPABASE_USE_PG8000'] = 'true'

class SupabaseManager:
    _instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            try:
                # Forzar uso de pg8000
                import supabase.lib.client_options
                options = supabase.lib.client_options.ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10,
                )
                
                cls._instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY,
                    options=options
                )
                logger.info("✅ Cliente Supabase inicializado (usando pg8000)")
            except Exception as e:
                logger.error(f"❌ Error inicializando Supabase: {e}")
                raise
        return cls._instance
    
    @classmethod
    def test_connection(cls):
        """Probar conexión a Supabase"""
        try:
            client = cls.get_client()
            # Prueba simple
            result = client.table("leagues").select("*", count="exact").limit(1).execute()
            logger.info(f"✅ Conexión a Supabase: OK")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a Supabase: {e}")
            return False

def get_supabase() -> Client:
    return SupabaseManager.get_client()