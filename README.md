# Open Webui Enhancements

This repository contains custom functions and tools for Open WebUI.

## Contents

### Tools

*   **Lookup**: [lookup.py](tools/lookup.py) - A web search tool that uses a SearXNG instance to retrieve information from the web.
*   **Remember**: [remember.py](tools/remember.py) - A tool that allows the LLM to update the user's memory list, including adding new memories and consolidating existing ones.

### Functions

*   **Memory Injection Filter**: [Memory-Injection-Filter.py](functions/Memory-Injection-Filter.py) - Injects user memories into the system prompt, allowing selection of which model has access to memories, even if the user's memories setting is off.
*   **Native Tool Call Formatting Outlet**: [Native-tool-call-formatting-outlet.py](functions/Native-tool-call-formatting-outlet.py) - Simplifies the `<details>` tag in native tool call responses to avoid confusing the model in subsequent messages.
*   **Reasoning Injection Filter**: [Reasoning-injection.py](functions/Reasoning-injection.py) - Emits a "Thinking..." event on inlet, then updates it with the elapsed time (in sec or min/sec) when the first stream chunk arrives.

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
