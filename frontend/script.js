const API = "https://inboxiq-9p2y.onrender.com";

// ----------------------
// ELEMENTS
// ----------------------
const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const loadEmailsBtn = document.getElementById("loadEmails");
const sendEmailBtn = document.getElementById("sendEmail");

const inbox = document.getElementById("inbox");
const statusMessage = document.getElementById("statusMessage");

const authMessage = document.getElementById("authMessage");
const appContent = document.getElementById("appContent");

// ----------------------
// PAGINATION STATE
// ----------------------
let nextPageToken = null;
let isLoadingEmails = false;
let hasStartedLoading = false;

// ----------------------
// AUTH
// ----------------------
loginBtn.onclick = () => {
  window.location.href = `${API}/auth/login`;
};

logoutBtn.onclick = async () => {
  try {
    const res = await fetch(`${API}/auth/logout`, {
      method: "POST",
      credentials: "include"
    });

    if (!res.ok) throw new Error("Logout failed");

    updateAuthUI(false);
    resetInbox();
    showStatus("Logged out successfully");
  } catch (err) {
    showStatus(err.message);
  }
};

// ----------------------
// CHECK AUTH STATUS
// ----------------------
async function checkAuthStatus() {
  try {
    const res = await fetch(`${API}/auth/status`, {
      credentials: "include"
    });

    if (!res.ok) {
      updateAuthUI(false);
      return;
    }

    const data = await res.json();
    updateAuthUI(!!data.authenticated);
  } catch {
    updateAuthUI(false);
  }
}

function updateAuthUI(isAuthenticated) {
  if (isAuthenticated) {
    loginBtn.classList.add("hidden");
    logoutBtn.classList.remove("hidden");
    authMessage.classList.add("hidden");
    appContent.classList.remove("hidden");
  } else {
    loginBtn.classList.remove("hidden");
    logoutBtn.classList.add("hidden");
    authMessage.classList.remove("hidden");
    appContent.classList.add("hidden");
  }
}

// ----------------------
// LOAD EMAILS PROGRESSIVELY
// ----------------------
loadEmailsBtn.onclick = async () => {
  resetInbox();
  hasStartedLoading = true;
  await loadNextBatch();
};

async function loadNextBatch() {
  if (isLoadingEmails) return;

  isLoadingEmails = true;
  showStatus("Loading emails...");

  try {
    let url = `${API}/emails?limit=5`;
    if (nextPageToken) {
      url += `&page_token=${encodeURIComponent(nextPageToken)}`;
    }

    const res = await fetch(url, {
      credentials: "include"
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || "Failed to load emails");
    }

    const emails = data.emails || [];

    if (!emails.length && !nextPageToken) {
      inbox.innerHTML = `
        <div class="card" style="padding:20px;">
          <p style="margin:0;color:#94a3b8;">No unread emails found</p>
        </div>
      `;
      showStatus("No unread emails found");
      isLoadingEmails = false;
      return;
    }

    appendEmails(emails);

    nextPageToken = data.next_page_token || null;

    if (nextPageToken) {
      showStatus("Loaded current batch...");
      setTimeout(() => {
        isLoadingEmails = false;
        loadNextBatch();
      }, 250);
      return;
    }

    showStatus("All unread emails loaded");
  } catch (err) {
    showStatus(err.message);
  } finally {
    if (!nextPageToken) {
      isLoadingEmails = false;
    }
  }
}

function resetInbox() {
  inbox.innerHTML = "";
  nextPageToken = null;
  isLoadingEmails = false;
  hasStartedLoading = false;
}

// ----------------------
// SEND EMAIL
// ----------------------
sendEmailBtn.onclick = async () => {
  const to = document.getElementById("to").value.trim();
  const subject = document.getElementById("subject").value.trim();
  const body = document.getElementById("body").value.trim();

  if (!to || !subject || !body) {
    showStatus("Fill all fields");
    return;
  }

  try {
    const res = await fetch(`${API}/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ to, subject, body })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) throw new Error(data.detail || "Failed to send email");

    showStatus("Email sent");

    document.getElementById("to").value = "";
    document.getElementById("subject").value = "";
    document.getElementById("body").value = "";
  } catch (err) {
    showStatus(err.message);
  }
};

// ----------------------
// RENDER EMAILS
// ----------------------
function appendEmails(emails) {
  emails.forEach(email => {
    const div = document.createElement("div");
    div.className = "email-card";

    const subject = escapeHtml(email.subject || "(No Subject)");
    const sender = escapeHtml(email.sender || "(Unknown)");
    const body = escapeHtml(email.body || "");
    const label = escapeHtml(email.label || "general");
    const id = escapeAttr(email.id || "");

    const trimmedBody = body.length > 1200 ? body.slice(0, 1200) + "..." : body;

    div.innerHTML = `
      <div class="email-main">
        <div class="email-top">
          <div>
            <h3 class="email-subject">${subject}</h3>
            <div class="email-meta">From: ${sender}</div>
          </div>
          <div class="label-chip">${label}</div>
        </div>

        <div class="email-body">
          <details>
            <summary>View Email</summary>
            <p>${trimmedBody}</p>
          </details>
        </div>

        <div class="reply-box">
          <textarea id="reply-${id}" placeholder="Write reply..."></textarea>

          <div class="reply-actions">
            <button class="btn btn-secondary" onclick="generateReply('${id}')">
              Generate Reply
            </button>

            <button class="btn btn-success" onclick="sendReply('${id}', '${jsEscape(email.sender || "")}', '${jsEscape(email.subject || "")}')">
              Send Reply
            </button>
          </div>
        </div>
      </div>
    `;

    inbox.appendChild(div);
  });
}

// ----------------------
// GENERATE REPLY
// ----------------------
async function generateReply(id) {
  try {
    showStatus("Generating reply...");

    const res = await fetch(`${API}/generate-reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ id })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) throw new Error(data.detail || "Reply generation failed");

    const box = document.getElementById(`reply-${id}`);
    if (box) box.value = data.reply || "";

    showStatus("Reply generated");
  } catch (err) {
    showStatus(err.message);
  }
}

// ----------------------
// SEND REPLY
// ----------------------
async function sendReply(id, sender, subject) {
  try {
    const replyBox = document.getElementById(`reply-${id}`);
    const reply = replyBox?.value.trim();

    if (!reply) {
      showStatus("Reply is empty");
      return;
    }

    const res = await fetch(`${API}/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        to: sender,
        subject: subject ? `Re: ${subject}` : "Re:",
        body: reply
      })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) throw new Error(data.detail || "Failed to send reply");

    showStatus("Reply sent");
  } catch (err) {
    showStatus(err.message);
  }
}

// ----------------------
// UTILITIES
// ----------------------
function showStatus(msg) {
  statusMessage.textContent = msg;
  statusMessage.classList.remove("hidden");
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(str) {
  return String(str)
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function jsEscape(str) {
  return String(str)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "");
}

// ----------------------
// INIT
// ----------------------
checkAuthStatus();
