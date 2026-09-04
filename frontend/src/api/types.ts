export interface HealthResponse {
    status: 'ok'
    service: string
    version: string
}

export interface CreateSessionResponse {
    session_id: string
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
