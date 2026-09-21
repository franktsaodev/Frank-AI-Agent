import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MessageContent } from './MessageContent'

describe('MessageContent', () => {
    it('should render ordinary message content', () => {
        render(<MessageContent content="Hello from Frank AI Agent." />)

        expect(
            screen.getByText('Hello from Frank AI Agent.'),
        ).toBeInTheDocument()

        expect(
            screen.queryByTitle('Verified retrieval source'),
        ).not.toBeInTheDocument()
    })

    it('should render a verified source as a citation badge', () => {
        render(
            <MessageContent
                content={
                    'Sessions use sliding expiration. ' +
                    '[Source: knowledge/session.md]'
                }
            />,
        )

        const citationBadge = screen.getByLabelText(
            'Verified citation: Source: knowledge/session.md',
        )

        expect(citationBadge).toBeInTheDocument()
        expect(citationBadge).toHaveTextContent('Source: knowledge/session.md')
    })

    it('should render multiple citation badges', () => {
        render(
            <MessageContent
                content={
                    'Architecture and deployment details. ' +
                    '[Source: knowledge/architecture.pdf (page 1)] ' +
                    '[Source: knowledge/deployment.txt]'
                }
            />,
        )

        const citationBadges = screen.getAllByTitle('Verified retrieval source')

        expect(citationBadges).toHaveLength(2)
        expect(citationBadges[0]).toHaveTextContent(
            'Source: knowledge/architecture.pdf (page 1)',
        )
        expect(citationBadges[1]).toHaveTextContent(
            'Source: knowledge/deployment.txt',
        )
    })

    it('should leave malformed citations as ordinary text', () => {
        render(<MessageContent content="Unverified result [source:1]" />)

        expect(
            screen.getByText('Unverified result [source:1]'),
        ).toBeInTheDocument()

        expect(
            screen.queryByTitle('Verified retrieval source'),
        ).not.toBeInTheDocument()
    })
})
