import useConfigStore from '../store/useConfigStore'

export default function ConnectionStatus() {
  const { connectionStatus, isConfigured } = useConfigStore()

  if (!isConfigured()) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
        <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
        <span>Backend não configurado</span>
      </div>
    )
  }

  const statusConfig = {
    connected: {
      color: 'bg-green-100 text-green-800',
      dot: 'bg-green-500',
      label: 'Conectado'
    },
    disconnected: {
      color: 'bg-red-100 text-red-800',
      dot: 'bg-red-500',
      label: 'Desconectado'
    },
    testing: {
      color: 'bg-blue-100 text-blue-800',
      dot: 'bg-blue-500 animate-pulse',
      label: 'Testando...'
    },
  }

  const config = statusConfig[connectionStatus] || statusConfig.disconnected

  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${config.color}`}>
      <span className={`w-2 h-2 rounded-full ${config.dot}`}></span>
      <span>{config.label}</span>
    </div>
  )
}
