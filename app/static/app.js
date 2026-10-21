// Landing page (spec 0001, R-10): asks the server once whether the system is ready.
// Display only: the readiness decision is the server's (docs/architecture.md, rule 5).

const READY_URL = "/api/health/ready";
const TIMEOUT_MS = 5000;
const MESSAGES = {
  ready: "Sistem çalışıyor",
  unavailable: "Sisteme şu an ulaşılamıyor",
};

async function isSystemReady() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(READY_URL, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    return response.ok;
  } catch {
    // Network failure or timeout: both mean the system cannot be reached right now.
    return false;
  } finally {
    clearTimeout(timer);
  }
}

const statusElement = document.getElementById("system-status");
const state = (await isSystemReady()) ? "ready" : "unavailable";
statusElement.textContent = MESSAGES[state];
statusElement.dataset.state = state;
