import React from 'react';
import { useLigas } from '@/context/LigasContext';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Trophy, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Temporada {
  id: string;
  nombre: string;
  anio: string;
  fechaInicio: string;
  fechaFin: string;
  activa: boolean;
  totalPartidos: number;
}

const TemporadasList: React.FC = () => {
  const { 
    ligaSeleccionada, 
    temporadas, 
    temporadaSeleccionada,
    setTemporadaSeleccionada,
    setLigaSeleccionada,
    cargandoTemporadas 
  } = useLigas();

  const handleTemporadaSelect = (temporada: Temporada) => {
    setTemporadaSeleccionada(temporada);
  };

  const handleVolver = () => {
    setLigaSeleccionada(null);
    setTemporadaSeleccionada(null);
  };

  if (!ligaSeleccionada) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Trophy className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">Selecciona una liga para ver las temporadas disponibles</p>
        </div>
      </div>
    );
  }

  if (cargandoTemporadas) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="outline" size="sm" onClick={handleVolver}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver a Ligas
          </Button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{ligaSeleccionada.nombre}</h2>
            <p className="text-gray-600">{ligaSeleccionada.pais}</p>
          </div>
        </div>
        
        <div className="grid gap-4 max-w-4xl mx-auto">
          {[...Array(6)].map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                  <div className="h-10 w-24 bg-gray-200 rounded"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" size="sm" onClick={handleVolver}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver a Ligas
        </Button>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{ligaSeleccionada.nombre}</h2>
          <p className="text-gray-600">{ligaSeleccionada.pais}</p>
        </div>
      </div>

      {/* Temporadas List */}
      {temporadas.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No hay temporadas disponibles</h3>
          <p className="text-gray-500">Esta liga no tiene temporadas registradas en este momento.</p>
        </div>
      ) : (
        <div className="space-y-4 max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Temporadas Disponibles ({temporadas.length})
            </h3>
          </div>
          
          {temporadas.map((temporada) => (
            <Card 
              key={temporada.id}
              className={cn(
                "transition-all duration-200 hover:shadow-md cursor-pointer border-2",
                temporadaSeleccionada?.id === temporada.id 
                  ? "border-blue-500 bg-blue-50" 
                  : "border-gray-200 hover:border-gray-300"
              )}
              onClick={() => handleTemporadaSelect(temporada)}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-xl font-bold text-gray-900">
                        {temporada.nombre}
                      </h4>
                      {temporada.activa && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                          Activa
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-6 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        <span>{temporada.fechaInicio} - {temporada.fechaFin}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Trophy className="h-4 w-4" />
                        <span>{temporada.totalPartidos} partidos</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-2xl font-bold text-gray-900">{temporada.anio}</div>
                    </div>
                    <Button 
                      variant={temporadaSeleccionada?.id === temporada.id ? "default" : "outline"}
                      size="sm"
                    >
                      {temporadaSeleccionada?.id === temporada.id ? "Seleccionada" : "Seleccionar"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      
      {/* Selected Season Info */}
      {temporadaSeleccionada && (
        <Card className="max-w-4xl mx-auto bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader>
            <h3 className="text-lg font-semibold text-blue-900">Temporada Seleccionada</h3>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xl font-bold text-blue-900 mb-1">
                  {temporadaSeleccionada.nombre}
                </h4>
                <p className="text-blue-700">
                  {temporadaSeleccionada.fechaInicio} - {temporadaSeleccionada.fechaFin}
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-900">{temporadaSeleccionada.anio}</div>
                <div className="text-sm text-blue-700">{temporadaSeleccionada.totalPartidos} partidos</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TemporadasList;