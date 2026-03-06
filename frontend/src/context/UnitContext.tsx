import { createContext, useContext, useState, ReactNode } from "react";

type TempUnit = "C" | "F" | "K";
type WindUnit = "ms" | "kmh" | "mph";
type PressureUnit = "hPa" | "mmHg";

interface UnitContextType {
  tempUnit: TempUnit;
  windUnit: WindUnit;
  pressureUnit: PressureUnit;
  setTempUnit: (u: TempUnit) => void;
  setWindUnit: (u: WindUnit) => void;
  setPressureUnit: (u: PressureUnit) => void;
}

const UnitContext = createContext<UnitContextType | null>(null);

export function UnitProvider({ children }: { children: ReactNode }) {
  const [tempUnit, setTempUnit] = useState<TempUnit>("C");
  const [windUnit, setWindUnit] = useState<WindUnit>("ms");
  const [pressureUnit, setPressureUnit] = useState<PressureUnit>("hPa");

  return (
    <UnitContext.Provider
      value={{
        tempUnit,
        windUnit,
        pressureUnit,
        setTempUnit,
        setWindUnit,
        setPressureUnit,
      }}
    >
      {children}
    </UnitContext.Provider>
  );
}

export function useUnits() {
  const ctx = useContext(UnitContext);
  if (!ctx) {
    throw new Error("useUnits must be used inside UnitProvider");
  }
  return ctx;
}