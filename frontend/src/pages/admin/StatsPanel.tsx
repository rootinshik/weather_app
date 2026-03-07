interface Stat {
  date: string;
  platform: string;
  total_requests: number;
  unique_users: number;
}

interface Props {
  stats: Stat[];
}

export function StatsPanel({ stats }: Props) {

  return (
    <div className="glass p-6 rounded-2xl">

      <h3 className="text-lg font-semibold mb-4">
        Статистика API
      </h3>

      <table className="w-full text-sm">

        <thead>
          <tr className="text-left text-gray-400">
            <th>Дата</th>
            <th>Платформа</th>
            <th>Запросы</th>
            <th>Пользователи</th>
          </tr>
        </thead>

        <tbody>

          {stats.map((s, i) => (

            <tr key={i} className="border-t border-gray-700">

              <td>{s.date}</td>

              <td>{s.platform}</td>

              <td>{s.total_requests}</td>

              <td>{s.unique_users}</td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>
  );
}