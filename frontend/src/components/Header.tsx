import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import {
  useUnits,
  type TemperatureUnit,
  type WindUnit,
  type PressureUnit,
} from '../context/UnitsContext';

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const { units, setTemperatureUnit, setWindUnit, setPressureUnit } = useUnits();

  return (
    <header className="app-header">
      <div className="header-left">
        <Link to="/">Weather Aggregator</Link>
        <input type="text" placeholder="Search city..." disabled />
      </div>
      <div className="header-right">
        <button onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'light' ? '\u{1F319}' : '\u{2600}\u{FE0F}'}
        </button>
        <select
          value={units.temperature}
          onChange={(e) => setTemperatureUnit(e.target.value as TemperatureUnit)}
          aria-label="Temperature unit"
        >
          <option value="C">&deg;C</option>
          <option value="F">&deg;F</option>
          <option value="K">K</option>
        </select>
        <select
          value={units.wind}
          onChange={(e) => setWindUnit(e.target.value as WindUnit)}
          aria-label="Wind speed unit"
        >
          <option value="ms">m/s</option>
          <option value="kmh">km/h</option>
          <option value="mph">mph</option>
        </select>
        <select
          value={units.pressure}
          onChange={(e) => setPressureUnit(e.target.value as PressureUnit)}
          aria-label="Pressure unit"
        >
          <option value="hpa">hPa</option>
          <option value="mmhg">mmHg</option>
        </select>
      </div>
    </header>
  );
}
