/**
 * Gmail Inbox Page — centralized inbox for multiple Gmail accounts
 * TODO: Backend OAuth2 integration (FASE 5)
 */
export default function InboxPage() {
  return (
    <div className="p-8 space-y-8 max-w-[1800px]">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">COMUNICAÇÃO</span>
        <h2 className="text-3xl font-bold tracking-tight">Inbox Gmail</h2>
      </div>

      <div className="glass-card rounded-2xl p-16 text-center">
        <span className="material-symbols-outlined text-7xl text-on-surface-variant opacity-30">inbox</span>
        <h3 className="mt-6 text-xl font-bold">Em breve</h3>
        <p className="mt-2 text-on-surface-variant max-w-md mx-auto">
          O módulo de Inbox Gmail está sendo desenvolvido. Você poderá conectar
          múltiplas contas Gmail, visualizar e responder emails diretamente aqui.
        </p>
        <div className="mt-8 flex flex-wrap gap-3 justify-center">
          {[
            { icon: 'account_circle', text: 'Multi-conta' },
            { icon: 'filter_list', text: 'Filtros avançados' },
            { icon: 'translate', text: 'Tradução automática' },
            { icon: 'smart_toy', text: 'Classificação por IA' },
            { icon: 'description', text: 'Templates de resposta' },
          ].map(f => (
            <div key={f.text} className="flex items-center gap-2 px-4 py-2 bg-surface-container rounded-full text-sm text-on-surface-variant">
              <span className="material-symbols-outlined text-base text-primary">{f.icon}</span>
              {f.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
