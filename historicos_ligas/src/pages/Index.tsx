import { useState } from "react";
import Header from "@/components/Header";
import PaisesGrid from "@/components/PaisesGrid";
import LigaCard from "@/components/LigaCard";
import TemporadasList from "@/components/TemporadasList";
import PartidosTable from "@/components/PartidosTable";
import EstadisticasPanel from "@/components/EstadisticasPanel";
import { useLigas } from "@/context/LigasContext";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

const Index = () => {
  const { selectedLiga, selectedTemporada, setSelectedLiga, setSelectedTemporada } = useLigas();
  const [view, setView] = useState<'paises' | 'liga' | 'temporada' | 'partidos'>('paises');

  const handleLigaSelect = (liga: any) => {
    setSelectedLiga(liga);
    setView('liga');
  };

  const handleTemporadaSelect = (temporada: any) => {
    setSelectedTemporada(temporada);
    setView('temporada');
  };

  const handleViewPartidos = () => {
    setView('partidos');
  };

  const handleBack = () => {
    if (view === 'partidos') {
      setView('temporada');
    } else if (view === 'temporada') {
      setView('liga');
    } else if (view === 'liga') {
      setView('paises');
      setSelectedLiga(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {view !== 'paises' && (
          <Button 
            onClick={handleBack}
            variant="outline" 
            className="mb-6 flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
        )}

        {view === 'paises' && (
          <PaisesGrid onLigaSelect={handleLigaSelect} />
        )}

        {view === 'liga' && selectedLiga && (
          <div className="space-y-6">
            <LigaCard liga={selectedLiga} />
            <TemporadasList 
              ligaId={selectedLiga.id} 
              onTemporadaSelect={handleTemporadaSelect}
            />
          </div>
        )}

        {view === 'temporada' && selectedTemporada && (
          <div className="space-y-6">
            <EstadisticasPanel 
              temporadaId={selectedTemporada.id}
              onViewPartidos={handleViewPartidos}
            />
          </div>
        )}

        {view === 'partidos' && selectedTemporada && (
          <PartidosTable temporadaId={selectedTemporada.id} />
        )}
      </main>
    </div>
  );
};

export default Index;
