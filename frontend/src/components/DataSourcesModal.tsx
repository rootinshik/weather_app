import { X, Globe } from 'lucide-react';

interface DataSourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const dataSources = [
  {
    name: 'Open-Meteo',
    url: 'https://open-meteo.com',
    priority: 10,
    description: 'Основной источник метеорологических данных. Глобальная сеть метеостанций.',
  },
  {
    name: 'Geocoding API',
    url: 'https://open-meteo.com/en/features/geocoding-api',
    priority: 9,
    description: 'Определение географических координат по названию города.',
  },
];

export function DataSourcesModal({ isOpen, onClose }: DataSourcesModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass rounded-3xl max-w-2xl w-full max-h-96 overflow-y-auto">
        <div className="p-6 border-b border-white/10 flex items-center justify-between sticky top-0 bg-white/5">
          <h2 className="text-xl font-bold text-white">Об источниках данных</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {dataSources.map((source, index) => (
            <div key={index} className="glass-dark rounded-xl p-4 hover:bg-purple-500/20 transition-all">
              <div className="flex items-start gap-3 mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-white">{source.name}</h3>
                    <span className="px-2 py-0.5 bg-purple-500/30 rounded-full text-xs font-bold text-purple-200">
                      Приоритет: {source.priority}/10
                    </span>
                  </div>
                  <p className="text-sm text-purple-300/80 mb-2">{source.description}</p>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-pink-400 hover:text-pink-300 transition-colors"
                  >
                    <Globe className="w-3 h-3" />
                    Посетить сайт
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
