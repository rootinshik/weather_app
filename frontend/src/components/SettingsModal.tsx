import { X, Sun, Moon } from 'lucide-react';
import { getSettings, saveSettings, setTheme, Theme, TempUnit, SpeedUnit, PressureUnit } from '../services/themeService';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const settings = getSettings();

  const handleThemeChange = (theme: Theme) => {
    setTheme(theme);
    window.location.reload();
  };

  const handleUnitChange = (key: 'tempUnit' | 'speedUnit' | 'pressureUnit', value: string) => {
    const newSettings = { ...settings, [key]: value };
    saveSettings(newSettings);
    window.location.reload();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 [data-theme=light]:bg-black/30">
      <div className="glass rounded-3xl max-w-md w-full max-h-96 overflow-y-auto [data-theme=light]:bg-white [data-theme=light]:border-gray-300">
        <div className="p-6 border-b border-white/10 flex items-center justify-between sticky top-0 bg-white/5 [data-theme=light]:bg-gray-50 [data-theme=light]:border-gray-200">
          <h2 className="text-xl font-bold text-white [data-theme=light]:text-gray-900">Настройки</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-full transition-colors [data-theme=light]:hover:bg-gray-200"
          >
            <X className="w-5 h-5 text-white [data-theme=light]:text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-purple-200 mb-3 [data-theme=light]:text-gray-700">Тема</h3>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleThemeChange('dark')}
                className={`p-3 rounded-lg border transition-all ${
                  settings.theme === 'dark'
                    ? 'bg-purple-500/30 border-purple-400 text-white [data-theme=light]:bg-purple-100 [data-theme=light]:border-purple-400 [data-theme=light]:text-purple-900'
                    : 'glass text-purple-200 hover:text-white [data-theme=light]:bg-white [data-theme=light]:border-gray-300 [data-theme=light]:text-gray-600'
                }`}
              >
                <Moon className="w-4 h-4 mx-auto mb-1" />
                <span className="text-xs font-medium">Тёмная</span>
              </button>
              <button
                onClick={() => handleThemeChange('light')}
                className={`p-3 rounded-lg border transition-all ${
                  settings.theme === 'light'
                    ? 'bg-blue-200/30 border-blue-400 text-gray-900 [data-theme=light]:bg-blue-100 [data-theme=light]:border-blue-400'
                    : 'glass text-purple-200 hover:text-white [data-theme=light]:bg-white [data-theme=light]:border-gray-300 [data-theme=light]:text-gray-600'
                }`}
              >
                <Sun className="w-4 h-4 mx-auto mb-1" />
                <span className="text-xs font-medium">Светлая</span>
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-purple-200 mb-3">Температура</h3>
            <div className="grid grid-cols-2 gap-2">
              {(['C', 'F'] as TempUnit[]).map(unit => (
                <button
                  key={unit}
                  onClick={() => handleUnitChange('tempUnit', unit)}
                  className={`p-2 rounded-lg text-sm font-medium border transition-all ${
                    settings.tempUnit === unit
                      ? 'bg-purple-500/30 border-purple-400 text-white'
                      : 'glass text-purple-200 hover:text-white'
                  }`}
                >
                  °{unit}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-purple-200 mb-3">Скорость ветра</h3>
            <div className="grid grid-cols-2 gap-2">
              {(['kmh', 'mph'] as SpeedUnit[]).map(unit => (
                <button
                  key={unit}
                  onClick={() => handleUnitChange('speedUnit', unit)}
                  className={`p-2 rounded-lg text-sm font-medium border transition-all ${
                    settings.speedUnit === unit
                      ? 'bg-purple-500/30 border-purple-400 text-white'
                      : 'glass text-purple-200 hover:text-white'
                  }`}
                >
                  {unit === 'kmh' ? 'км/ч' : 'миль/ч'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-purple-200 mb-3">Давление</h3>
            <div className="grid grid-cols-3 gap-2">
              {(['kPa', 'mmHg', 'atm'] as PressureUnit[]).map(unit => (
                <button
                  key={unit}
                  onClick={() => handleUnitChange('pressureUnit', unit)}
                  className={`p-2 rounded-lg text-xs font-medium border transition-all ${
                    settings.pressureUnit === unit
                      ? 'bg-purple-500/30 border-purple-400 text-white'
                      : 'glass text-purple-200 hover:text-white'
                  }`}
                >
                  {unit}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
