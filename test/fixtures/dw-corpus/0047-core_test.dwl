%dw 2.0
---
{name: "test", (status: payload.status) if payload.status?}