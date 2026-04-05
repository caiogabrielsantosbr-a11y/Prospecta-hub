import useConfigStore from '../store/useConfigStore'

export default function ConnectionStatus() {
  const connectionStatus = useConfigStore((s) => s.connectionStatus)
  const isConnected = connectionStatus === 'connected'

  return (
    <div className={`status-pill ${isConnected ? 'connected' : 'disconnected'}`}>
      <span className="status-dot" />
      {isConnected ? 'Conectado' : 'Desconectado'}
    </div>
  )
}
