const BACKEND_URL = "https://adaptive-rag-chatbot-2.onrender.com";

const sessionIdEl = document.getElementById("session-id");
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const fileInput = document.getElementById("file-input");
const uploadStatusEl = document.getElementById("upload-status");
const resetBtn = document.getElementById("reset-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const backendStatusEl = document.getElementById("backend-status");
const routeIndicatorEl = document.getElementById("route-indicator");
const chatListEl = document.getElementById("chat-list");

let messages = [];
let sessionId = crypto.randomUUID();

// In-memory map of conversations for this browser tab
// { [sessionId]: { title: string, messages: [{role, content}] } }
const conversations = {};

function setSession(id) {
  sessionId = id;
  sessionIdEl.textContent = id;
}

setSession(sessionId);
conversations[sessionId] = { title: "New chat", messages: [] };

async function checkBackend() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (!res.ok) throw new Error("health failed");
    const data = await res.json();
    backendStatusEl.textContent = `OK · vectors: ${data.vector_backend}${data.mongo_connected ? " · mongo" : ""}`;
    backendStatusEl.classList.remove("bg-red-900", "text-red-200");
    backendStatusEl.classList.add("bg-green-900", "text-green-200");
  } catch {
    backendStatusEl.textContent = "Backend unavailable";
    backendStatusEl.classList.remove("bg-green-900", "text-green-200");
    backendStatusEl.classList.add("bg-red-900", "text-red-200");
  }
}

checkBackend();

function renderChatList() {
  if (!chatListEl) return;
  chatListEl.innerHTML = "";
  Object.entries(conversations).forEach(([id, conv]) => {
    const item = document.createElement("button");
    const active = id === sessionId;
    item.type = "button";
    item.className =
      "w-full text-left px-2 py-1.5 rounded-lg border text-xs truncate " +
      (active
        ? "bg-indigo-600/80 border-indigo-400 text-white"
        : "bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800");
    item.textContent = conv.title || "Untitled chat";
    item.onclick = () => switchChat(id);
    chatListEl.appendChild(item);
  });
}

function switchChat(id) {
  if (!conversations[id]) {
    conversations[id] = { title: "New chat", messages: [] };
  }
  sessionId = id;
  sessionIdEl.textContent = id;
  messages = conversations[id].messages.slice();
  messagesEl.innerHTML = "";
  messages.forEach((m) => renderMessageBubble(m.role, m.content));
  routeIndicatorEl.textContent = "Ready";
  renderChatList();
}

function generateSmartTitle(text) {
  let cleaned = text.trim();

  // remove common useless words
  cleaned = cleaned.replace(/^(hi|hello|hey|ok|okay|no|yes)\s*/i, "");

  // remove question starters
  cleaned = cleaned.replace(/^(what|how|why|is|are|can|do)\s+/i, "");

  // capitalize first letter
  cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);

  // fallback if empty
  if (!cleaned) return "New Chat";

  return cleaned.length > 35 ? cleaned.slice(0, 35) + "…" : cleaned;
}

function updateChatTitleFromMessage(id, text) {
  const conv = conversations[id];
  if (!conv) return;

  const badTitles = ["new chat", "hi", "hello", "ok", "no", "yes"];

  if (!conv.title || badTitles.includes(conv.title.toLowerCase())) {
    conv.title = generateSmartTitle(text);
  }
  }

function addMessage(role, content) {
  const msg = { role, content };
  messages.push(msg);
  if (!conversations[sessionId]) {
    conversations[sessionId] = { title: "New chat", messages: [] };
  }
  conversations[sessionId].messages.push(msg);
  renderMessageBubble(role, content);
  renderChatList();
}

function renderMessageBubble(role, content) {
  const wrapper = document.createElement("div");
  wrapper.className = "flex";
  wrapper.innerHTML = `
    <div class="flex-1 max-w-full ${role === "user" ? "ml-auto" : "mr-auto"}">
      <div class="text-[11px] mb-1 ${role === "user" ? "text-indigo-300 text-right" : "text-amber-300"}">
        ${role === "user" ? "You" : "Assistant"}
      </div>
      <div class="inline-block px-3 py-2 rounded-2xl text-sm leading-relaxed break-words ${
        role === "user"
          ? "bg-indigo-600 text-white rounded-br-sm shadow-lg"
          : "bg-gray-800 text-gray-100 border border-gray-700 rounded-bl-sm"
      }">
        ${content}
      </div>
    </div>
  `;
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Initial render of chat list
renderChatList();

async function sendMessage(text) {
  if (!text.trim()) return;
  addMessage("user", text);
  updateChatTitleFromMessage(sessionId, text);
  chatInput.value = "";

  sendBtn.disabled = true;
  sendBtn.textContent = "Thinking…";
  routeIndicatorEl.textContent = "Routing…";

  try {
    const recent = messages.slice(-10);
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        history_limit: 50,
        messages: recent,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const answer = data.answer || "(no answer)";
    const route = data.route || "general";

    addMessage("assistant", answer);
    routeIndicatorEl.textContent = `Route: ${route}`;
  } catch (err) {
    addMessage("assistant", "Request failed. Please check the backend logs.");
    console.error(err);
    routeIndicatorEl.textContent = "Error";
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send";
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(chatInput.value);
});

// Allow Enter to send, Shift+Enter for newline
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(chatInput.value);
  }
});

fileInput.addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;

  uploadStatusEl.textContent = "Uploading and ingesting…";
  uploadStatusEl.classList.remove("text-green-300", "text-red-300");
  uploadStatusEl.classList.add("text-gray-300");

  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("file", file);

  try {
    const res = await fetch(`${BACKEND_URL}/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    uploadStatusEl.textContent = `Ingested ${data.num_chunks} chunks using ${data.backend}.`;
    uploadStatusEl.classList.remove("text-gray-300");
    uploadStatusEl.classList.add("text-green-300");
  } catch (err) {
    console.error(err);
    uploadStatusEl.textContent = "Upload failed. See console logs.";
    uploadStatusEl.classList.remove("text-gray-300");
    uploadStatusEl.classList.add("text-red-300");
  } finally {
    fileInput.value = "";
  }
});

resetBtn.addEventListener("click", () => {
  messages = [];
  messagesEl.innerHTML = "";
  uploadStatusEl.textContent = "";
  routeIndicatorEl.textContent = "Ready";
  if (conversations[sessionId]) {
    conversations[sessionId].messages = [];
  }
  renderChatList();
});

// Ask backend for a brand new session id and create a separate conversation entry.
newChatBtn.addEventListener("click", async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/session`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    messages = [];
    messagesEl.innerHTML = "";
    setSession(data.session_id);
    conversations[data.session_id] = { title: "New chat", messages: [] };
    uploadStatusEl.textContent = "";
    routeIndicatorEl.textContent = "Ready";
    renderChatList();
  } catch (err) {
    console.error(err);
  }
});

