import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useLigas } from '@/context/LigasContext';
import { Trophy, Calendar, MapPin } from 'lucide-react';

interface Liga {
  id: string;
  nombre: string;
  pais: string;
  temporadas: number;
  logoUrl?: string;
  descripcion?: string;
  fundacion?: number;
}

interface LigaCardProps {
  liga: Liga;
}

const LigaCard: React.FC<LigaCardProps> = ({ liga }) => {
  const { seleccionarLiga } = useLigas();

  const handleSeleccionar = () => {
    seleccionarLiga(liga.id);
  };

  return (
    <Card className="w-full max-w-sm md:max-w-lg lg:max-w-xl mx-auto hover:shadow-lg transition-shadow duration-300 border border-gray-200 hover:border-blue-300">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          {liga.logoUrl ? (
            <img 
              src={liga.logoUrl} 
              alt={`Logo de ${liga.nombre}`}
              className="w-12 h-12 object-contain rounded-lg"
            />
          ) : (
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <Trophy className="w-6 h-6 text-white" />
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 line-clamp-1">
              {liga.nombre}
            </h3>
            <div className="flex items-center gap-1 text-sm text-gray-600 mt-1">
              <MapPin className="w-4 h-4" />
              <span>{liga.pais}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {liga.descripcion && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
            {liga.descripcion}
          </p>
        )}
        
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Calendar className="w-4 h-4" />
            <span>{liga.temporadas} temporadas</span>
          </div>
          
          {liga.fundacion && (
            <div className="text-sm text-gray-500">
              Fundada en {liga.fundacion}
            </div>
          )}
        </div>
        
        <Button 
          onClick={handleSeleccionar}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
        >
          Ver Temporadas
        </Button>
      </CardContent>
    </Card>
  );
};

export default LigaCard;