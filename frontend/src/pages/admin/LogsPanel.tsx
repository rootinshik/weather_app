interface Log {
  id: number
  platform: string
  action: string
  city_id: number
  created_at: string
}

interface Props {
  logs: Log[]
}

export function LogsPanel({ logs }: Props) {
  return (
    <div className="glass p-6 rounded-2xl">

      <h3 className="text-lg font-semibold mb-4">
        Логи запросов
      </h3>

      <table className="w-full text-sm">

        <thead>
          <tr className="text-left text-gray-400">
            <th>Время</th>
            <th>Действие</th>
            <th>Платформа</th>
            <th>Город</th>
          </tr>
        </thead>

        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-t border-gray-700">

              <td>
                {new Date(log.created_at).toLocaleTimeString()}
              </td>

              <td>{log.action}</td>

              <td>{log.platform}</td>

              <td>{log.city_id ?? "-"}</td>

            </tr>
          ))}
        </tbody>

      </table>

    </div>
  )
}