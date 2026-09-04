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

## Quality checks

```powershell
npm run lint
npm run build
```

## Backend

The frontend will communicate with the Frank AI Agent FastAPI service running at
http://localhost:8000.
