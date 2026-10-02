import type {
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    DeleteSessionResponse,
    ErrorResponse,
    HealthResponse,
    SessionHistoryResponse,
    ChatStreamEvent,
} from './types'

import { parseChatStream } from './chatStreamParser'

const DEFAULT_API_BASE_URL = 'http://localhost:8000'

const apiBaseUrl = (
    import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL
).replace(/\/+$/, '')

export class ApiError extends Error {
    readonly status: number
    readonly requestId: string | null

    constructor(
        status: number,
        message: string,
        requestId: string | null = null,
    ) {
        super(message)

        this.name = 'ApiError'
        this.status = status
        this.requestId = requestId
    }
}

export class ChatStreamError extends Error {
    readonly requestId: string | null

    constructor(message: string, requestId: string | null = null) {
        super(message)

        this.name = 'ChatStreamError'
        this.requestId = requestId
    }
}

async function createApiError(response: Response): Promise<ApiError> {
    let message = `API request failed with status ${response.status}`

    try {
        const payload = (await response.json()) as Partial<ErrorResponse>

        if (typeof payload.message === 'string') {
            message = payload.message
        }
    } catch {
        // Keep the status-based fallback when the response is not JSON.
    }

    return new ApiError(
        response.status,
        message,
        response.headers.get('X-Request-ID'),
    )
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${apiBaseUrl}${path}`, options)

    if (!response.ok) {
        throw await createApiError(response)
    }

    return (await response.json()) as T
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    return request<HealthResponse>('/health', {
        headers: {
            Accept: 'application/json',
        },
        signal,
    })
}

export function createSession(
    signal?: AbortSignal,
): Promise<CreateSessionResponse> {
    return request<CreateSessionResponse>('/api/v1/sessions', {
        method: 'POST',
        headers: {
            Accept: 'application/json',
        },
        signal,
    })
}

export function deleteSession(
    sessionId: string,
    signal?: AbortSignal,
): Promise<DeleteSessionResponse> {
    return request<DeleteSessionResponse>(
        `/api/v1/sessions/${encodeURIComponent(sessionId)}`,
        {
            method: 'DELETE',
            headers: {
                Accept: 'application/json',
            },
            signal,
        },
    )
}

export function getSessionHistory(
    sessionId: string,
    signal?: AbortSignal,
): Promise<SessionHistoryResponse> {
    return request<SessionHistoryResponse>(
        `/api/v1/sessions/${encodeURIComponent(sessionId)}/history`,
        {
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

export async function* streamChatMessage(
    sessionId: string,
    message: string,
    signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent> {
    const requestBody: ChatRequest = {
        message,
    }

    const response = await fetch(
        `${apiBaseUrl}/api/v1/sessions/` +
            `${encodeURIComponent(sessionId)}/chat/stream`,
        {
            method: 'POST',
            headers: {
                Accept: 'text/event-stream',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
            signal,
        },
    )

    if (!response.ok) {
        throw await createApiError(response)
    }

    const requestId = response.headers.get('X-Request-ID')
    const contentType = response.headers.get('Content-Type')

    if (
        contentType === null ||
        !contentType.toLowerCase().startsWith('text/event-stream')
    ) {
        throw new ChatStreamError(
            'API returned an invalid chat stream response.',
            requestId,
        )
    }

    if (response.body === null) {
        throw new ChatStreamError(
            'API returned an empty chat stream response.',
            requestId,
        )
    }

    try {
        for await (const event of parseChatStream(response.body)) {
            if (event.type === 'error') {
                yield {
                    ...event,
                    requestId,
                }
                return
            }

            yield event

            if (event.type === 'completed') {
                return
            }
        }
    } catch {
        throw new ChatStreamError('Unable to read the chat stream.', requestId)
    }

    throw new ChatStreamError('Chat stream ended before completion.', requestId)
}
