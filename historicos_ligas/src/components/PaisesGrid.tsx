import React from 'react';
import { useLigas } from '@/context/LigasContext';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Globe, Trophy } from 'lucide-react';

interface Pais {
  id: string;
  nombre: string;
  codigo: string;
  bandera: string;
  ligas: Liga[];
}

interface Liga {
  id: string;
  nombre: string;
  logo: string;
  paisId: string;
  temporadas: number;
}

const PaisesGrid: React.FC = () => {
  const { paises, loading, error, seleccionarPais, paisSeleccionado } = useLigas();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-500 mb-2">
            <Globe className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error al cargar países</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!paises || paises.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <Globe className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No hay países disponibles</h3>
          <p className="text-gray-600">No se encontraron países con ligas de fútbol.</p>
        </div>
      </div>
    );
  }

  const handlePaisClick = (pais: Pais) => {
    seleccionarPais(pais.id);
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Países Disponibles</h2>
        <p className="text-gray-600">Selecciona un país para explorar sus ligas de fútbol</p>
      </div>

      <div className="space-y-4 max-w-4xl mx-auto">
        {paises.map((pais) => (
          <Card
            key={pais.id}
            className={cn(
              "cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border-2",
              paisSeleccionado === pais.id
                ? "border-blue-500 bg-blue-50 shadow-md"
                : "border-gray-200 hover:border-blue-300"
            )}
            onClick={() => handlePaisClick(pais)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-gray-200 flex-shrink-0">
                    <img
                      src={pais.bandera}
                      alt={`Bandera de ${pais.nombre}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><rect width="48" height="48" fill="%23f3f4f6"/><text x="24" y="28" text-anchor="middle" font-size="12" fill="%236b7280">${pais.codigo}</text></svg>`;
                      }}
                    />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{pais.nombre}</h3>
                    <p className="text-sm text-gray-500">Código: {pais.codigo}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2 text-blue-600">
                  <Trophy className="h-5 w-5" />
                  <span className="font-semibold">{pais.ligas.length}</span>
                  <span className="text-sm text-gray-600">
                    {pais.ligas.length === 1 ? 'liga' : 'ligas'}
                  </span>
                </div>
              </div>
            </CardHeader>

            <CardContent className="pt-0">
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Ligas disponibles:</h4>
                <div className="space-y-1">
                  {pais.ligas.slice(0, 3).map((liga) => (
                    <div key={liga.id} className="flex items-center space-x-3 p-2 bg-white rounded-lg border border-gray-100">
                      <div className="w-6 h-6 rounded overflow-hidden flex-shrink-0">
                        <img
                          src={liga.logo}
                          alt={`Logo de ${liga.nombre}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><rect width="24" height="24" fill="%23e5e7eb"/><circle cx="12" cy="12" r="8" fill="%23f3f4f6"/></svg>`;
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-700 flex-1">{liga.nombre}</span>
                      <span className="text-xs text-gray-500">
                        {liga.temporadas} {liga.temporadas === 1 ? 'temporada' : 'temporadas'}
                      </span>
                    </div>
                  ))}
                  {pais.ligas.length > 3 && (
                    <div className="text-xs text-gray-500 text-center py-1">
                      y {pais.ligas.length - 3} {pais.ligas.length - 3 === 1 ? 'liga más' : 'ligas más'}...
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default PaisesGrid;