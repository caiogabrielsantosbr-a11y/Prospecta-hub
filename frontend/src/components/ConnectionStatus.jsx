import useConfigStore from '../store/useConfigStore'

export default function ConnectionStatus() {
  const { connectionStatus, isConfigured } = useConfigStore()

  if (!isConfigured()) {
    return (
      <div style={{ display:'flex', alignItems:'center', gap:5, padding:'4px 10px', borderRadius:100, background:'rgba(251,191,36,0.12)', fontSize:11, fontWeight:600, color:'#fbbf24' }}>
        <span style={{ width:6, height:6, borderRadius:'50%', background:'#fbbf24', flexShrink:0 }} />
        Não configurado
      </div>
    )
  }

  const cfg = {
    connected:    { bg:'rgba(74,222,128,0.12)', dot:'#4ade80', label:'Conectado' },
    disconnected: { bg:'rgba(248,113,113,0.12)', dot:'#f87171', label:'Desconectado' },
    testing:      { bg:'rgba(96,165,250,0.12)',  dot:'#60a5fa', label:'Testando...' },
  }[connectionStatus] || { bg:'rgba(248,113,113,0.12)', dot:'#f87171', label:'Desconectado' }

  return (
    <div style={{ display:'flex', alignItems:'center', gap:5, padding:'4px 10px', borderRadius:100, background:cfg.bg, fontSize:11, fontWeight:600, color:cfg.dot }}>
      <span style={{ width:6, height:6, borderRadius:'50%', background:cfg.dot, flexShrink:0 }} />
      {cfg.label}
    </div>
  )
}
