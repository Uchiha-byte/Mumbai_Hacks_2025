const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

const statusText = document.getElementById("statusText");
const toggleButton = document.getElementById("toggleButton");
const scanNowButton = document.getElementById("scanNowButton");
const resultText = document.getElementById("resultText");
const resultCard = document.getElementById("resultCard");
const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const saveApiButton = document.getElementById("saveApiButton");

function clearResultStateClasses() {
  resultText.classList.remove("scanning", "error");
  resultCard.classList.remove("result-fake", "result-verified", "result-suspect", "result-mixed");
}

function renderState(enabled) {
  statusText.textContent = enabled ? "Auto scan: ON" : "Auto scan: OFF";
  toggleButton.textContent = enabled ? "Turn OFF" : "Turn ON";
  toggleButton.classList.toggle("is-on", enabled);
}

function renderResult(lastResult) {
  clearResultStateClasses();
  if (!lastResult || !lastResult.verdict) {
    resultText.textContent = "No scan result yet.";
    return;
  }
  const headingSegment = lastResult.heading ? ` | ${lastResult.heading}` : "";
  resultText.textContent = `${lastResult.verdict} (${lastResult.confidence}%)${headingSegment}`;

  const verdict = String(lastResult.verdict || "").toUpperCase();
  if (verdict === "FAKE") resultCard.classList.add("result-fake");
  else if (verdict === "VERIFIED") resultCard.classList.add("result-verified");
  else if (verdict === "SUSPECT") resultCard.classList.add("result-suspect");
  else if (verdict === "MIXED") resultCard.classList.add("result-mixed");
}

async function loadSettings() {
  const { enabled = true, apiBaseUrl = DEFAULT_API_BASE_URL, lastResult = null } =
    await chrome.storage.local.get(["enabled", "apiBaseUrl", "lastResult"]);
  renderState(enabled);
  renderResult(lastResult);
  apiBaseUrlInput.value = apiBaseUrl;
}

toggleButton.addEventListener("click", async () => {
  const { enabled = true } = await chrome.storage.local.get(["enabled"]);
  const next = !enabled;
  await chrome.storage.local.set({ enabled: next });
  renderState(next);
});

saveApiButton.addEventListener("click", async () => {
  const value = apiBaseUrlInput.value.trim() || DEFAULT_API_BASE_URL;
  await chrome.storage.local.set({ apiBaseUrl: value });
  statusText.textContent = "Backend URL saved";
  setTimeout(() => {
    chrome.storage.local.get(["enabled"], ({ enabled = true }) => {
      renderState(enabled);
    });
  }, 900);
});

scanNowButton.addEventListener("click", async () => {
  scanNowButton.disabled = true;
  clearResultStateClasses();
  resultText.classList.add("scanning");
  resultText.textContent = "Scanning current page...";
  try {
    const response = await chrome.runtime.sendMessage({ type: "POPUP_MANUAL_SCAN" });
    if (!response || !response.ok) {
      clearResultStateClasses();
      resultText.classList.add("error");
      resultText.textContent = `Scan failed: ${response && response.error ? response.error : "Unknown error"}`;
      return;
    }
    const latest = await chrome.storage.local.get(["lastResult"]);
    renderResult(latest.lastResult);
  } catch (error) {
    clearResultStateClasses();
    resultText.classList.add("error");
    resultText.textContent = `Scan failed: ${error.message || "Unknown error"}`;
  } finally {
    scanNowButton.disabled = false;
  }
});

loadSettings();
