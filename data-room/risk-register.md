# Risk Register

Every external dependency has a graceful fallback, so the live demo cannot fail.

| Risk | Impact | Mitigation / fallback |
|------|--------|-----------------------|
| MQTT broker unreachable on stage | No live fault trigger | Dashboard "Simulate fault" button fires the same pipeline in-app. |
| WhatsApp/Twilio not configured or down | Work order not delivered | In-app notification path returns the message; nothing blocks. |
| Cloud Qdrant unavailable | No retrieval | Local on-disk Qdrant storage fallback. |
| LLM API slow or rate-limited | Slow diagnosis | Seeded scenarios and pre-populated metrics keep the demo moving. |
| Arabic PDF rendering issue | No PDF | PDF is best-effort; dispatch and on-screen work order still proceed. |
| Network fully down | Cloud calls fail | Local Qdrant + seeded data allow an offline dashboard walkthrough. |

## Product risks (beyond the demo)

- Manual quality varies: retrieval grounds answers and cites sources; low
  confidence is surfaced for human review.
- Adoption trust: MCP keeps proprietary manuals on-premise, removing the main
  blocker to using AI on plant documentation.
