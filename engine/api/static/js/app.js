const NODE_AGENT_MAP_INTERNAL = {
  requirement: "Requirement Agent",
  image_fetch: "Image Fetcher Agent",
  generate: "Compose Generator",
  validate: "Validator",
  approval: "Approval",
  execute: "Executor",
};

class InfraPilotApp {
  constructor() {
    this.state = "landing";
    this.sessionId = null;
    this.session = null;
    this.api = new ApiClient();
    this.pollTimer = null;
    this.typewriterStop = null;
    this.monacoEditor = null;
    this.agents = [
      { id: "requirement", name: "Requirement Agent", desc: "Converting natural language to ProvisioningSpec", status: "pending" },
      { id: "image_fetch", name: "Image Fetcher Agent", desc: "Discovering Docker Hub images and tags", status: "pending" },
      { id: "generate", name: "Compose Generator", desc: "Generating docker-compose.yml from spec", status: "pending" },
      { id: "validate", name: "Validator", desc: "Validating compose configuration", status: "pending" },
      { id: "execute", name: "Executor", desc: "Deploying infrastructure", status: "pending" },
    ];
    this.toolEvents = [];
    this.interruptValue = null;
    this._lastAgent = null;
    this._lastActiveNode = null;

    this.init();
  }

   init() {
     this.initBackground();
     this.initTheme();
     this.renderExamples();
     this.startRotatingText();
     this.bindLandingEvents();
     this.bindResultEvents();
     this.bindComposeActions();
     this.bindApprovalEvents();
     this.bindThemeToggle();
     this.bindErrorEvents();
   }

   /* ===== Background Atmosphere ===== */

   initBackground() {
     const orbsContainer = document.getElementById("bg-orbs");
     const particlesContainer = document.getElementById("bg-particles");
     if (orbsContainer) createOrbs(orbsContainer, 6);
     if (particlesContainer) createParticleField(particlesContainer, 30);
   }

   /* ===== Theme ===== */

   initTheme() {
     const html = document.documentElement;
     const saved = localStorage.getItem("theme");
     const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
     const initial = saved || (prefersDark ? "dark" : "light");
     html.setAttribute("data-theme", initial);
     this.updateThemeIcon(initial);
   }

   updateThemeIcon(theme) {
     const icon = document.querySelector(".theme-icon");
     if (icon) icon.textContent = theme === "dark" ? "☀️" : "🌙";
   }

   bindThemeToggle() {
     const toggle = document.getElementById("theme-toggle");
     if (!toggle) return;
     toggle.addEventListener("click", () => {
       const html = document.documentElement;
       const current = html.getAttribute("data-theme") || "light";
       const next = current === "light" ? "dark" : "light";
       html.setAttribute("data-theme", next);
       localStorage.setItem("theme", next);
       this.updateThemeIcon(next);
     });
   }

  /* ===== View Management ===== */

  showView(viewName) {
    this.state = viewName;
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    const screen = document.getElementById(`${viewName}-screen`);
    if (screen) screen.classList.add("active");
  }

   showLanding() {
     this.showView("landing");
     if (this.typewriterStop) this.typewriterStop();
     const promptInput = document.getElementById("prompt-input");
     if (promptInput) promptInput.value = "";
     const generateBtn = document.getElementById("generate-btn");
      if (generateBtn) generateBtn.disabled = true;
      this.hidePromptContext();
    }

   /* ===== Prompt Context ===== */

   showPromptContext(prompt) {
     const ctx = document.getElementById("prompt-context");
     const text = document.getElementById("prompt-text");
     if (ctx && text) {
       text.textContent = prompt;
       ctx.classList.remove("hidden");
     }
   }

   hidePromptContext() {
     const ctx = document.getElementById("prompt-context");
     if (ctx) ctx.classList.add("hidden");
   }

   startGenerating() {
    this.showView("generation");
    this.resetTimeline();
    this.clearToolEvents();
    document.getElementById("status-badge").textContent = "Processing";
    document.getElementById("status-badge").className = "status-badge processing";
    this.hideCompose();
    this.hideValidation();
    this.hideApproval();
  }

