import {
    ApiError,
    createSession,
    getHealth,
    getSessionHistory,
} from '../api/client'
import type { HealthResponse, HistoryMessageResponse } from '../api/types'
import {
    clearStoredSessionId,
    getStoredSessionId,
    storeSessionId,
} from '../storage/activeSessionStorage'

export interface ApplicationInitializationResult {
    health: HealthResponse
    sessionId: string
    history: HistoryMessageResponse[]
}

let initializationPromise: Promise<ApplicationInitializationResult> | null =
    null

async function performInitialization(): Promise<ApplicationInitializationResult> {
    const health = await getHealth()
    const storedSessionId = getStoredSessionId()

    if (storedSessionId !== null) {
        try {
            const sessionHistory = await getSessionHistory(storedSessionId)

            return {
                health,
                sessionId: sessionHistory.session_id,
                history: sessionHistory.messages,
            }
        } catch (error: unknown) {
            if (!(error instanceof ApiError) || error.status !== 404) {
                throw error
            }

            clearStoredSessionId()
        }
    }

    const session = await createSession()

    storeSessionId(session.session_id)

    return {
        health,
        sessionId: session.session_id,
        history: [],
    }
}

export function initializeApplication(): Promise<ApplicationInitializationResult> {
    if (initializationPromise === null) {
        initializationPromise = performInitialization().catch(
            (error: unknown) => {
                initializationPromise = null

                throw error
            },
        )
    }

    return initializationPromise
}

export function resetApplicationInitialization(): void {
    initializationPromise = null
}
