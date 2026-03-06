export function convertTemperature(value: number, unit: "C" | "F") {
  if (unit === "F") return (value * 9) / 5 + 32;
  return value; // Celsius default
}

export function convertWind(value: number, unit: "m/s" | "km/h") {
  if (unit === "km/h") return value * 3.6;
  return value; // m/s default
}

export function convertPressure(value: number, unit: "hPa" | "mmHg") {
  if (unit === "mmHg") return value * 0.75006;
  return value; // hPa default
}