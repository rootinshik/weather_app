import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

export type TemperatureUnit = 'C' | 'F' | 'K';
export type WindUnit = 'ms' | 'kmh' | 'mph';
export type PressureUnit = 'hpa' | 'mmhg';

export interface Units {
  temperature: TemperatureUnit;
  wind: WindUnit;
  pressure: PressureUnit;
}

interface UnitsContextValue {
  units: Units;
  setTemperatureUnit: (u: TemperatureUnit) => void;
  setWindUnit: (u: WindUnit) => void;
  setPressureUnit: (u: PressureUnit) => void;
}

const STORAGE_KEY = 'weather-app-units';

const defaultUnits: Units = { temperature: 'C', wind: 'ms', pressure: 'hpa' };

const UnitsContext = createContext<UnitsContextValue | null>(null);

function loadUnits(): Units {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...defaultUnits, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return defaultUnits;
}

export function UnitsProvider({ children }: { children: ReactNode }) {
  const [units, setUnits] = useState<Units>(loadUnits);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(units));
  }, [units]);

  return (
    <UnitsContext.Provider
      value={{
        units,
        setTemperatureUnit: (temperature) => setUnits((prev) => ({ ...prev, temperature })),
        setWindUnit: (wind) => setUnits((prev) => ({ ...prev, wind })),
        setPressureUnit: (pressure) => setUnits((prev) => ({ ...prev, pressure })),
      }}
    >
      {children}
    </UnitsContext.Provider>
  );
}

export function useUnits(): UnitsContextValue {
  const ctx = useContext(UnitsContext);
  if (!ctx) throw new Error('useUnits must be used within UnitsProvider');
  return ctx;
}
