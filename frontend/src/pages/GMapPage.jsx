            <button
              onClick={handleStart}
              disabled={isStarting || currentTask?.status === 'running'}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginBottom: 8, pointerEvents: isStarting || currentTask?.status === 'running' ? 'none' : 'auto' }}
              aria-busy={isStarting}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              {isStarting ? 'Iniciando...' : 'Iniciar Processo'}
            </button>
