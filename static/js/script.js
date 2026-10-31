"use strict";

const chatLog = document.querySelector("#chat-log");
const form = document.querySelector("#message-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-button");
const characterCount = document.querySelector("#character-count");
const requestStatus = document.querySelector("#request-status");
const maximumLength = Number(input.maxLength) || 500;
let requestPending = false;
let activeController = null;
let activeRequestId = 0;
let typingIndicator = null;

function scrollToNewest() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function timestamp() {
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date());
}

function addMessage(text, role, category = null) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "YOU" : "EC";

  const body = document.createElement("div");
  body.className = "message-body";
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  body.append(bubble);

  const meta = document.createElement("div");
  meta.className = "message-meta";
  if (category) {
    const categoryLabel = document.createElement("span");
    categoryLabel.className = "message-category";
    categoryLabel.textContent = category;
    meta.append(categoryLabel);
  }
  const time = document.createElement("time");
  time.dateTime = new Date().toISOString();
  time.textContent = timestamp();
  meta.append(time);
  body.append(meta);
  article.append(avatar, body);
  chatLog.append(article);
  scrollToNewest();
}

function addWelcomeMessage() {
  addMessage("Hello! I can help you with admissions, courses, fees, timings, scholarships, facilities, and placements. What would you like to know?", "bot");
}

function showTypingIndicator() {
  typingIndicator = document.createElement("div");
  typingIndicator.className = "message bot typing-message";
  typingIndicator.setAttribute("role", "status");
  typingIndicator.setAttribute("aria-label", "The assistant is typing");
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "EC";
  const bubble = document.createElement("div");
  bubble.className = "message-bubble typing-bubble";
  for (let index = 0; index < 3; index += 1) {
    bubble.append(document.createElement("span"));
  }
  typingIndicator.append(avatar, bubble);
  chatLog.append(typingIndicator);
  scrollToNewest();
}

function removeTypingIndicator() {
  typingIndicator?.remove();
  typingIndicator = null;
}

function updateCharacterCount() {
  characterCount.textContent = `${input.value.length} / ${maximumLength}`;
}

async function sendMessage(rawMessage) {
  const message = rawMessage.trim();
  if (!message || requestPending) return;
  if (message.length > maximumLength) {
    requestStatus.textContent = `Please keep your message to ${maximumLength} characters or fewer.`;
    input.focus();
    return;
  }

  requestPending = true;
  activeController = new AbortController();
  const controller = activeController;
  const requestId = ++activeRequestId;
  sendButton.disabled = true;
  requestStatus.textContent = "";
  addMessage(message, "user");
  input.value = "";
  updateCharacterCount();
  showTypingIndicator();
  input.focus();

  const timeoutId = window.setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ message }),
      signal: controller.signal,
    });
    let payload;
    try {
      payload = await response.json();
    } catch (_error) {
      throw new Error("The server returned an unreadable response. Please try again.");
    }
    if (requestId !== activeRequestId) return;
    if (!response.ok) {
      throw new Error(payload && typeof payload.error === "string" ? payload.error : "The request could not be completed.");
    }
    if (!payload || typeof payload.reply !== "string" || typeof payload.type !== "string") {
      throw new Error("The server returned an unexpected response. Please try again.");
    }
    removeTypingIndicator();
    addMessage(payload.reply, "bot", typeof payload.category === "string" ? payload.category : null);
  } catch (error) {
    if (requestId !== activeRequestId) return;
    removeTypingIndicator();
    if (error.name === "AbortError") {
      addMessage("This request took too long. Please check your connection and try again.", "bot");
    } else {
      addMessage(error.message || "I could not reach the college enquiry service. Please try again.", "bot");
    }
  } finally {
    window.clearTimeout(timeoutId);
    if (requestId === activeRequestId) {
      removeTypingIndicator();
      requestPending = false;
      activeController = null;
      sendButton.disabled = false;
    }
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  void sendMessage(input.value);
});

input.addEventListener("input", updateCharacterCount);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => void sendMessage(button.textContent));
});

clearButton.addEventListener("click", () => {
  activeRequestId += 1;
  activeController?.abort();
  activeController = null;
  requestPending = false;
  sendButton.disabled = false;
  removeTypingIndicator();
  requestStatus.textContent = "";
  chatLog.replaceChildren();
  addWelcomeMessage();
  input.focus();
});

addWelcomeMessage();
updateCharacterCount();