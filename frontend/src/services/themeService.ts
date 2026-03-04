export type Theme = 'dark' | 'light';
export type TempUnit = 'C' | 'F';
export type SpeedUnit = 'kmh' | 'mph';
export type PressureUnit = 'kPa' | 'mmHg' | 'atm';

export interface UserSettings {
  theme: Theme;
  tempUnit: TempUnit;
  speedUnit: SpeedUnit;
  pressureUnit: PressureUnit;
}

const THEME_KEY = 'weatrack_theme';
const SETTINGS_KEY = 'weatrack_settings';

const DEFAULT_SETTINGS: UserSettings = {
  theme: 'dark',
  tempUnit: 'C',
  speedUnit: 'kmh',
  pressureUnit: 'kPa',
};

export const getSettings = (): UserSettings => {
  const stored = localStorage.getItem(SETTINGS_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return DEFAULT_SETTINGS;
    }
  }
  return DEFAULT_SETTINGS;
};

export const saveSettings = (settings: UserSettings): void => {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
};

export const setTheme = (theme: Theme): void => {
  const doc = document.documentElement;
  doc.setAttribute('data-theme', theme);
  const settings = getSettings();
  settings.theme = theme;
  saveSettings(settings);
};

export const getTheme = (): Theme => {
  const settings = getSettings();
  const theme = settings.theme;
  if (document.documentElement.getAttribute('data-theme') !== theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }
  return theme;
};

export const initTheme = (): void => {
  const settings = getSettings();
  document.documentElement.setAttribute('data-theme', settings.theme);
};

export const convertTemperature = (value: number, from: TempUnit, to: TempUnit): number => {
  if (from === to) return value;
  if (from === 'C' && to === 'F') return (value * 9) / 5 + 32;
  if (from === 'F' && to === 'C') return ((value - 32) * 5) / 9;
  return value;
};

export const convertSpeed = (value: number, from: SpeedUnit, to: SpeedUnit): number => {
  if (from === to) return value;
  if (from === 'kmh' && to === 'mph') return value * 0.621371;
  if (from === 'mph' && to === 'kmh') return value / 0.621371;
  return value;
};

export const convertPressure = (value: number, from: PressureUnit, to: PressureUnit): number => {
  if (from === to) return value;

  let kpa = value;
  if (from === 'mmHg') kpa = value * 0.133322;
  if (from === 'atm') kpa = value * 101.325;

  if (to === 'mmHg') return kpa / 0.133322;
  if (to === 'atm') return kpa / 101.325;
  return kpa;
};

export const formatTemp = (value: number, unit: TempUnit): string => `${Math.round(value)}°${unit}`;
export const formatSpeed = (value: number, unit: SpeedUnit): string =>
  `${Math.round(value)} ${unit === 'kmh' ? 'км/ч' : 'миль/ч'}`;
export const formatPressure = (value: number, unit: PressureUnit): string => {
  const units = { kPa: 'кПа', mmHg: 'мм рт.ст.', atm: 'атм' };
  return `${Math.round(value * 10) / 10} ${units[unit]}`;
};
