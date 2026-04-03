import useConfigStore from '../store/useConfigStore'

export default function ConnectionStatus() {
  const wsConnected = useConfigStore((s) => s.wsConnected)

  return (
    <div className={`status-pill ${wsConnected ? 'connected' : 'disconnected'}`}>
      <span className="status-dot" />
      {wsConnected ? 'Conectado' : 'Desconectado'}
    </div>
  )
}
