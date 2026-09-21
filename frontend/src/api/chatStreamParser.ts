import type { ChatStreamEvent } from './types'

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null
}

interface EventBoundary {
    index: number
    length: number
}

function findEventBoundary(buffer: string): EventBoundary | null {
    const lineFeedIndex = buffer.indexOf('\n\n')
    const carriageReturnIndex = buffer.indexOf('\r\n\r\n')

    if (lineFeedIndex === -1 && carriageReturnIndex === -1) {
        return null
    }

    if (
        carriageReturnIndex !== -1 &&
        (lineFeedIndex === -1 || carriageReturnIndex < lineFeedIndex)
    ) {
        return {
            index: carriageReturnIndex,
            length: 4,
        }
    }

    return {
        index: lineFeedIndex,
        length: 2,
    }
}

function createChatStreamEvent(
    eventName: string,
    payload: unknown,
): ChatStreamEvent {
    if (!isRecord(payload)) {
        throw new Error('Chat stream event payload must be an object.')
    }

    if (eventName === 'content_delta' && typeof payload.content === 'string') {
        return {
            type: 'content_delta',
            content: payload.content,
        }
    }

    if (eventName === 'completed' && typeof payload.response === 'string') {
        return {
            type: 'completed',
            response: payload.response,
        }
    }

    if (
        eventName === 'error' &&
        typeof payload.error === 'string' &&
        typeof payload.message === 'string'
    ) {
        return {
            type: 'error',
            error: payload.error,
            message: payload.message,
        }
    }

    throw new Error(`Invalid chat stream event: ${eventName}`)
}

function parseEventBlock(block: string): ChatStreamEvent | null {
    let eventName: string | null = null
    const dataLines: string[] = []

    for (const line of block.split(/\r?\n/)) {
        if (line.startsWith('event:')) {
            eventName = line.slice('event:'.length).trim()
        } else if (line.startsWith('data:')) {
            dataLines.push(line.slice('data:'.length).trimStart())
        }
    }

    if (eventName === null || dataLines.length === 0) {
        return null
    }

    const payload: unknown = JSON.parse(dataLines.join('\n'))

    return createChatStreamEvent(eventName, payload)
}

export async function* parseChatStream(
    stream: ReadableStream<Uint8Array>,
): AsyncGenerator<ChatStreamEvent> {
    const reader = stream.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
        while (true) {
            const { done, value } = await reader.read()

            if (done) {
                break
            }

            buffer += decoder.decode(value, {
                stream: true,
            })

            let boundary = findEventBoundary(buffer)

            while (boundary !== null) {
                const block = buffer.slice(0, boundary.index)

                buffer = buffer.slice(boundary.index + boundary.length)

                const event = parseEventBlock(block)

                if (event !== null) {
                    yield event
                }

                boundary = findEventBoundary(buffer)
            }
        }

        buffer += decoder.decode()

        if (buffer.trim()) {
            const event = parseEventBlock(buffer)

            if (event !== null) {
                yield event
            }
        }
    } finally {
        reader.releaseLock()
    }
}
