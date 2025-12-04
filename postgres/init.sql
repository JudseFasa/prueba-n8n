CREATE DATABASE soccer_db;

\c soccer_db;

-- Tablas para el scraper
CREATE TABLE IF NOT EXISTS encuentros (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100) UNIQUE,
    jornada INTEGER,
    fecha DATE,
    equipo_local VARCHAR(200),
    equipo_visitante VARCHAR(200),
    estado VARCHAR(50),
    goles_local INTEGER DEFAULT 0,
    goles_visitante INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS goles (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100),
    equipo VARCHAR(50),
    minuto INTEGER,
    tiempo INTEGER,
    jugador VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scraping_logs (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(100),
    match_urls TEXT,
    encuentros_procesados INTEGER,
    goles_extraidos INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Índices
CREATE INDEX idx_encuentros_fecha ON encuentros(fecha);
CREATE INDEX idx_goles_match_id ON goles(match_id);