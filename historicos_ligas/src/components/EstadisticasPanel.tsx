import React from 'react';
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useLigas } from "@/context/LigasContext";
import { Trophy, Calendar, Users, Target } from "lucide-react";

const EstadisticasPanel: React.FC = () => {
  const { temporadaSeleccionada, partidos } = useLigas();

  if (!temporadaSeleccionada) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-8 text-center">
          <div className="text-gray-500">
            <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg">Selecciona una temporada para ver las estadísticas</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const partidosTemporada = partidos.filter(
    partido => partido.temporada === temporadaSeleccionada.temporada
  );

  const totalPartidos = partidosTemporada.length;
  const partidosJugados = partidosTemporada.filter(p => p.golesLocal !== null && p.golesVisitante !== null).length;
  const partidosPendientes = totalPartidos - partidosJugados;

  const totalGoles = partidosTemporada.reduce((total, partido) => {
    if (partido.golesLocal !== null && partido.golesVisitante !== null) {
      return total + partido.golesLocal + partido.golesVisitante;
    }
    return total;
  }, 0);

  const promedioGolesPorPartido = partidosJugados > 0 ? (totalGoles / partidosJugados).toFixed(2) : '0.00';

  const equiposUnicos = new Set();
  partidosTemporada.forEach(partido => {
    equiposUnicos.add(partido.equipoLocal);
    equiposUnicos.add(partido.equipoVisitante);
  });
  const totalEquipos = equiposUnicos.size;

  const estadisticas = [
    {
      titulo: 'Total de Partidos',
      valor: totalPartidos.toString(),
      icono: Trophy,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      titulo: 'Partidos Jugados',
      valor: partidosJugados.toString(),
      icono: Target,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      titulo: 'Partidos Pendientes',
      valor: partidosPendientes.toString(),
      icono: Calendar,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      titulo: 'Total de Equipos',
      valor: totalEquipos.toString(),
      icono: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-bold text-gray-800">
            Estadísticas de la Temporada {temporadaSeleccionada.temporada}
          </h2>
          <p className="text-gray-600">
            {temporadaSeleccionada.liga} - {temporadaSeleccionada.pais}
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6">
            {/* Estadísticas principales */}
            <div className="grid grid-cols-2 gap-4 w-full max-w-4xl mx-auto">
              {estadisticas.map((stat, index) => {
                const IconComponent = stat.icono;
                return (
                  <div
                    key={index}
                    className={`${stat.bgColor} rounded-lg p-6 border border-gray-200`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">
                          {stat.titulo}
                        </p>
                        <p className={`text-3xl font-bold ${stat.color}`}>
                          {stat.valor}
                        </p>
                      </div>
                      <IconComponent className={`w-8 h-8 ${stat.color}`} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Estadísticas adicionales */}
            <div className="grid gap-4 w-full max-w-2xl mx-auto">
              <Card className="bg-gradient-to-r from-indigo-50 to-blue-50 border-indigo-200">
                <CardContent className="p-6">
                  <div className="text-center">
                    <h3 className="text-lg font-semibold text-indigo-800 mb-2">
                      Total de Goles
                    </h3>
                    <p className="text-4xl font-bold text-indigo-600 mb-2">
                      {totalGoles}
                    </p>
                    <p className="text-sm text-indigo-600">
                      Promedio: {promedioGolesPorPartido} goles por partido
                    </p>
                  </div>
                </CardContent>
              </Card>

              {partidosJugados > 0 && (
                <Card className="bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200">
                  <CardContent className="p-6">
                    <div className="text-center">
                      <h3 className="text-lg font-semibold text-emerald-800 mb-2">
                        Progreso de la Temporada
                      </h3>
                      <div className="w-full bg-emerald-200 rounded-full h-3 mb-3">
                        <div
                          className="bg-emerald-600 h-3 rounded-full transition-all duration-300"
                          style={{
                            width: `${(partidosJugados / totalPartidos) * 100}%`
                          }}
                        ></div>
                      </div>
                      <p className="text-sm text-emerald-600">
                        {((partidosJugados / totalPartidos) * 100).toFixed(1)}% completado
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EstadisticasPanel;