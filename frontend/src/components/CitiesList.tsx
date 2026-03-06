import { useEffect, useState } from "react";
import { Heart, X, MapPin } from "lucide-react";

interface City {
  id: number;
  name: string;
  country: string;
  favorite: boolean;
}

interface CitiesListProps {
  onCitySelected: (cityId: number) => void;
}

export function CitiesList({ onCitySelected }: CitiesListProps) {
  const [cities, setCities] = useState<City[]>([]);

  const loadCities = () => {
    try {
      const stored = JSON.parse(localStorage.getItem("cities") || "[]");

      // ⭐ Favorites always appear first
      stored.sort((a: City, b: City) => Number(b.favorite) - Number(a.favorite));

      setCities(stored);
    } catch {
      setCities([]);
    }
  };

  useEffect(() => {
    loadCities();

    // ⭐ reload if cities change in localStorage
    window.addEventListener("storage", loadCities);

    return () => {
      window.removeEventListener("storage", loadCities);
    };
  }, []);

  const toggleFavorite = (id: number) => {
    const updated = cities.map((city) =>
      city.id === id ? { ...city, favorite: !city.favorite } : city
    );

    updated.sort((a, b) => Number(b.favorite) - Number(a.favorite));

    localStorage.setItem("cities", JSON.stringify(updated));
    setCities(updated);
  };

  const deleteCity = (id: number) => {
    const updated = cities.filter((city) => city.id !== id);
    localStorage.setItem("cities", JSON.stringify(updated));
    setCities(updated);
  };

  if (cities.length === 0) {
    return (
      <div className="text-sm text-muted mt-4">
        Сохранённых городов пока нет
      </div>
    );
  }

  return (
    <div className="space-y-3 mt-4">

      {cities.map((city) => (
        <div
          key={city.id}
          className="flex items-center justify-between glass rounded-xl px-4 py-3 hover:scale-[1.01] transition"
        >

          {/* CITY BUTTON */}
          <button
            onClick={() => onCitySelected(city.id)}
            className="flex items-center gap-3 text-left"
          >
            <MapPin size={18} className="text-accent" />

            <div className="flex flex-col">
              <span className="font-medium">
                {city.name}
              </span>

              <span className="text-xs text-muted">
                {city.country}
              </span>
            </div>
          </button>


          {/* ACTION BUTTONS */}
          <div className="flex items-center gap-3">

            {/* FAVORITE */}
            <button
              onClick={() => toggleFavorite(city.id)}
              title="Избранное"
              className="hover:scale-110 transition"
            >
              <Heart
                size={18}
                className={
                  city.favorite
                    ? "text-red-500 fill-red-500"
                    : "text-muted"
                }
              />
            </button>

            {/* DELETE */}
            <button
              onClick={() => deleteCity(city.id)}
              title="Удалить город"
              className="hover:scale-110 transition"
            >
              <X size={18} className="text-muted hover:text-red-500" />
            </button>

          </div>
        </div>
      ))}
    </div>
  );
}