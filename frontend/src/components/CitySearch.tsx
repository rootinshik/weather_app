import { useState } from "react";
import { Search, MapPin } from "lucide-react";
import { useCitySearch } from "../hooks/useCitySearch";
import { useCreateCity } from "../hooks/useCreateCity";
import { useDebounce } from "../hooks/useDebounce";

interface CitySearchProps {
  onCitySelected: (cityId: number) => void;
}

interface CitySearchResult {
  name: string;
  country: string;
  lat: number;
  lon: number;
}

interface SavedCity {
  id: number;
  name: string;
  country: string;
  favorite: boolean;
}

export function CitySearch({ onCitySelected }: CitySearchProps) {
  const [query, setQuery] = useState("");

  // Debounce input
  const debouncedQuery = useDebounce(query, 500);

  const { data: results, isLoading } = useCitySearch(debouncedQuery);

  const createCity = useCreateCity();

  const handleSelectCity = async (city: CitySearchResult) => {
    try {
      const savedCity = await createCity.mutateAsync({
        name: city.name,
        country: city.country,
        lat: city.lat,
        lon: city.lon,
      });

      // Load saved cities
      const stored: SavedCity[] = JSON.parse(
        localStorage.getItem("cities") || "[]"
      );

      // Prevent duplicates
      const exists = stored.find((c) => c.id === savedCity.id);

      if (!exists) {
        const newCity: SavedCity = {
          id: savedCity.id,
          name: savedCity.name,
          country: savedCity.country,
          favorite: false,
        };

        stored.push(newCity);
        localStorage.setItem("cities", JSON.stringify(stored));
      }

      // Notify parent component
      onCitySelected(savedCity.id);

      // Clear search
      setQuery("");
    } catch (error) {
      console.error("Ошибка при добавлении города:", error);
    }
  };

  return (
    <div className="relative">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Поиск города..."
          className="w-full pl-12 pr-4 py-3 glass rounded-xl outline-none focus:ring-2 focus:ring-accent"
        />
      </div>

      {/* Dropdown results */}
      {query.length > 1 && (
        <div className="absolute w-full mt-2 glass rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-sm text-muted">Поиск...</div>
          ) : results && results.length > 0 ? (
            results.map((city: CitySearchResult, index: number) => (
              <button
                key={`${city.name}-${city.country}-${index}`}
                onClick={() => handleSelectCity(city)}
                className="block w-full text-left px-4 py-3 hover:bg-accent/10 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <MapPin size={16} className="text-accent" />
                  <span>
                    {city.name}, {city.country}
                  </span>
                </div>
              </button>
            ))
          ) : (
            <div className="p-4 text-sm text-muted">Не найдено</div>
          )}
        </div>
      )}
    </div>
  );
}