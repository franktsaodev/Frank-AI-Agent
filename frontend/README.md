# Frank AI Agent Frontend

React and TypeScript frontend for the Frank AI Agent interactive demo.

## Requirements

- Node.js 24
- npm 11

## Development

Create the local frontend environment file:

```powershell
Copy-Item .env.example .env
```

Install dependencies and start the development server:

```powershell
npm install
npm run dev
```

The development server runs at http://localhost:5173 by default.

## Testing

Run the frontend unit tests once:

```powershell
npm run test
```

Run tests continuously while developing:

```powershell
npm run test:watch
```

Frontend tests use Vitest, jsdom, and React Testing Library.

## Quality checks

Check linting, formatting, and the production build:

```powershell
npm run lint
npm run format:check
npm run build
```

Apply frontend formatting automatically:

```powershell
npm run format
```

## API configuration

For local Vite development, the frontend communicates directly with the
FastAPI service using the URL configured in `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

An empty `VITE_API_BASE_URL` enables same-origin API requests. This mode is
used by the production Docker image, where Nginx proxies `/api` and `/health`
requests to the FastAPI container.

## Streaming chat

The chat interface sends messages using:

```text
POST /api/v1/sessions/{session_id}/chat/stream
```

The frontend consumes the Server-Sent Events response through the Fetch API
and incrementally handles `content_delta`, `completed`, and `error` events.

The stream parser supports events split across network chunks, UTF-8 characters
split across byte boundaries, and both LF and CRLF line endings. HTTP failures,
invalid stream responses, incomplete streams, and server-sent error events are
shown to the user without exposing internal error details.

The backend validates retrieved citations before emitting guarded assistant
content, so streamed content has already passed the application's citation
safety checks.

## Docker

From the project root, build and start the frontend and API services:

```powershell
docker compose up --build -d
```

Check both container health states:

```powershell
docker compose ps
```

The containerized frontend is available at:

```text
http://localhost:5173
```

The frontend image uses a multi-stage build. Node.js builds the React
application, and the generated static assets are copied into a lightweight
Nginx image.
