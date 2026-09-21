export interface HealthResponse {
    status: 'ok'
    service: string
    version: string
}

export interface CreateSessionResponse {
    session_id: string
}

export interface DeleteSessionResponse {
    deleted: boolean
}

export interface HistoryMessageResponse {
    role: string
    content: string | null
}

export interface SessionHistoryResponse {
    session_id: string
    messages: HistoryMessageResponse[]
}

export interface ErrorResponse {
    error: string
    message: string
}

export interface ChatRequest {
    message: string
}

export interface ChatResponse {
    response: string
}

export interface ChatContentDeltaEvent {
    type: 'content_delta'
    content: string
}

export interface ChatCompletedEvent {
    type: 'completed'
    response: string
}

export interface ChatErrorEvent {
    type: 'error'
    error: string
    message: string
}

export type ChatStreamEvent =
    ChatContentDeltaEvent | ChatCompletedEvent | ChatErrorEvent
