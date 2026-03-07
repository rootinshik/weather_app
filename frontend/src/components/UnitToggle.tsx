import { useUnits } from "../context/UnitContext";

export function UnitToggle() {
  const {
    tempUnit,
    setTempUnit,
    windUnit,
    setWindUnit,
    pressureUnit,
    setPressureUnit,
  } = useUnits();

  return (
    <div className="flex gap-2 text-sm">

      {/* TEMPERATURE */}
      <select
        value={tempUnit}
        onChange={(e) =>
          setTempUnit(e.target.value as "C" | "F" | "K")
        }
        className="px-2 py-1 rounded bg-black/20"
      >
        <option value="C">°C</option>
        <option value="F">°F</option>
        <option value="K">K</option>
      </select>


      {/* WIND */}
      <select
        value={windUnit}
        onChange={(e) =>
          setWindUnit(e.target.value as "m/s" | "km/h" | "mph")
        }
        className="px-2 py-1 rounded bg-black/20"
      >
        <option value="m/s">m/s</option>
        <option value="km/h">km/h</option>
        <option value="mph">mph</option>
      </select>


      {/* PRESSURE */}
      <select
        value={pressureUnit}
        onChange={(e) =>
          setPressureUnit(e.target.value as "hPa" | "mmHg")
        }
        className="px-2 py-1 rounded bg-black/20"
      >
        <option value="hPa">hPa</option>
        <option value="mmHg">mmHg</option>
      </select>

    </div>
  );
}