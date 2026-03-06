import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

interface HourlyPoint {
  hour: string;
  temperature: number;
}

interface DailyPoint {
  date: string;
  temp_avg: number;
}

interface Props {
  hourlyData?: HourlyPoint[];
  dailyData?: DailyPoint[];
  isLoading: boolean;
}

export function TemperatureGraph({ hourlyData, dailyData, isLoading }: Props) {

  const [mode, setMode] = useState<"24h" | "7d">("24h");

  if (isLoading) {
    return <p>Загрузка графика...</p>;
  }

  if (!hourlyData || !dailyData) {
    return <p>Не удалось загрузить данные графика</p>;
  }

  // ⭐ convert hourly
  const hourly = hourlyData.map((p) => ({
    time: new Date(p.hour).getHours() + ":00",
    temp: Number(p.temperature.toFixed(1))
  }));

  // ⭐ convert daily
  const daily = dailyData.map((p) => ({
    time: new Date(p.date).toLocaleDateString("ru-RU", {
      weekday: "short"
    }),
    temp: Number(p.temp_avg.toFixed(1))
  }));

  const chartData = mode === "24h" ? hourly : daily;

  return (
    <div className="glass p-6 rounded-2xl">

      {/* MODE SWITCH */}
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setMode("24h")}
          className={`px-3 py-1 rounded ${
            mode === "24h" ? "bg-accent text-white" : "bg-gray-700 text-gray-300"
          }`}
        >
          24ч
        </button>

        <button
          onClick={() => setMode("7d")}
          className={`px-3 py-1 rounded ${
            mode === "7d" ? "bg-accent text-white" : "bg-gray-700 text-gray-300"
          }`}
        >
          7д
        </button>
      </div>

      {/* CHART */}
      <div className="w-full h-[320px]">

        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

            <XAxis
              dataKey="time"
              stroke="#94a3b8"
            />

            <YAxis
              stroke="#94a3b8"
              tickFormatter={(v) => `${v}°`}
            />

            <Tooltip
  contentStyle={{
    backgroundColor: "#1e293b",
    border: "none",
    borderRadius: "8px",
    color: "#fff"
  }}
  labelStyle={{ color: "#94a3b8" }}
  formatter={(value: number | undefined) => `${value?.toFixed(1) ?? 0}°C`}
/>

            <Line
              type="monotone"
              dataKey="temp"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />

          </LineChart>
        </ResponsiveContainer>

      </div>

    </div>
  );
}