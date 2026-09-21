import './MessageContent.css'

interface MessageContentProps {
    content: string
}

const CITATION_PATTERN = /(\[Source: [^\]\r\n]+\])/g

function getCitationLabel(contentPart: string): string | null {
    if (!contentPart.startsWith('[Source: ') || !contentPart.endsWith(']')) {
        return null
    }

    return contentPart.slice(1, -1)
}

export function MessageContent({ content }: MessageContentProps) {
    const contentParts = content.split(CITATION_PATTERN)

    return (
        <>
            {contentParts.map((contentPart, index) => {
                const citationLabel = getCitationLabel(contentPart)

                if (citationLabel === null) {
                    return contentPart
                }

                return (
                    <span
                        className="citation-badge"
                        aria-label={`Verified citation: ${citationLabel}`}
                        title="Verified retrieval source"
                        key={`${citationLabel}-${index}`}
                    >
                        <span
                            className="citation-badge-icon"
                            aria-hidden="true"
                        >
                            ✓
                        </span>

                        {citationLabel}
                    </span>
                )
            })}
        </>
    )
}
