import { useState } from "react";
import { Cloud } from "lucide-react";

import { ForecastList } from "./components/ForecastList";
import { ThemeToggle } from "./components/ThemeToggle";
import { CitySearch } from "./components/CitySearch";
import { CitiesList } from "./components/CitiesList";
import { CurrentWeather } from "./components/CurrentWeather";
import { ClothingRecommendation } from "./components/ClothingRecommendation";
import { TemperatureGraph } from "./components/TemperatureGraph";

import { useCurrentWeather } from "./hooks/useCurrentWeather";
import { useForecast } from "./hooks/useForecast";
import { useHourlyChart } from "./hooks/useHourlyChart";
import { useDailyChart } from "./hooks/useDailyChart";
import { useClothingRecommendation } from "./hooks/useClothingRecommendation";

import { UnitToggle } from "./components/UnitToggle";


function App() {

  const [selectedCityId, setSelectedCityId] = useState<number | null>(null);

  // ================= WEATHER DATA =================

  const {
    data: currentWeather,
    isLoading: loadingCurrent,
    isError: errorCurrent,
  } = useCurrentWeather(selectedCityId ?? 0);

  const {
    data: forecast,
    isLoading: loadingForecast,
    isError: errorForecast,
  } = useForecast(selectedCityId ?? 0, 3);

  const {
    data: hourlyData,
    isLoading: loadingHourly,
    isError: errorHourly,
  } = useHourlyChart(selectedCityId ?? 0);

  const {
    data: dailyData,
    isLoading: loadingDaily,
    isError: errorDaily,
  } = useDailyChart(selectedCityId ?? 0);

  const {
    data: recommendation,
    isLoading: loadingRecommendation,
    isError: errorRecommendation,
  } = useClothingRecommendation(selectedCityId ?? 0);


  return (
    <div className="min-h-screen px-6 py-10 max-w-6xl mx-auto">

      {/* ================= HEADER ================= */}
      <header className="flex justify-between items-center mb-10">

        <div className="flex items-center gap-3">
          <Cloud className="w-8 h-8 text-accent" />
          <h1 className="text-3xl font-bold">WEAtrack</h1>
        </div>

        <div className="flex items-center gap-4">
          <UnitToggle />
          <ThemeToggle />
        </div>

      </header>


      {/* ================= SEARCH ================= */}

      <div className="mb-6 max-w-xl">
        <CitySearch onCitySelected={setSelectedCityId} />
      </div>


      {/* ================= SAVED CITIES LIST ================= */}

      <div className="mb-10 max-w-xl">
        <CitiesList onCitySelected={setSelectedCityId} />
      </div>


      {/* ================= EMPTY STATE ================= */}

      {!selectedCityId && (
        <div className="text-center text-gray-500 mt-20">
          <p>Выберите город для отображения погоды</p>
        </div>
      )}


      {/* ================= DATA SECTION ================= */}

      {selectedCityId && (
        <div className="space-y-10">


          {/* CURRENT WEATHER */}

          <section>
            <h2 className="text-xl font-semibold mb-4">
              Текущая погода
            </h2>

            <CurrentWeather
              data={currentWeather}
              isLoading={loadingCurrent}
              isError={errorCurrent}
            />
          </section>


          {/* CLOTHING RECOMMENDATION */}

          <section>
            <h2 className="text-xl font-semibold mb-4">
              Рекомендации по одежде
            </h2>

            {errorRecommendation ? (
              <div className="glass p-4 rounded-xl border border-red-500">
                <p className="text-red-500">
                  Не удалось загрузить рекомендации
                </p>
              </div>
            ) : (
              <ClothingRecommendation
                data={recommendation}
                isLoading={loadingRecommendation}
              />
            )}
          </section>


          {/* TEMPERATURE GRAPH */}

          <section>
            <h2 className="text-xl font-semibold mb-4">
              Температурный тренд
            </h2>

            {errorHourly || errorDaily ? (
              <div className="glass p-4 rounded-xl border border-red-500">
                <p className="text-red-500">
                  Не удалось загрузить данные графика
                </p>
              </div>
            ) : (
              <TemperatureGraph
                hourlyData={hourlyData}
                dailyData={dailyData}
                isLoading={loadingHourly || loadingDaily}
              />
            )}
          </section>


          {/* FORECAST */}

          <section>
            <h2 className="text-xl font-semibold mb-4">
              Прогноз на 3 дня
            </h2>

            {errorForecast ? (
              <div className="glass p-4 rounded-xl border border-red-500">
                <p className="text-red-500">
                  Не удалось загрузить прогноз
                </p>
              </div>
            ) : (
              <ForecastList
                data={forecast}
                isLoading={loadingForecast}
              />
            )}
          </section>

        </div>
      )}

    </div>
  );
}

export default App;