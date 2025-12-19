import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Types
export interface Pais {
  id: string;
  nombre: string;
  codigo: string;
  bandera: string;
  ligas: Liga[];
}

export interface Liga {
  id: string;
  nombre: string;
  paisId: string;
  logo: string;
  temporadas: Temporada[];
  estadisticas: EstadisticasLiga;
}

export interface Temporada {
  id: string;
  nombre: string;
  ligaId: string;
  fechaInicio: string;
  fechaFin: string;
  partidos: Partido[];
  estadisticas: EstadisticasTemporada;
}

export interface Partido {
  id: string;
  temporadaId: string;
  equipoLocal: string;
  equipoVisitante: string;
  golesLocal: number;
  golesVisitante: number;
  fecha: string;
  jornada: number;
  estadio: string;
}

export interface EstadisticasLiga {
  totalTemporadas: number;
  totalPartidos: number;
  promedioGolesPorPartido: number;
  equipoMasVictorias: string;
}

export interface EstadisticasTemporada {
  totalPartidos: number;
  totalGoles: number;
  promedioGolesPorPartido: number;
  partidoMasGoles: Partido | null;
}

export interface FiltrosPartidos {
  equipo?: string;
  fechaDesde?: string;
  fechaHasta?: string;
  jornada?: number;
}

// Context State Interface
interface LigasContextState {
  // Data
  paises: Pais[];
  paisSeleccionado: Pais | null;
  ligaSeleccionada: Liga | null;
  temporadaSeleccionada: Temporada | null;
  
  // Loading states
  cargandoPaises: boolean;
  cargandoLigas: boolean;
  cargandoTemporadas: boolean;
  cargandoPartidos: boolean;
  
  // Error states
  errorPaises: string | null;
  errorLigas: string | null;
  errorTemporadas: string | null;
  errorPartidos: string | null;
  
  // Filters
  filtrosPartidos: FiltrosPartidos;
  
  // Actions
  cargarPaises: () => Promise<void>;
  seleccionarPais: (pais: Pais) => void;
  seleccionarLiga: (liga: Liga) => void;
  seleccionarTemporada: (temporada: Temporada) => void;
  actualizarFiltrosPartidos: (filtros: Partial<FiltrosPartidos>) => void;
  limpiarSelecciones: () => void;
  obtenerPartidosFiltrados: () => Partido[];
  obtenerEstadisticasLiga: (ligaId: string) => EstadisticasLiga | null;
  obtenerEstadisticasTemporada: (temporadaId: string) => EstadisticasTemporada | null;
}

// Mock data generator
const generarDatosMock = (): Pais[] => {
  const equiposEspana = ['Real Madrid', 'Barcelona', 'Atlético Madrid', 'Sevilla', 'Valencia', 'Real Sociedad'];
  const equiposInglaterra = ['Manchester City', 'Liverpool', 'Chelsea', 'Arsenal', 'Manchester United', 'Tottenham'];
  const equiposItalia = ['Juventus', 'Inter Milan', 'AC Milan', 'Napoli', 'Roma', 'Lazio'];

  const generarPartidos = (equipos: string[], temporadaId: string): Partido[] => {
    const partidos: Partido[] = [];
    let partidoId = 1;
    
    for (let jornada = 1; jornada <= 10; jornada++) {
      for (let i = 0; i < equipos.length; i += 2) {
        if (i + 1 < equipos.length) {
          partidos.push({
            id: `${temporadaId}-partido-${partidoId}`,
            temporadaId,
            equipoLocal: equipos[i],
            equipoVisitante: equipos[i + 1],
            golesLocal: Math.floor(Math.random() * 4),
            golesVisitante: Math.floor(Math.random() * 4),
            fecha: new Date(2023, 8, jornada * 7).toISOString().split('T')[0],
            jornada,
            estadio: `Estadio ${equipos[i]}`
          });
          partidoId++;
        }
      }
    }
    
    return partidos;
  };

  const calcularEstadisticasTemporada = (partidos: Partido[]): EstadisticasTemporada => {
    const totalGoles = partidos.reduce((sum, p) => sum + p.golesLocal + p.golesVisitante, 0);
    const partidoMasGoles = partidos.reduce((max, p) => {
      const golesPartido = p.golesLocal + p.golesVisitante;
      const golesMax = max ? max.golesLocal + max.golesVisitante : 0;
      return golesPartido > golesMax ? p : max;
    }, partidos[0] || null);

    return {
      totalPartidos: partidos.length,
      totalGoles,
      promedioGolesPorPartido: partidos.length > 0 ? totalGoles / partidos.length : 0,
      partidoMasGoles
    };
  };

  const calcularEstadisticasLiga = (temporadas: Temporada[]): EstadisticasLiga => {
    const todosPartidos = temporadas.flatMap(t => t.partidos);
    const totalGoles = todosPartidos.reduce((sum, p) => sum + p.golesLocal + p.golesVisitante, 0);
    
    return {
      totalTemporadas: temporadas.length,
      totalPartidos: todosPartidos.length,
      promedioGolesPorPartido: todosPartidos.length > 0 ? totalGoles / todosPartidos.length : 0,
      equipoMasVictorias: 'Real Madrid'
    };
  };

  return [
    {
      id: 'espana',
      nombre: 'España',
      codigo: 'ES',
      bandera: '🇪🇸',
      ligas: [
        {
          id: 'laliga',
          nombre: 'La Liga',
          paisId: 'espana',
          logo: '⚽',
          temporadas: [
            {
              id: 'laliga-2023',
              nombre: '2023-24',
              ligaId: 'laliga',
              fechaInicio: '2023-08-01',
              fechaFin: '2024-05-31',
              partidos: generarPartidos(equiposEspana, 'laliga-2023'),
              estadisticas: {} as EstadisticasTemporada
            },
            {
              id: 'laliga-2022',
              nombre: '2022-23',
              ligaId: 'laliga',
              fechaInicio: '2022-08-01',
              fechaFin: '2023-05-31',
              partidos: generarPartidos(equiposEspana, 'laliga-2022'),
              estadisticas: {} as EstadisticasTemporada
            }
          ],
          estadisticas: {} as EstadisticasLiga
        }
      ]
    },
    {
      id: 'inglaterra',
      nombre: 'Inglaterra',
      codigo: 'GB',
      bandera: '🇬🇧',
      ligas: [
        {
          id: 'premier',
          nombre: 'Premier League',
          paisId: 'inglaterra',
          logo: '⚽',
          temporadas: [
            {
              id: 'premier-2023',
              nombre: '2023-24',
              ligaId: 'premier',
              fechaInicio: '2023-08-01',
              fechaFin: '2024-05-31',
              partidos: generarPartidos(equiposInglaterra, 'premier-2023'),
              estadisticas: {} as EstadisticasTemporada
            }
          ],
          estadisticas: {} as EstadisticasLiga
        }
      ]
    },
    {
      id: 'italia',
      nombre: 'Italia',
      codigo: 'IT',
      bandera: '🇮🇹',
      ligas: [
        {
          id: 'seriea',
          nombre: 'Serie A',
          paisId: 'italia',
          logo: '⚽',
          temporadas: [
            {
              id: 'seriea-2023',
              nombre: '2023-24',
              ligaId: 'seriea',
              fechaInicio: '2023-08-01',
              fechaFin: '2024-05-31',
              partidos: generarPartidos(equiposItalia, 'seriea-2023'),
              estadisticas: {} as EstadisticasTemporada
            }
          ],
          estadisticas: {} as EstadisticasLiga
        }
      ]
    }
  ];
};