  showResult(finalState) {
    this.showView("result");
    const card = document.getElementById("result-card");
    const title = document.getElementById("result-title");
    const desc = document.getElementById("result-desc");
    const icon = document.getElementById("result-icon");

    if (finalState.error) {
      card.className = "result-card failed";
      icon.textContent = "✗";
      title.textContent = "Provisioning Failed";
      desc.textContent = finalState.error || "An error occurred during provisioning.";
    } else if (finalState.status === "completed") {
      const exec = finalState.execution_result || {};
      if (exec.success) {
        card.className = "result-card completed";
        icon.textContent = "✓";
        title.textContent = "Provisioning Complete";
        desc.textContent = "Your infrastructure has been deployed successfully.";
      } else {
        card.className = "result-card failed";
        icon.textContent = "⚠";
        title.textContent = "Execution Completed";
        desc.textContent =
          (exec.errors && exec.errors[0]) ||
          "Provisioning pipeline completed but execution encountered issues.";
      }
    } else {
      card.className = "result-card failed";
      icon.textContent = "✗";
      title.textContent = "Cancelled";
      desc.textContent = "Provisioning was cancelled.";
    }
  }

  /* ===== Landing Page ===== */

  renderExamples() {
     const container = document.getElementById("example-library");
     container.innerHTML = "";
      EXAMPLE_PROMPTS.forEach((ex, i) => {
        const card = document.createElement("div");
        card.className = "example-card";
        card.innerHTML = `
          <div class="card-title">${ex.title}</div>
          <div class="card-description">${ex.description}</div>
        `;
       card.style.animationDelay = `${i * 0.1}s`;
       card.addEventListener("click", () => {
         const promptInput = document.getElementById("prompt-input");
         promptInput.value = ex.prompt;
         promptInput.dispatchEvent(new Event("input", { bubbles: true }));
       });
       container.appendChild(card);
     });
   }

  startRotatingText() {
    const el = document.getElementById("rotating-prompt");
    if (el) {
      this.typewriterStop = typewriterCycle(el, ROTATING_PROMPTS);
    }
  }

