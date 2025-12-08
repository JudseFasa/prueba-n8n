from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    _instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            try:
                cls._instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("✅ Cliente Supabase inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Supabase: {e}")
                raise
        return cls._instance
    
    @classmethod
    def test_connection(cls):
        """Probar conexión a Supabase"""
        try:
            client = cls.get_client()
            result = client.table("leagues").select("count", count="exact").limit(1).execute()
            logger.info(f"✅ Conexión a Supabase: OK (count: {result.count})")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a Supabase: {e}")
            return False

# Funciones helper
def get_supabase() -> Client:
    return SupabaseManager.get_client()

def upsert_many(table: str, data: list, on_conflict: str = "id"):
    """Insertar/actualizar múltiples registros"""
    client = get_supabase()
    try:
        result = client.table(table).upsert(data, on_conflict=on_conflict).execute()
        logger.info(f"✅ Upsert en {table}: {len(data)} registros")
        return result
    except Exception as e:
        logger.error(f"❌ Error en upsert {table}: {e}")
        raise

def log_sync(sync_data: dict):
    """Registrar sincronización"""
    client = get_supabase()
    client.table("logs").insert({
        "source": "api_sync",
        "message": "Sincronización completada",
        "extra": sync_data
    }).execute()