import React, { useState } from 'react';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu, X, Trophy, Calendar, MapPin, BarChart3 } from "lucide-react";
import { useIsMobile } from "@/hooks/use-mobile";

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const isMobile = useIsMobile();

  const navigationItems = [
    { label: 'Países', icon: MapPin, href: '#paises' },
    { label: 'Ligas', icon: Trophy, href: '#ligas' },
    { label: 'Temporadas', icon: Calendar, href: '#temporadas' },
    { label: 'Estadísticas', icon: BarChart3, href: '#estadisticas' }
  ];

  const handleNavClick = (href: string) => {
    setIsMenuOpen(false);
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const NavigationMenu = ({ className }: { className?: string }) => (
    <nav className={cn("flex gap-1", className)}>
      {navigationItems.map((item) => {
        const Icon = item.icon;
        return (
          <Button
            key={item.label}
            variant="ghost"
            size="sm"
            onClick={() => handleNavClick(item.href)}
            className="text-white hover:text-green-400 hover:bg-white/10 transition-colors duration-200 flex items-center gap-2"
          >
            <Icon className="h-4 w-4" />
            <span className="hidden sm:inline">{item.label}</span>
          </Button>
        );
      })}
    </nav>
  );

  return (
    <header className="sticky top-0 z-50 w-full border-b border-green-700/20 bg-gradient-to-r from-green-800 via-green-700 to-emerald-700 backdrop-blur supports-[backdrop-filter]:bg-green-800/95 shadow-lg">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between max-w-6xl">
        {/* Logo and Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-white/10 rounded-full backdrop-blur-sm">
            <Trophy className="h-6 w-6 text-white" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold text-white leading-tight">
              Histórico Fútbol
            </h1>
            <p className="text-xs text-green-100 hidden sm:block">
              Ligas y Estadísticas
            </p>
          </div>
        </div>

        {/* Desktop Navigation */}
        {!isMobile && (
          <NavigationMenu className="hidden md:flex" />
        )}

        {/* Mobile Menu */}
        {isMobile && (
          <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-white hover:text-green-400 hover:bg-white/10 md:hidden"
              >
                <Menu className="h-5 w-5" />
                <span className="sr-only">Abrir menú</span>
              </Button>
            </SheetTrigger>
            <SheetContent 
              side="right" 
              className="w-64 bg-gradient-to-b from-green-800 to-green-900 border-green-700"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-2">
                  <Trophy className="h-6 w-6 text-white" />
                  <span className="text-lg font-semibold text-white">
                    Menú
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMenuOpen(false)}
                  className="text-white hover:text-green-400 hover:bg-white/10"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
              
              <nav className="flex flex-col gap-2">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Button
                      key={item.label}
                      variant="ghost"
                      onClick={() => handleNavClick(item.href)}
                      className="justify-start text-white hover:text-green-400 hover:bg-white/10 transition-colors duration-200 h-12"
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {item.label}
                    </Button>
                  );
                })}
              </nav>
            </SheetContent>
          </Sheet>
        )}

        {/* Desktop Menu Button for smaller screens */}
        {!isMobile && (
          <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-white hover:text-green-400 hover:bg-white/10 md:hidden"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent 
              side="right" 
              className="w-64 bg-gradient-to-b from-green-800 to-green-900 border-green-700"
            >
              <NavigationMenu className="flex-col items-start gap-2 mt-8" />
            </SheetContent>
          </Sheet>
        )}
      </div>
    </header>
  );
};

export default Header;