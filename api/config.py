import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mvsnymlcqutxnmnfxdgt.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # Determinar tipo de key
    @property
    def is_service_role_key(self):
        return self.SUPABASE_KEY.startswith("sb_secret_")
    
    @property
    def is_anon_key(self):
        return self.SUPABASE_KEY.startswith("eyJ")
    
    # API
    API_HOST = os.getenv("HOST", "0.0.0.0")
    API_PORT = int(os.getenv("PORT", 10000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Validaciones
    def validate(self):
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        
        if missing:
            logger.warning(f"⚠️ Variables de entorno faltantes: {', '.join(missing)}")
            return False
        
        logger.info("✅ Configuración cargada")
        logger.info(f"   Supabase URL: {self.SUPABASE_URL}")
        logger.info(f"   Tipo de Key: {'Service Role' if self.is_service_role_key else 'Anon Public' if self.is_anon_key else 'Desconocido'}")
        logger.info(f"   Debug: {self.DEBUG}")
        
        return True

settings = Settings()