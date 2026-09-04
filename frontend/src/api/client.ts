import type {
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    ErrorResponse,
    HealthResponse,
} from './types'

const DEFAULT_API_BASE_URL = 'http://localhost:8000'

const apiBaseUrl = (
    import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, '')

export class ApiError extends Error {
    readonly status: number

    constructor(status: number, message: string) {
        super(message)

        this.name = 'ApiError'
        this.status = status
    }
}

async function request<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const response = await fetch(
        `${apiBaseUrl}${path}`,
        options,
    )

    if (!response.ok) {
        let message = `API request failed with status ${response.status}`

        try {
            const payload = (await response.json()) as Partial<ErrorResponse>

            if (typeof payload.message === 'string') {
                message = payload.message
            }
        } catch {
            // Keep the status-based fallback when the response is not JSON.
        }

        throw new ApiError(
            response.status,
            message,
        )
    }

    return (await response.json()) as T
}

export function getHealth(
    signal?: AbortSignal,
): Promise<HealthResponse> {
    return request<HealthResponse>(
        '/health',
        {
            headers: {
                Accept: 'application/json',
            },
            signal,
        },
    )
}

export function createSession(
    signal?: AbortSignal,
): Promise<CreateSessionResponse> {
    return request<CreateSessionResponse>(
        '/api/v1/sessions',
        {
            method: 'POST',
            headers: {
                Accept: 'application/json',
            },
            signal,
        },
    )
}

export function sendChatMessage(
    sessionId: string,
    message: string,
    signal?: AbortSignal,
): Promise<ChatResponse> {
    const requestBody: ChatRequest = {
        message,
    }

    return request<ChatResponse>(
        `/api/v1/sessions/${encodeURIComponent(sessionId)}/chat`,
        {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
            signal,
        },
    )
}