// Create Context
const LigasContext = createContext<LigasContextState | undefined>(undefined);

// Provider Props
interface LigasProviderProps {
  children: ReactNode;
}

// Provider Component
export const LigasProvider: React.FC<LigasProviderProps> = ({ children }) => {
  // State
  const [paises, setPaises] = useState<Pais[]>([]);
  const [paisSeleccionado, setPaisSeleccionado] = useState<Pais | null>(null);
  const [ligaSeleccionada, setLigaSeleccionada] = useState<Liga | null>(null);
  const [temporadaSeleccionada, setTemporadaSeleccionada] = useState<Temporada | null>(null);
  
  // Loading states
  const [cargandoPaises, setCargandoPaises] = useState(false);
  const [cargandoLigas, setCargandoLigas] = useState(false);
  const [cargandoTemporadas, setCargandoTemporadas] = useState(false);
  const [cargandoPartidos, setCargandoPartidos] = useState(false);
  
  // Error states
  const [errorPaises, setErrorPaises] = useState<string | null>(null);
  const [errorLigas, setErrorLigas] = useState<string | null>(null);
  const [errorTemporadas, setErrorTemporadas] = useState<string | null>(null);
  const [errorPartidos, setErrorPartidos] = useState<string | null>(null);
  
  // Filters
  const [filtrosPartidos, setFiltrosPartidos] = useState<FiltrosPartidos>({});

  // Actions
  const cargarPaises = useCallback(async (): Promise<void> => {
    setCargandoPaises(true);
    setErrorPaises(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const datosMock = generarDatosMock();
      
      // Calculate statistics for all leagues and seasons
      const paisesConEstadisticas = datosMock.map(pais => ({
        ...pais,
        ligas: pais.ligas.map(liga => {
          const temporadasConEstadisticas = liga.temporadas.map(temporada => ({
            ...temporada,
            estadisticas: calcularEstadisticasTemporada(temporada.partidos)
          }));
          
          return {
            ...liga,
            temporadas: temporadasConEstadisticas,
            estadisticas: calcularEstadisticasLiga(temporadasConEstadisticas)
          };
        })
      }));
      
      setPaises(paisesConEstadisticas);
    } catch (error) {
      setErrorPaises('Error al cargar los países');
      console.error('Error loading countries:', error);
    } finally {
      setCargandoPaises(false);
    }
  }, []);

  const calcularEstadisticasTemporada = (partidos: Partido[]): EstadisticasTemporada => {
    const totalGoles = partidos.reduce((sum, p) => sum + p.golesLocal + p.golesVisitante, 0);
    const partidoMasGoles = partidos.reduce((max, p) => {
      const golesPartido = p.golesLocal + p.golesVisitante;
      const golesMax = max ? max.golesLocal + max.golesVisitante : 0;
      return golesPartido > golesMax ? p : max;
    }, partidos[0] || null);

    return {
      totalPartidos: partidos.length,
      totalGoles,
      promedioGolesPorPartido: partidos.length > 0 ? Number((totalGoles / partidos.length).toFixed(2)) : 0,
      partidoMasGoles
    };
  };

  const calcularEstadisticasLiga = (temporadas: Temporada[]): EstadisticasLiga => {
    const todosPartidos = temporadas.flatMap(t => t.partidos);
    const totalGoles = todosPartidos.reduce((sum, p) => sum + p.golesLocal + p.golesVisitante, 0);
    
    return {
      totalTemporadas: temporadas.length,
      totalPartidos: todosPartidos.length,
      promedioGolesPorPartido: todosPartidos.length > 0 ? Number((totalGoles / todosPartidos.length).toFixed(2)) : 0,
      equipoMasVictorias: 'Real Madrid'
    };
  };

  const seleccionarPais = useCallback((pais: Pais): void => {
    setPaisSeleccionado(pais);
    setLigaSeleccionada(null);
    setTemporadaSeleccionada(null);
    setFiltrosPartidos({});
  }, []);

  const seleccionarLiga = useCallback((liga: Liga): void => {
    setLigaSeleccionada(liga);
    setTemporadaSeleccionada(null);
    setFiltrosPartidos({});
  }, []);

  const seleccionarTemporada = useCallback((temporada: Temporada): void => {
    setTemporadaSeleccionada(temporada);
    setFiltrosPartidos({});
  }, []);

  const actualizarFiltrosPartidos = useCallback((filtros: Partial<FiltrosPartidos>): void => {
    setFiltrosPartidos(prev => ({ ...prev, ...filtros }));
  }, []);

  const limpiarSelecciones = useCallback((): void => {
    setPaisSeleccionado(null);
    setLigaSeleccionada(null);
    setTemporadaSeleccionada(null);
    setFiltrosPartidos({});
  }, []);

  const obtenerPartidosFiltrados = useCallback((): Partido[] => {
    if (!temporadaSeleccionada) return [];
    
    let partidos = temporadaSeleccionada.partidos;
    
    if (filtrosPartidos.equipo) {
      partidos = partidos.filter(p => 
        p.equipoLocal.toLowerCase().includes(filtrosPartidos.equipo!.toLowerCase()) ||
        p.equipoVisitante.toLowerCase().includes(filtrosPartidos.equipo!.toLowerCase())
      );
    }
    
    if (filtrosPartidos.fechaDesde) {
      partidos = partidos.filter(p => p.fecha >= filtrosPartidos.fechaDesde!);
    }
    
    if (filtrosPartidos.fechaHasta) {
      partidos = partidos.filter(p => p.fecha <= filtrosPartidos.fechaHasta!);
    }
    
    if (filtrosPartidos.jornada) {
      partidos = partidos.filter(p => p.jornada === filtrosPartidos.jornada);
    }
    
    return partidos;
  }, [temporadaSeleccionada, filtrosPartidos]);

  const obtenerEstadisticasLiga = useCallback((ligaId: string): EstadisticasLiga | null => {
    for (const pais of paises) {
      const liga = pais.ligas.find(l => l.id === ligaId);
      if (liga) return liga.estadisticas;
    }
    return null;
  }, [paises]);

  const obtenerEstadisticasTemporada = useCallback((temporadaId: string): EstadisticasTemporada | null => {
    for (const pais of paises) {
      for (const liga of pais.ligas) {
        const temporada = liga.temporadas.find(t => t.id === temporadaId);
        if (temporada) return temporada.estadisticas;
      }
    }
    return null;
  }, [paises]);

  // Context value
  const contextValue: LigasContextState = {
    // Data
    paises,
    paisSeleccionado,
    ligaSeleccionada,
    temporadaSeleccionada,
    
    // Loading states
    cargandoPaises,
    cargandoLigas,
    cargandoTemporadas,
    cargandoPartidos,
    
    // Error states
    errorPaises,
    errorLigas,
    errorTemporadas,
    errorPartidos,
    
    // Filters
    filtrosPartidos,
    
    // Actions
    cargarPaises,
    seleccionarPais,
    seleccionarLiga,
    seleccionarTemporada,
    actualizarFiltrosPartidos,
    limpiarSelecciones,
    obtenerPartidosFiltrados,
    obtenerEstadisticasLiga,
    obtenerEstadisticasTemporada
  };

  return (
    <LigasContext.Provider value={contextValue}>
      {children}
    </LigasContext.Provider>
  );
};

// Custom hook to use the context
export const useLigas = (): LigasContextState => {
  const context = useContext(LigasContext);
  if (context === undefined) {
    throw new Error('useLigas debe ser usado dentro de un LigasProvider');
  }
  return context;
};

// Export default
export default LigasProvider;