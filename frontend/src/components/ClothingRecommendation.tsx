import { Shirt, Sun } from "lucide-react";

interface RecommendationData {
  summary: string;
  advice: string[];
  risk_level?: string;
}

interface RecommendationResponse {
  city_id: number;
  recommendation: RecommendationData;
}

interface Props {
  data?: RecommendationResponse;
  isLoading?: boolean;
}

export function ClothingRecommendation({ data, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="glass p-6 rounded-2xl">
        <p className="text-muted">Загрузка рекомендаций...</p>
      </div>
    );
  }

  if (!data?.recommendation) {
    return (
      <div className="glass p-6 rounded-2xl">
        <p className="text-muted">Рекомендации отсутствуют</p>
      </div>
    );
  }

  const rec = data.recommendation;

  return (
    <div className="glass p-6 rounded-2xl shadow-lg">
      <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
        <Shirt className="w-6 h-6 text-accent" />
        Рекомендации по одежде
      </h2>

      <p className="mb-4 text-lg">{rec.summary}</p>

      <ul className="space-y-2">
        {rec.advice.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            <Sun className="w-4 h-4 text-accent" />
            {item}
          </li>
        ))}
      </ul>

      {rec.risk_level && (
        <p className="mt-4 text-sm text-muted">
          Уровень риска: {rec.risk_level}
        </p>
      )}
    </div>
  );
}