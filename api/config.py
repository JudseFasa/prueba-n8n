import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("https://mvsnymlcqutxnmnfxdgt.supabase.co")
    SUPABASE_KEY = os.getenv("sb_secret_Wo7RzDpb1DZitr-_1Dy8PA_LDq0SoME")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY"))
    
    # API
    API_HOST = os.getenv("HOST", "0.0.0.0")
    API_PORT = int(os.getenv("PORT", 10000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Scraper
    SCRAPER_TIMEOUT = 30
    SCRAPER_USER_AGENT = "Mozilla/5.0 (compatible; FootballScraper/1.0)"
    
    # Validaciones
    @classmethod
    def validate(cls):
        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        
        if missing:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
        
        print("✅ Configuración cargada correctamente")
        print(f"   Supabase URL: {cls.SUPABASE_URL[:30]}...")
        print(f"   API Port: {cls.API_PORT}")

settings = Settings()