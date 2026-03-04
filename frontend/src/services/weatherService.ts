export interface WeatherData {
  current: {
    temperature: number;
    weatherCode: number;
    windSpeed: number;
    humidity: number;
    feelsLike: number;
    pressure: number;
  };
  hourly: {
    time: string[];
    temperature: number[];
    weatherCode: number[];
  };
  daily: {
    time: string[];
    tempMax: number[];
    tempMin: number[];
    weatherCode: number[];
  };
}

export interface CityLocation {
  name: string;
  latitude: number;
  longitude: number;
  country: string;
  state?: string;
}

// RUSSIAN WEATHER DESCRIPTIONS
export const getWeatherCodeInfo = (code: number) => {
  const weatherCodes: Record<number, { icon: string; description: string }> = {
    0: { icon: '☀️', description: 'Ясно' },
    1: { icon: '🌤️', description: 'Преимущественно ясно' },
    2: { icon: '⛅', description: 'Переменная облачность' },
    3: { icon: '☁️', description: 'Пасмурно' },
    45: { icon: '🌫️', description: 'Туман' },
    48: { icon: '🌫️', description: 'Изморозь' },
    51: { icon: '🌦️', description: 'Лёгкая морось' },
    53: { icon: '🌦️', description: 'Умеренная морось' },
    55: { icon: '🌧️', description: 'Сильная морось' },
    61: { icon: '🌧️', description: 'Слабый дождь' },
    63: { icon: '🌧️', description: 'Умеренный дождь' },
    65: { icon: '🌧️', description: 'Сильный дождь' },
    71: { icon: '🌨️', description: 'Слабый снег' },
    73: { icon: '🌨️', description: 'Умеренный снег' },
    75: { icon: '🌨️', description: 'Сильный снег' },
    77: { icon: '🌨️', description: 'Снежная крупа' },
    80: { icon: '🌦️', description: 'Слабые ливни' },
    81: { icon: '🌧️', description: 'Умеренные ливни' },
    82: { icon: '⛈️', description: 'Сильные ливни' },
    85: { icon: '🌨️', description: 'Слабые снегопады' },
    86: { icon: '🌨️', description: 'Сильные снегопады' },
    95: { icon: '⛈️', description: 'Гроза' },
    96: { icon: '⛈️', description: 'Гроза с градом' },
    99: { icon: '⛈️', description: 'Сильная гроза с градом' },
  };

  return weatherCodes[code] || { icon: '🌤️', description: 'Неизвестно' };
};

// English search for user input
export const searchCities = async (query: string): Promise<CityLocation[]> => {
  const response = await fetch(
    `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=en&format=json`
  );

  if (!response.ok) {
    throw new Error('Не удалось найти города');
  }

  const data = await response.json();

  if (!data.results) {
    return [];
  }

  return data.results.map((result: any) => ({
    name: result.name,
    latitude: result.latitude,
    longitude: result.longitude,
    country: result.country,
    state: result.admin1,
  }));
};

export const getWeatherData = async (
  latitude: number,
  longitude: number
): Promise<WeatherData> => {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m,apparent_temperature,pressure_msl&hourly=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto&forecast_days=7&wind_speed_unit=kmh&precipitation_unit=mm`
  );

  if (!response.ok) {
    throw new Error('Не удалось получить данные о погоде');
  }

  const data = await response.json();

  return {
    current: {
      temperature: Math.round(data.current.temperature_2m),
      weatherCode: data.current.weather_code,
      windSpeed: Math.round(data.current.wind_speed_10m),
      humidity: data.current.relative_humidity_2m,
      feelsLike: Math.round(data.current.apparent_temperature),
      pressure: Math.round(data.current.pressure_msl),
    },
    hourly: {
      time: data.hourly.time,
      temperature: data.hourly.temperature_2m.map((temp: number) => Math.round(temp)),
      weatherCode: data.hourly.weather_code,
    },
    daily: {
      time: data.daily.time,
      tempMax: data.daily.temperature_2m_max.map((temp: number) => Math.round(temp)),
      tempMin: data.daily.temperature_2m_min.map((temp: number) => Math.round(temp)),
      weatherCode: data.daily.weather_code,
    },
  };
};

// Helper for Russian day names
export const getRussianDayName = (dateString: string): string => {
  const date = new Date(dateString);
  const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
  return days[date.getDay()];
};