import {
    describe,
    expect,
    it,
} from 'vitest'

import {
    parseChatStream,
} from './chatStreamParser'
import type {
    ChatStreamEvent,
} from './types'

function createByteStream(
    chunks: Uint8Array[],
): ReadableStream<Uint8Array> {
    return new ReadableStream<Uint8Array>({
        start(controller) {
            for (const chunk of chunks) {
                controller.enqueue(chunk)
            }

            controller.close()
        },
    })
}

function createTextStream(
    chunks: string[],
): ReadableStream<Uint8Array> {
    const encoder = new TextEncoder()

    return createByteStream(
        chunks.map((chunk) => encoder.encode(chunk)),
    )
}

async function collectEvents(
    stream: ReadableStream<Uint8Array>,
): Promise<ChatStreamEvent[]> {
    const events: ChatStreamEvent[] = []

    for await (const event of parseChatStream(stream)) {
        events.push(event)
    }

    return events
}

describe('chat stream parser', () => {
    it('should parse events split across network chunks', async () => {
        const stream = createTextStream([
            'event: content_',
            'delta\ndata: {"content":"你好"}\n\n',
            'event: completed\n',
            'data: {"response":"你好"}\n\n',
        ])

        const events = await collectEvents(stream)

        expect(events).toEqual([
            {
                type: 'content_delta',
                content: '你好',
            },
            {
                type: 'completed',
                response: '你好',
            },
        ])
    })

    it('should parse an error event', async () => {
        const stream = createTextStream([
            'event: error\n',
            'data: {"error":"client_timeout",',
            '"message":"The request timed out."}\n\n',
        ])

        const events = await collectEvents(stream)

        expect(events).toEqual([
            {
                type: 'error',
                error: 'client_timeout',
                message: 'The request timed out.',
            },
        ])
    })

    it('should preserve UTF-8 characters split across byte chunks', async () => {
        const encodedEvent = new TextEncoder().encode(
            'event: content_delta\n' +
            'data: {"content":"你好"}\n\n',
        )

        const multibyteStart = encodedEvent.findIndex(
            (value) => value > 0x7f,
        )

        if (multibyteStart === -1) {
            throw new Error(
                'Expected the test event to contain UTF-8 bytes.',
            )
        }

        const stream = createByteStream([
            encodedEvent.slice(
                0,
                multibyteStart + 1,
            ),
            encodedEvent.slice(
                multibyteStart + 1,
            ),
        ])

        const events = await collectEvents(stream)

        expect(events).toEqual([
            {
                type: 'content_delta',
                content: '你好',
            },
        ])
    })

    it('should parse multiple CRLF-delimited events', async () => {
        const stream = createTextStream([
            'event: content_delta\r\n',
            'data: {"content":"Done"}\r\n\r\n',
            'event: completed\r\n',
            'data: {"response":"Done"}\r\n\r\n',
        ])

        const events = await collectEvents(stream)

        expect(events).toEqual([
            {
                type: 'content_delta',
                content: 'Done',
            },
            {
                type: 'completed',
                response: 'Done',
            },
        ])
    })

    it('should reject an invalid event payload', async () => {
        const stream = createTextStream([
            'event: content_delta\n',
            'data: {"content":42}\n\n',
        ])

        await expect(
            collectEvents(stream),
        ).rejects.toThrow(
            'Invalid chat stream event: content_delta',
        )
    })
})
