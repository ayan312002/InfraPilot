class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
    this.eventSource = null;
  }

  async startProvision({ user_request, project_name, example_id }) {
    const resp = await fetch(`${this.baseUrl}/provision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_request, project_name, example_id }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  }

  async getSession(sessionId) {
    const resp = await fetch(`${this.baseUrl}/provision/${sessionId}`);
    if (resp.status === 404) return null;
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  }

  async approve(sessionId, { approved, feedback }) {
    const resp = await fetch(`${this.baseUrl}/provision/${sessionId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved, feedback }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
  }

  subscribeToEvents(sessionId, onEvent, onError) {
    this.eventSource = new EventSource(
      `${this.baseUrl}/provision/${sessionId}/events`
    );
    this.eventSource.onmessage = (e) => {
      try {
        onEvent(JSON.parse(e.data));
      } catch {
        console.warn("Unparseable SSE event:", e.data);
      }
    };
    this.eventSource.onerror = () => {
      console.warn("SSE connection error, falling back to polling");
      this.eventSource.close();
      this.eventSource = null;
      if (onError) onError();
    };
    return this.eventSource;
  }

  closeEvents() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
