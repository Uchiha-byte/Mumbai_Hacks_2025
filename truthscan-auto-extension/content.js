(() => {
  const MIN_TEXT_LENGTH = 50;
  const MAX_TEXT_LENGTH = 500;
  const AUTO_SCAN_DELAY_MS = 2500;
  let hasScannedThisPage = false;
  let lastPayload = null;

  function simpleHash(input) {
    let hash = 5381;
    for (let i = 0; i < input.length; i += 1) {
      hash = (hash * 33) ^ input.charCodeAt(i);
    }
    return (hash >>> 0).toString(16);
  }

  function isVisible(element) {
    if (!element) return false;
    const style = window.getComputedStyle(element);
    if (
      style.display === "none" ||
      style.visibility === "hidden" ||
      Number.parseFloat(style.opacity) === 0
    ) {
      return false;
    }
    return element.getClientRects().length > 0;
  }

  function collectTextFromSelectors(selectors) {
    const chunks = [];
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const element of elements) {
        if (!isVisible(element)) continue;
        const text = (element.innerText || "").replace(/\s+/g, " ").trim();
        if (text.length < 20) continue;
        chunks.push(text);
        if (chunks.join(" ").length >= MAX_TEXT_LENGTH * 2) {
          return chunks;
        }
      }
    }
    return chunks;
  }

  function extractMeaningfulContent() {
    const headingElement =
      document.querySelector("article h1, main h1, h1") ||
      document.querySelector("article h2, main h2, h2");
    const primaryHeading = headingElement
      ? (headingElement.innerText || "").replace(/\s+/g, " ").trim()
      : "";

    const preferredChunks = collectTextFromSelectors([
      "article h1, article h2, article h3, article p",
      "main h1, main h2, main h3, main p",
      "h1, h2, h3, p"
    ]);
    const combined = preferredChunks.join(" ").replace(/\s+/g, " ").trim();
    const headingPrefixed = primaryHeading ? `${primaryHeading}. ${combined}` : combined;
    const text = headingPrefixed.slice(0, MAX_TEXT_LENGTH);

    if (text.length < MIN_TEXT_LENGTH) {
      return null;
    }

    const firstVisibleImage = Array.from(document.querySelectorAll("img")).find(
      (img) => isVisible(img) && img.src
    );

    const firstVideo = Array.from(document.querySelectorAll("video")).find(
      (video) => isVisible(video)
    );
    const videoSource =
      (firstVideo && firstVideo.currentSrc) ||
      (firstVideo && firstVideo.src) ||
      null;

    return {
      content: text,
      contentType: "text",
      hash: simpleHash(`${location.href}|${text}`),
      metadata: {
        url: location.href,
        title: document.title,
        heading: primaryHeading || null,
        image: firstVisibleImage ? firstVisibleImage.src : null,
        video: videoSource
      }
    };
  }

  function sendScanPayload(payload, force = false) {
    lastPayload = payload;
    chrome.runtime.sendMessage(
      {
        type: "SCAN_CONTENT",
        payload: {
          content: payload.content,
          content_type: payload.contentType,
          hash: payload.hash,
          metadata: payload.metadata
        },
        force
      },
      (response) => {
        if (chrome.runtime.lastError) {
          console.debug("TruthScan Auto: message send error", chrome.runtime.lastError.message);
          return;
        }
        if (response && response.ok) {
          console.debug("TruthScan Auto: scan success", response.verdict, response.confidence);
        } else if (response && response.error) {
          console.debug("TruthScan Auto: scan failed", response.error);
        }
      }
    );
  }

  function runAutoScan(force = false) {
    if (hasScannedThisPage && !force) return;
    chrome.storage.local.get(["enabled"], (result) => {
      const enabled = result.enabled !== false;
      if (!enabled && !force) return;

      const extracted = extractMeaningfulContent();
      if (!extracted) return;

      hasScannedThisPage = true;
      sendScanPayload(extracted, force);
    });
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || typeof message !== "object") return;
    if (message.type === "FORCE_SCAN") {
      runAutoScan(true);
      sendResponse({ ok: true });
      return;
    }
    if (message.type === "SCAN_NOW") {
      const extracted = extractMeaningfulContent();
      if (!extracted) {
        sendResponse({ ok: false, error: "No meaningful content found on page" });
        return;
      }
      sendScanPayload(extracted, true);
      sendResponse({ ok: true, payload: extracted });
      return;
    }
    if (message.type === "GET_PAGE_SCAN_PAYLOAD") {
      const extracted = extractMeaningfulContent() || lastPayload;
      sendResponse({ ok: Boolean(extracted), payload: extracted || null });
      return;
    }
  });

  window.addEventListener("load", () => {
    window.setTimeout(() => runAutoScan(false), AUTO_SCAN_DELAY_MS);
  });
})();
