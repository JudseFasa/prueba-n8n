import React, { useState, useMemo } from 'react';
import { useLigas } from '@/context/LigasContext';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Calendar, Trophy, Users, Filter } from 'lucide-react';

interface Partido {
  id: string;
  fecha: string;
  jornada: number;
  fase: string;
  equipoLocal: string;
  equipoVisitante: string;
  golesLocal: number | null;
  golesVisitante: number | null;
  estado: 'programado' | 'en_curso' | 'finalizado' | 'suspendido';
}

const PartidosTable: React.FC = () => {
  const { selectedTemporada } = useLigas();
  const [filtroFase, setFiltroFase] = useState<string>('todas');
  const [filtroJornada, setFiltroJornada] = useState<number | null>(null);
  const [mostrarFiltros, setMostrarFiltros] = useState(false);

  // Mock data for partidos
  const partidos: Partido[] = useMemo(() => [
    {
      id: '1',
      fecha: '2024-01-15T20:00:00Z',
      jornada: 1,
      fase: 'Liga Regular',
      equipoLocal: 'Real Madrid',
      equipoVisitante: 'Barcelona',
      golesLocal: 2,
      golesVisitante: 1,
      estado: 'finalizado'
    },
    {
      id: '2',
      fecha: '2024-01-16T18:30:00Z',
      jornada: 1,
      fase: 'Liga Regular',
      equipoLocal: 'Atlético Madrid',
      equipoVisitante: 'Sevilla',
      golesLocal: 1,
      golesVisitante: 1,
      estado: 'finalizado'
    },
    {
      id: '3',
      fecha: '2024-01-20T21:00:00Z',
      jornada: 2,
      fase: 'Liga Regular',
      equipoLocal: 'Valencia',
      equipoVisitante: 'Real Madrid',
      golesLocal: null,
      golesVisitante: null,
      estado: 'programado'
    },
    {
      id: '4',
      fecha: '2024-02-15T20:45:00Z',
      jornada: 1,
      fase: 'Copa del Rey',
      equipoLocal: 'Barcelona',
      equipoVisitante: 'Athletic Bilbao',
      golesLocal: 3,
      golesVisitante: 0,
      estado: 'finalizado'
    },
    {
      id: '5',
      fecha: '2024-02-20T19:00:00Z',
      jornada: 2,
      fase: 'Copa del Rey',
      equipoLocal: 'Real Sociedad',
      equipoVisitante: 'Villarreal',
      golesLocal: 2,
      golesVisitante: 2,
      estado: 'finalizado'
    }
  ], []);

  const fases = useMemo(() => {
    const fasesUnicas = Array.from(new Set(partidos.map(p => p.fase)));
    return fasesUnicas;
  }, [partidos]);

  const jornadas = useMemo(() => {
    const jornadasUnicas = Array.from(new Set(partidos.map(p => p.jornada))).sort((a, b) => a - b);
    return jornadasUnicas;
  }, [partidos]);

  const partidosFiltrados = useMemo(() => {
    return partidos.filter(partido => {
      const cumpleFase = filtroFase === 'todas' || partido.fase === filtroFase;
      const cumpleJornada = filtroJornada === null || partido.jornada === filtroJornada;
      return cumpleFase && cumpleJornada;
    });
  }, [partidos, filtroFase, filtroJornada]);

  const formatearFecha = (fecha: string) => {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const obtenerColorEstado = (estado: string) => {
    switch (estado) {
      case 'finalizado':
        return 'text-green-600 bg-green-50';
      case 'en_curso':
        return 'text-blue-600 bg-blue-50';
      case 'programado':
        return 'text-gray-600 bg-gray-50';
      case 'suspendido':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const obtenerTextoEstado = (estado: string) => {
    switch (estado) {
      case 'finalizado':
        return 'Finalizado';
      case 'en_curso':
        return 'En Curso';
      case 'programado':
        return 'Programado';
      case 'suspendido':
        return 'Suspendido';
      default:
        return 'Desconocido';
    }
  };

  const limpiarFiltros = () => {
    setFiltroFase('todas');
    setFiltroJornada(null);
  };

  if (!selectedTemporada) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-8 text-center">
          <Trophy className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">
            Selecciona una Temporada
          </h3>
          <p className="text-gray-500">
            Elige una temporada para ver los partidos disponibles
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Partidos</h2>
          <p className="text-gray-600">
            Temporada {selectedTemporada.nombre} - {partidosFiltrados.length} partidos
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setMostrarFiltros(!mostrarFiltros)}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          Filtros
        </Button>
      </div>

      {/* Filtros */}
      {mostrarFiltros && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Filtros</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Filtro por Fase */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fase
                </label>
                <select
                  value={filtroFase}
                  onChange={(e) => setFiltroFase(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="todas">Todas las fases</option>
                  {fases.map(fase => (
                    <option key={fase} value={fase}>{fase}</option>
                  ))}
                </select>
              </div>

              {/* Filtro por Jornada */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Jornada
                </label>
                <select
                  value={filtroJornada || ''}
                  onChange={(e) => setFiltroJornada(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todas las jornadas</option>
                  {jornadas.map(jornada => (
                    <option key={jornada} value={jornada}>Jornada {jornada}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end">
              <Button variant="outline" onClick={limpiarFiltros}>
                Limpiar Filtros
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de Partidos */}
      <Card>
        <CardContent className="p-0">
          {partidosFiltrados.length === 0 ? (
            <div className="p-8 text-center">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">
                No hay partidos
              </h3>
              <p className="text-gray-500">
                No se encontraron partidos con los filtros seleccionados
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fase
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Jornada
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Partido
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Resultado
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {partidosFiltrados.map((partido) => (
                    <tr key={partido.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-900">
                            {formatearFecha(partido.fecha)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">{partido.fase}</span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">{partido.jornada}</span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          <div className="font-medium">{partido.equipoLocal}</div>
                          <div className="text-gray-500">vs {partido.equipoVisitante}</div>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-center">
                        {partido.golesLocal !== null && partido.golesVisitante !== null ? (
                          <span className="text-lg font-bold text-gray-900">
                            {partido.golesLocal} - {partido.golesVisitante}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-center">
                        <span className={cn(
                          "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
                          obtenerColorEstado(partido.estado)
                        )}>
                          {obtenerTextoEstado(partido.estado)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PartidosTable;