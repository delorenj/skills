# HTML Project Console Design Principles

1. **One file first**: prefer a self-contained HTML file so any browser can open it.
2. **Data-model driven**: keep mutable project state in one JSON object near the top.
3. **Stable anchors**: fixed section IDs let agents patch targeted regions reliably.
4. **Human legibility**: status colors, badges, and concise cards over long prose.
5. **Bidirectional loop**: include a structured feedback panel to send input back to the agent.
6. **Progressive enhancement**: advanced features (diagrams, diffs) should degrade gracefully.
