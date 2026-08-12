# Session Management

Frank AI Agent sessions use sliding expiration.

Each session has a configurable time-to-live value. When a session remains inactive beyond its configured TTL, it expires and can be removed by the session manager.