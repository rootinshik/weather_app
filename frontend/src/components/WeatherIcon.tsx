import {
  Sun,
  Cloud,
  CloudRain,
  CloudSnow,
  CloudLightning,
  CloudFog,
} from "lucide-react";

interface WeatherIconProps {
  condition?: string | null;
  size?: number;
}

export function WeatherIcon({ condition, size = 32 }: WeatherIconProps) {
  if (!condition) {
    return <Cloud size={size} />;
  }

  const lower = condition.toLowerCase();

  if (lower.includes("clear")) return <Sun size={size} />;
  if (lower.includes("rain")) return <CloudRain size={size} />;
  if (lower.includes("snow")) return <CloudSnow size={size} />;
  if (lower.includes("storm") || lower.includes("thunder"))
    return <CloudLightning size={size} />;
  if (lower.includes("fog") || lower.includes("mist"))
    return <CloudFog size={size} />;
  if (lower.includes("cloud")) return <Cloud size={size} />;

  return <Cloud size={size} />;
}