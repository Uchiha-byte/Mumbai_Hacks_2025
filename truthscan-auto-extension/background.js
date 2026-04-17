const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const MIN_SCAN_GAP_MS = 10000;
const NOTIFICATION_COOLDOWN_MS = 20000;
const CONFIDENCE_NOTIFICATION_THRESHOLD = 65;
const NOTIFICATION_ICON =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg==";

const lastScanByTab = new Map();
let lastNotificationAt = 0;

function isSupportedPageUrl(url) {
  if (!url || typeof url !== "string") return false;
  return /^https?:\/\//i.test(url);
}

async function getPagePayloadFromTab(tabId) {
  return chrome.tabs.sendMessage(tabId, { type: "GET_PAGE_SCAN_PAYLOAD" });
}

async function ensureContentScriptAndGetPayload(tab) {
  if (!tab || !tab.id) {
    return { ok: false, error: "No active tab available" };
  }
  if (!isSupportedPageUrl(tab.url)) {
    return { ok: false, error: "This page cannot be scanned (open a normal http/https page)." };
  }

  try {
    const existing = await getPagePayloadFromTab(tab.id);
    if (existing && existing.ok && existing.payload) {
      return { ok: true, payload: existing.payload };
    }
  } catch (error) {
    const message = error && error.message ? error.message : "";
    if (!message.includes("Receiving end does not exist")) {
      return { ok: false, error: message || "Failed to contact page scanner" };
    }
  }

  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
  } catch (error) {
    return {
      ok: false,
      error:
        "Could not inject scanner on this page. Chrome internal/restricted pages are not supported."
    };
  }

  try {
    const injected = await getPagePayloadFromTab(tab.id);
    if (injected && injected.ok && injected.payload) {
      return { ok: true, payload: injected.payload };
    }
    return { ok: false, error: "Could not extract meaningful content from this page" };
  } catch (error) {
    return { ok: false, error: "Scanner injection succeeded, but page communication failed" };
  }
}

function getVerdictConfig(verdict) {
  const normalized = (verdict || "").toUpperCase();
  if (normalized === "FAKE") return { badge: "F", color: "#d93025" };
  if (normalized === "VERIFIED") return { badge: "V", color: "#188038" };
  if (normalized === "SUSPECT") return { badge: "?", color: "#f9ab00" };
  if (normalized === "MIXED") return { badge: "M", color: "#5f6368" };
  return { badge: "?", color: "#5f6368" };
}

async function getStorage(keys) {
  return chrome.storage.local.get(keys);
}

async function setStorage(payload) {
  return chrome.storage.local.set(payload);
}

async function updateBadge(tabId, verdict) {
  if (!tabId) return;
  const config = getVerdictConfig(verdict);
  await chrome.action.setBadgeText({ tabId, text: config.badge });
  await chrome.action.setBadgeBackgroundColor({ tabId, color: config.color });
}

async function clearBadge(tabId) {
  if (!tabId) return;
  await chrome.action.setBadgeText({ tabId, text: "" });
}

async function notifyResult(verdict, confidence, url) {
  const now = Date.now();
  if (now - lastNotificationAt < NOTIFICATION_COOLDOWN_MS) return;

  const confidenceValue = Number(confidence) || 0;
  const strongEnough = confidenceValue >= CONFIDENCE_NOTIFICATION_THRESHOLD;
  const concerningVerdict = ["FAKE", "SUSPECT"].includes((verdict || "").toUpperCase());
  if (!strongEnough && !concerningVerdict) return;

  lastNotificationAt = now;
  await chrome.notifications.create({
    type: "basic",
    iconUrl: NOTIFICATION_ICON,
    title: "TruthScan Auto",
    message: `${verdict || "UNKNOWN"} (${confidenceValue}%)`,
    contextMessage: url || "Misinformation scan completed",
    priority: 1
  });
}

