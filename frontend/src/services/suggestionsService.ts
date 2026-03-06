export interface WeatherSuggestion {
  icon: string;
  category: string;
  suggestion: string;
}

export const getWeatherSuggestions = (
  temperature: number,
  weatherCode: number,
  windSpeed: number,
  humidity: number
): WeatherSuggestion[] => {
  const suggestions: WeatherSuggestion[] = [];

  if (weatherCode >= 61 && weatherCode <= 82) {
    suggestions.push({
      icon: '☔',
      category: 'Зонтик',
      suggestion: 'Возьмите зонтик - ожидается дождь',
    });
  }

  if (weatherCode >= 71 && weatherCode <= 86) {
    suggestions.push({
      icon: '🧥',
      category: 'Зимняя одежда',
      suggestion: 'Носите теплую зимнюю одежду',
    });
  }

  if (temperature < 0) {
    suggestions.push({
      icon: '🧤',
      category: 'Одежда',
      suggestion: 'Очень холодно! Наденьте перчатки, шарф и тяжелое пальто',
    });
  } else if (temperature < 10) {
    suggestions.push({
      icon: '🧥',
      category: 'Одежда',
      suggestion: 'Холодно - носите теплую куртку',
    });
  } else if (temperature < 18) {
    suggestions.push({
      icon: '👔',
      category: 'Одежда',
      suggestion: 'Прохладно - рекомендуется легкая куртка',
    });
  } else if (temperature < 25) {
    suggestions.push({
      icon: '👕',
      category: 'Одежда',
      suggestion: 'Приятная погода - удобная одежда',
    });
  } else if (temperature < 30) {
    suggestions.push({
      icon: '👕',
      category: 'Одежда',
      suggestion: 'Теплая погода - рекомендуется легкая одежда',
    });
  } else {
    suggestions.push({
      icon: '🩳',
      category: 'Одежда',
      suggestion: 'Очень жарко! Носите легкую дышащую одежду',
    });
  }

  if (temperature > 28) {
    suggestions.push({
      icon: '💧',
      category: 'Гидратация',
      suggestion: 'Пейте больше воды - носите с собой напитки',
    });
  }

  if (windSpeed > 30) {
    suggestions.push({
      icon: '💨',
      category: 'Ветер',
      suggestion: 'Очень ветрено - закрепите свободные предметы',
    });
  } else if (windSpeed > 20) {
    suggestions.push({
      icon: '🌬️',
      category: 'Ветер',
      suggestion: 'Ожидаются ветреные условия',
    });
  }

  if (weatherCode === 0 || weatherCode === 1) {
    suggestions.push({
      icon: '🕶️',
      category: 'Защита от солнца',
      suggestion: 'Солнечный день - наденьте солнцезащитные очки',
    });

    if (temperature > 20) {
      suggestions.push({
        icon: '🧴',
        category: 'Защита от солнца',
        suggestion: 'Нанесите солнцезащитный крем перед выходом',
      });
    }
  }

  if (weatherCode >= 45 && weatherCode <= 48) {
    suggestions.push({
      icon: '🚗',
      category: 'Вождение',
      suggestion: 'Туманные условия - ездите осторожно',
    });
  }

  if (weatherCode >= 95) {
    suggestions.push({
      icon: '⚠️',
      category: 'Безопасность',
      suggestion: 'Гроза - старайтесь оставаться в помещении',
    });
  }

  if (humidity > 80 && temperature > 25) {
    suggestions.push({
      icon: '💦',
      category: 'Комфорт',
      suggestion: 'Высокая влажность - может быть некомфортно',
    });
  }

  if (weatherCode === 0 && temperature >= 18 && temperature <= 25 && windSpeed < 15) {
    suggestions.push({
      icon: '🏃',
      category: 'Активность',
      suggestion: 'Идеальная погода для активного отдыха',
    });
  }

  return suggestions;
};
