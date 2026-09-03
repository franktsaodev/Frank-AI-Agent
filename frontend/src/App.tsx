import './App.css'

const capabilities = [
  {
    title: 'Knowledge retrieval',
    description: 'Ask questions about indexed project documentation.',
  },
  {
    title: 'Trusted citations',
    description: 'Receive answers backed by validated document sources.',
  },
  {
    title: 'Agent tools',
    description: 'Interact with tools through the agent execution flow.',
  },
] as const

function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            F
          </div>

          <div>
            <p className="brand-eyebrow">AI Agent</p>
            <h1>Frank</h1>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">Workspace</p>

          <div className="navigation-item navigation-item-active">
            <span className="navigation-icon" aria-hidden="true">
              ◇
            </span>
            New conversation
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="status-dot" aria-hidden="true" />

          <div>
            <strong>Interface ready</strong>
            <span>API integration is next</span>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="workspace-eyebrow">Agent Playground</p>
            <h2>New conversation</h2>
          </div>

          <span className="version-badge">v1.3 in progress</span>
        </header>

        <section className="conversation" aria-labelledby="welcome-heading">
          <div className="welcome">
            <div className="welcome-icon" aria-hidden="true">
              ✦
            </div>

            <p className="welcome-eyebrow">Frank AI Agent</p>
            <h2 id="welcome-heading">What can I help you explore?</h2>

            <p className="welcome-description">
              Chat with a modular AI agent featuring retrieval, memory,
              tool calling, and trusted source attribution.
            </p>

            <div className="capability-grid">
              {capabilities.map((capability) => (
                <article className="capability-card" key={capability.title}>
                  <h3>{capability.title}</h3>
                  <p>{capability.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <footer className="composer">
          <div className="composer-control">
            <textarea
              aria-label="Chat message"
              disabled
              placeholder="Connect the API to start chatting…"
              rows={1}
            />

            <button type="button" disabled>
              Send
            </button>
          </div>

          <p>Frontend scaffold ready · Session API integration comes next</p>
        </footer>
      </main>
    </div>
  )
}

export default App