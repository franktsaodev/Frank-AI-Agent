const ACTIVE_SESSION_ID_KEY = 'frank-ai-agent.active-session-id'

export function getStoredSessionId(): string | null {
    try {
        const sessionId = window.localStorage.getItem(
            ACTIVE_SESSION_ID_KEY,
        )

        if (sessionId === null || !sessionId.trim()) {
            return null
        }

        return sessionId
    } catch {
        return null
    }
}

export function storeSessionId(
    sessionId: string,
): void {
    try {
        window.localStorage.setItem(
            ACTIVE_SESSION_ID_KEY,
            sessionId,
        )
    } catch {
        // The application can still work when browser storage is unavailable.
    }
}

export function clearStoredSessionId(): void {
    try {
        window.localStorage.removeItem(
            ACTIVE_SESSION_ID_KEY,
        )
    } catch {
        // The application can still work when browser storage is unavailable.
    }
}