async function quickAnalyze(apiBaseUrl, payload) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 9000);
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/quick-analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        content: payload.content,
        content_type: "text",
        metadata: payload.metadata || {}
      }),
      signal: controller.signal
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`API request failed with ${response.status}: ${errorBody}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

async function handleScanRequest(message, sender) {
  const tabId = sender.tab ? sender.tab.id : null;
  const now = Date.now();
  const payload = message.payload || {};

  if (!payload.content || payload.content.length < 50) {
    return { skipped: true, reason: "Content too short" };
  }

  const { enabled = true, lastScannedHash, apiBaseUrl } = await getStorage([
    "enabled",
    "lastScannedHash",
    "apiBaseUrl"
  ]);

  if (!enabled && !message.force) {
    if (tabId) await clearBadge(tabId);
    return { skipped: true, reason: "Auto scan is disabled" };
  }

  if (lastScannedHash && lastScannedHash === payload.hash && !message.force) {
    return { skipped: true, reason: "Duplicate content" };
  }

  if (tabId && lastScanByTab.has(tabId)) {
    const elapsed = now - lastScanByTab.get(tabId);
    if (elapsed < MIN_SCAN_GAP_MS && !message.force) {
      return { skipped: true, reason: "Debounced to reduce API calls" };
    }
  }

  lastScanByTab.set(tabId, now);

  try {
    const result = await quickAnalyze(apiBaseUrl || DEFAULT_API_BASE_URL, payload);
    const verdict = (result.verdict || result.label || "UNKNOWN").toUpperCase();
    const confidence = Math.round(Number(result.confidence || 0));

    await setStorage({
      lastScannedHash: payload.hash || null,
      lastResult: {
        verdict,
        confidence,
        url: payload.metadata && payload.metadata.url ? payload.metadata.url : "",
        heading: payload.metadata && payload.metadata.heading ? payload.metadata.heading : "",
        scannedAt: new Date().toISOString()
      }
    });
    if (tabId) await updateBadge(tabId, verdict);
    await notifyResult(verdict, confidence, payload.metadata && payload.metadata.url);

    return { ok: true, verdict, confidence };
  } catch (error) {
    if (tabId) {
      await chrome.action.setBadgeText({ tabId, text: "!" });
      await chrome.action.setBadgeBackgroundColor({ tabId, color: "#9aa0a6" });
    }
    return { ok: false, error: error.message || "Unknown error" };
  }
}

async function handlePopupManualScan() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const payloadResponse = await ensureContentScriptAndGetPayload(tab);
  if (!payloadResponse.ok) {
    return payloadResponse;
  }
  return handleScanRequest(
    { type: "SCAN_CONTENT", payload: payloadResponse.payload, force: true },
    { tab }
  );
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message !== "object") return;

  if (message.type === "SCAN_CONTENT") {
    handleScanRequest(message, sender)
      .then((result) => sendResponse(result))
      .catch((error) =>
        sendResponse({ ok: false, error: error.message || "Unhandled failure" })
      );
    return true;
  }
  if (message.type === "POPUP_MANUAL_SCAN") {
    handlePopupManualScan()
      .then((result) => sendResponse(result))
      .catch((error) =>
        sendResponse({ ok: false, error: error.message || "Manual scan failed unexpectedly" })
      );
    return true;
  }
});

chrome.runtime.onInstalled.addListener(async () => {
  const current = await getStorage(["enabled", "apiBaseUrl"]);
  if (typeof current.enabled !== "boolean") {
    await setStorage({ enabled: true });
  }
  if (!current.apiBaseUrl) {
    await setStorage({ apiBaseUrl: DEFAULT_API_BASE_URL });
  }

  chrome.contextMenus.create({
    id: "truthscan-manual-scan",
    title: "Scan with TruthScan",
    contexts: ["page"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "truthscan-manual-scan" && tab && tab.id) {
    ensureContentScriptAndGetPayload(tab).then((payloadResponse) => {
      if (!payloadResponse.ok) return;
      handleScanRequest(
        { type: "SCAN_CONTENT", payload: payloadResponse.payload, force: true },
        { tab }
      );
    });
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === "loading") {
    clearBadge(tabId);
  }
});
