import { useState } from "react";

interface Props {
  onLogin: (key: string) => void;
}

export function AdminLogin({ onLogin }: Props) {
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      // Changed from "/api/v1/admin/auth" to full URL
      const res = await fetch("http://localhost:8000/api/v1/admin/auth", {
        method: "POST",
        headers: {
          "X-Admin-API-Key": apiKey
        }
      });

      if (res.status === 200) {
        onLogin(apiKey);
      } else {
        setError("Неверный API ключ");
      }
    } catch (error) {
      console.error("Login error:", error);
      setError("Ошибка подключения");
    }
  };

  return (
    <div className="glass p-6 rounded-2xl max-w-md mx-auto">
      <h2 className="text-xl font-semibold mb-4">
        Вход в админ-панель
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="password"
          placeholder="Введите API-ключ"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="w-full p-3 rounded-xl bg-slate-800 text-white"
        />

        {error && (
          <p className="text-red-500 text-sm">
            {error}
          </p>
        )}

        <button
          type="submit"
          className="w-full bg-blue-500 hover:bg-blue-600 p-3 rounded-xl"
        >
          Войти
        </button>
      </form>
    </div>
  );
}