  bindLandingEvents() {
    const generateBtn = document.getElementById("generate-btn");
    const promptInput = document.getElementById("prompt-input");

    const checkPrompt = () => {
      const hasText = promptInput.value.trim().length > 0;
      generateBtn.disabled = !hasText;
    };

    promptInput.addEventListener("input", checkPrompt);
    checkPrompt();

    generateBtn.addEventListener("click", () => {
      const prompt = promptInput.value.trim();
      if (!prompt) return;
      this.startProvision(prompt);
    });

    promptInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!generateBtn.disabled) generateBtn.click();
      }
    });
  }

  startProvision(prompt) {
    if (this.typewriterStop) this.typewriterStop();
    this.showPromptContext(prompt);
    this.startGenerating();
    this.api.startProvision({ user_request: prompt })
      .then((resp) => {
        this.sessionId = resp.session_id;
        this.connectSSE();
        this.startPolling();
      })
      .catch((err) => {
        this.showError(err.message);
      });
  }

  /* ===== SSE + Polling ===== */

  connectSSE() {
    if (!this.sessionId) return;

    this.api.subscribeToEvents(
      this.sessionId,
      (event) => this.handleSseEvent(event),
      () => this.startPolling() // fallback to polling on SSE error
    );
  }

  startPolling() {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = setInterval(async () => {
      try {
        const session = await this.api.getSession(this.sessionId);
        if (!session) return;
        if (session.status === this.session?.status) return;
        this.handleSessionUpdate(session);
      } catch (err) {
        console.warn("Polling error:", err);
      }
    }, 2000);
  }

  stopPolling() {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = null;
  }

  stopSSE() {
    if (this.api) this.api.closeEvents();
  }

  reconnectSSE() {
    this.stopSSE();
    this.connectSSE();
  }

  /* ===== Event Handling ===== */

  handleSseEvent(event) {
    const type = event.type;

    switch (type) {
      case "status":
        this.updateStatus(event.status);
        if (event.status === "completed" || event.status === "failed") {
          if (event.error) {
            this.showProvisioningError(event.error);
          }
          this.stopPolling();
          this.showResultView({
            status: event.status,
            error: event.error,
            execution_result: this.session?.execution_result || null,
          });
        }
        break;
      case "agent_start":
        this.updateAgent(event.agent, "running");
        this.updateAgentDetails(event.agent, "Running...");
        break;
      case "agent_end":
        this.updateAgent(event.agent, "completed");
        if (event.node) {
          this._lastActiveNode = event.node;
        }
        if (event.output) {
          this.updateAgentDetails(event.agent, event.output.slice(0, 300));
        } else {
          this.updateAgentDetails(event.agent, "Completed");
        }
        break;
      case "tool_start":
        this.addToolEvent(event);
        break;
      case "tool_end":
        this.updateToolEvent(event);
        this.updateAgentDetails(
          this._lastAgent || "Agent",
          "Completed\n" + (event.output ? String(event.output).slice(0, 200) : "")
        );
        break;
      case "interrupt":
        this.interruptValue = event.value;
        this.stopPolling();
        this.stopSSE();
        this.handleSessionUpdate(
          this.sessionApiFormat("awaiting_approval", event.value)
        );
        break;
      case "error":
        this.stopPolling();
        this.stopSSE();
        this.showProvisioningError(event.message);
        break;
    }
  }

  handleSessionUpdate(session) {
    this.session = session;
    const prevStatus = this.session?.status;

    if (session.status === "processing") return;
    if (session.status === "awaiting_approval") {
      this.stopPolling();
      this.showReviewView(session);
    } else if (session.status === "completed") {
      this.stopPolling();
      this.showResultView(session);
    } else if (session.status === "failed") {
      this.stopPolling();
      this.showProvisioningError(session.error || "Unknown error");
    }
  }

  sessionApiFormat(status, interruptValue) {
    return {
      session_id: this.sessionId,
      status,
      project_name: interruptValue?.provision_spec
        ? interruptValue.provision_spec.services?.[0]?.name
        : undefined,
      provision_spec: interruptValue?.provision_spec || null,
      generated_config: interruptValue?.generated_config || null,
      validation_result: {
        success: interruptValue?.validation_success ?? null,
        errors: interruptValue?.validation_errors || [],
      },
      approved: null,
      execution_result: null,
      error: null,
    };
  }

  /* ===== View: Review ===== */

  showReviewView(session) {
    document.getElementById("status-badge").textContent = "Awaiting Approval";
    document.getElementById("status-badge").className = "status-badge awaiting";

    if (session.generated_config) {
      this.showCompose(session.generated_config);
    }

    if (session.validation_result) {
      this.showValidation(session.validation_result);
    }

    this.showApproval();
  }

  /* ===== View: Result ===== */

   showResultView(session) {
     this.hidePromptContext();
     this.showResult(session);
   }

  /* ===== Agent Timeline ===== */

  resetTimeline() {
    this.agents.forEach((a) => (a.status = "pending"));
    this._lastAgent = null;
    this._lastActiveNode = null;
    this.toolEvents = [];
    const container = document.getElementById("agent-timeline");
    container.innerHTML = "";
    this.agents.forEach((agent, i) => {
      const el = this.createAgentNode(agent, i, this.agents.length);
      container.appendChild(el);
    });
    document.getElementById("tool-events").innerHTML = "";
  }

  createAgentNode(agent, index, total) {
    const div = document.createElement("div");
    div.className = "timeline-node pending";
    div.dataset.agent = agent.id;
    div.innerHTML = `
      <div class="node-icon">
        <div class="spinner"></div>
        <div class="checkmark-container">
          <svg viewBox="0 0 24 24">
            <path d="M5 13l4 4L19 7" />
          </svg>
        </div>
      </div>
      <div class="node-content">
        <h3>${agent.name}</h3>
        <p>${agent.desc}</p>
        <div class="agent-details">
          <details>
            <summary>Agent output</summary>
            <pre id="details-${agent.id}">Waiting for output...</pre>
          </details>
        </div>
      </div>
    `;
    return div;
  }

   updateAgent(agentName, status) {
     if (status === "running") {
       this._lastAgent = agentName;
     }
     const mappedId = Object.keys(NODE_AGENT_MAP_INTERNAL).find(
      (k) => NODE_AGENT_MAP_INTERNAL[k] === agentName
    );
    const node = mappedId
      ? document.querySelector(`.timeline-node[data-agent="${mappedId}"]`)
      : null;

    if (!node) {
      const allNodes = document.querySelectorAll(".timeline-node");
      for (const n of allNodes) {
        if (n.querySelector("h3").textContent === agentName) {
          node = n;
          break;
        }
      }
    }

    if (!node) return;

    node.className = `timeline-node ${status}`;

    if (status === "completed") {
      const spinner = node.querySelector(".spinner");
      if (spinner) spinner.style.display = "none";
      const checkmark = node.querySelector(".checkmark-container");
      if (checkmark) {
        checkmark.style.display = "block";
        const path = checkmark.querySelector("path");
        if (path) {
          path.style.animation = "none";
          void path.offsetWidth;
          path.style.animation = "drawCheck 0.5s ease-in-out forwards";
        }
      }
    }
  }

  updateAgentDetails(agentName, content) {
    // Update details text if we have output
    const nodes = document.querySelectorAll(".timeline-node");
    nodes.forEach((node) => {
      const h3 = node.querySelector("h3");
      if (h3 && h3.textContent === agentName) {
        const detailsPre = node.querySelector("pre");
        if (detailsPre && content) {
          detailsPre.textContent = typeof content === "string" ? content : JSON.stringify(content, null, 2);
        }
      }
    });
  }

  /* ===== Tool Execution ===== */

  addToolEvent(event) {
    const section = document.getElementById("tool-section");
    if (section) section.classList.remove("hidden");
    this.toolEvents.push({ type: "start", ...event });
    const container = document.getElementById("tool-events");
    const div = document.createElement("div");
    div.className = "tool-event";
    div.dataset.tool = event.tool;
    div.style.setProperty("--i", this.toolEvents.filter((e) => e.type === "start").length - 1);
    div.innerHTML = `
      <div class="tool-header">
        <span class="tool-name">${this.prettyToolName(event.tool)}</span>
        <span class="tool-input">{ ${JSON.stringify(event.input).slice(0, 80)} }</span>
      </div>
      <div class="tool-results" id="results-${event.tool}-${Date.now()}">
        <span class="tool-result" style="opacity: 0.5">Discovering...</span>
      </div>
    `;
    div.classList.add("appear");
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  updateToolEvent(event) {
    const events = document.querySelectorAll(".tool-event");
    let target = null;
    events.forEach((el) => {
      if (el.dataset.tool === event.tool) target = el;
    });

    if (!target) {
      this.addToolEvent({ type: "end", ...event });
      return;
    }

    const resultsDiv = target.querySelector(".tool-results");
    if (resultsDiv && event.output) {
      let items = [];
      try {
        const parsed = JSON.parse(event.output);
        if (Array.isArray(parsed)) {
          items = parsed.map((p) => p.repository || p.name || JSON.stringify(p));
        } else if (parsed.repository || parsed.name) {
          items = [parsed.repository || parsed.name];
        }
      } catch {
        items = [event.output.toString().slice(0, 100)];
      }

      items.forEach((item, i) => {
        setTimeout(() => {
          const span = document.createElement("span");
          span.className = "tool-result";
          span.textContent = item;
          if (i === 0) span.classList.add("highlight");
          resultsDiv.appendChild(span);
        }, i * 200);
      });
    }

    target.querySelector(".tool-result").textContent = "Done ✓";
  }

  prettyToolName(tool) {
    const map = {
      search_repository: "Docker Hub Search",
      list_tags: "List Tags",
    };
    return map[tool] || tool;
  }

  clearToolEvents() {
    const container = document.getElementById("tool-events");
    if (container) container.innerHTML = "";
    const section = document.getElementById("tool-section");
    if (section) section.classList.add("hidden");
    this.toolEvents = [];
  }

  /* ===== Compose Viewer ===== */

  showCompose(yamlContent) {
    const viewer = document.getElementById("compose-viewer");
    viewer.classList.remove("hidden");

    const lineCountEl = document.getElementById("compose-line-count");
    if (lineCountEl) {
      lineCountEl.textContent = yamlContent ? yamlContent.split("\n").length : 0;
    }

    const container = document.getElementById("monaco-container");
    if (container) container.style.display = "block";

    if (!this.monacoEditor) {
      initMonaco(document.getElementById("monaco-container"), yamlContent).then(
        (editor) => {
          this.monacoEditor = editor;
        }
      );
    } else {
      this.monacoEditor.setValue(yamlContent || "");
    }
  }

  hideCompose() {
    const viewer = document.getElementById("compose-viewer");
    viewer.classList.add("hidden");
    const lineCountEl = document.getElementById("compose-line-count");
    if (lineCountEl) lineCountEl.textContent = "0";
    const container = document.getElementById("monaco-container");
    if (container) container.style.display = "none";
  }

  bindComposeActions() {
    const copyBtn = document.getElementById("copy-compose");
    const downloadBtn = document.getElementById("download-compose");

    copyBtn?.addEventListener("click", () => {
      const content = getEditorValue();
      navigator.clipboard.writeText(content).then(() => {
        copyBtn.innerHTML = '<span style="color:#10b981">✓</span>';
        setTimeout(() => {
          copyBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12a2 2 0 0 0 0-4z M16 5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h8z"/></svg>';
        }, 1500);
      });
    });

    downloadBtn?.addEventListener("click", () => {
      const content = getEditorValue();
      const blob = new Blob([content], { type: "text/yaml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "docker-compose.yml";
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  /* ===== Validation Panel ===== */

  showValidation(validation) {
    const panel = document.getElementById("validation-panel");
    panel.classList.remove("hidden");
    panel.innerHTML = "";

    if (validation.success) {
      panel.innerHTML = `
        <div class="validation-card success">
          <div class="validation-icon">✓</div>
          <div class="validation-content">
            <h4>Compose Syntax Valid</h4>
            <p>Docker Compose configuration passed validation.</p>
          </div>
        </div>
      `;
    } else {
      panel.innerHTML = `
        <div class="validation-card error">
          <div class="validation-icon">✗</div>
          <div class="validation-content">
            <h4>Validation Failed</h4>
            <p>${validation.errors?.join(", ") || "Configuration errors detected."}</p>
          </div>
        </div>
      `;
    }

    if (validation.warnings && validation.warnings.length > 0) {
      const details = document.createElement("div");
      details.className = "validation-details";
      details.innerHTML = `
        <details>
          <summary>Show warnings (${validation.warnings.length})</summary>
          <pre>${validation.warnings.join("\n")}</pre>
        </details>
      `;
      panel.appendChild(details);
    }
  }

  hideValidation() {
    const panel = document.getElementById("validation-panel");
    panel.classList.add("hidden");
  }

  /* ===== Approval Workflow ===== */

  showApproval() {
    const bar = document.getElementById("approval-bar");
    bar.classList.remove("hidden");
  }

  hideApproval() {
    const bar = document.getElementById("approval-bar");
    bar.classList.add("hidden");
  }

  bindApprovalEvents() {
    document.getElementById("approve-btn")?.addEventListener("click", () => {
      this.sendApproval(true, null);
    });

    document.getElementById("regenerate-btn")?.addEventListener("click", () => {
      document.getElementById("feedback-modal").classList.add("active");
      document.getElementById("feedback-input").value = "";
      setTimeout(() => document.getElementById("feedback-input").focus(), 100);
    });

    document.getElementById("cancel-btn")?.addEventListener("click", () => {
      this.sendApproval(false, null);
    });

    document.getElementById("modal-cancel")?.addEventListener("click", () => {
      document.getElementById("feedback-modal").classList.remove("active");
    });

    document.getElementById("modal-submit")?.addEventListener("click", () => {
      const feedback = document.getElementById("feedback-input").value.trim();
      document.getElementById("feedback-modal").classList.remove("active");
      this.sendApproval(false, feedback || null);
    });
  }

  async sendApproval(approved, feedback) {
    this.stopSSE();
    this.stopPolling();
    this.hideApproval();

    const badge = document.getElementById("status-badge");
    if (badge) {
      badge.textContent = "Restarting";
      badge.className = "status-badge processing";
    }

    try {
      const resp = await this.api.approve(this.sessionId, { approved, feedback });

      this._lastAgent = null;
      this._lastActiveNode = null;
      this.startGenerating();
      this.connectSSE();
      this.startPolling();
    } catch (err) {
      this.showError(err.message);
    }
  }

  /* ===== Error Handling ===== */

  showError(message) {
    const container = document.querySelector(".generation-header");
    if (container) {
      const errorDiv = document.createElement("div");
      errorDiv.className = "validation-card error";
      errorDiv.innerHTML = `
        <div class="validation-icon">⚠</div>
        <div class="validation-content">
          <h4>Error</h4>
          <p>${message}</p>
        </div>
      `;
      container.parentNode.insertBefore(errorDiv, container.nextSibling);
    }
  }

  showProvisioningError(message) {
    this.stopPolling();
    this.api.closeEvents();
    const modal = document.getElementById("error-modal");
    const msgEl = document.getElementById("error-message");
    if (modal && msgEl) {
      msgEl.textContent = message || "An error occurred during provisioning.";
      modal.classList.add("active");
    }
  }

  updateStatus(status) {
    const badge = document.getElementById("status-badge");
    if (!badge) return;
    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    badge.className = "status-badge " + status;
  }

  /* ===== Result Events ===== */

  bindResultEvents() {
    document.getElementById("back-to-landing").addEventListener("click", () => {
      this.showLanding();
    });
  }

  /* ===== Error Events ===== */

  bindErrorEvents() {
    document.getElementById("error-close")?.addEventListener("click", () => {
      this.hideErrorModal();
      this.showLanding();
    });
  }

  hideErrorModal() {
    const modal = document.getElementById("error-modal");
    if (modal) modal.classList.remove("active");
  }

  /* ===== Progress Stepper ===== */
  // Progress stepper removed — vertical agent timeline serves this purpose
}

let app;
document.addEventListener("DOMContentLoaded", () => {
  app = new InfraPilotApp();
});
