import { useState, useEffect } from "react";
import { AdminLogin } from "./AdminLogin";
import { StatsPanel } from "./StatsPanel";
import { LogsPanel } from "./LogsPanel";

export function AdminPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [stats, setStats] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!apiKey) return;

    async function loadAdminData() {
      try {
        setLoading(true);

        // Add type check to ensure apiKey is string
        const headers = {
          "X-Admin-API-Key": apiKey as string
        };

        const statsRes = await fetch("/api/v1/admin/stats", {
          headers
        });

        const statsData = await statsRes.json();
        setStats(statsData);

        const logsRes = await fetch("/api/v1/admin/logs?limit=20", {
          headers
        });

        const logsData = await logsRes.json();
        setLogs(logsData.items || []);
      } catch (err) {
        console.error("Admin API error:", err);
      } finally {
        setLoading(false);
      }
    }

    loadAdminData();
  }, [apiKey]);

  if (!apiKey) {
    return <AdminLogin onLogin={setApiKey} />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">
        Админ-панель
      </h1>

      {loading && (
        <p className="text-muted">Загрузка данных...</p>
      )}

      <StatsPanel stats={stats} />
      <LogsPanel logs={logs} />
    </div>
  );
}