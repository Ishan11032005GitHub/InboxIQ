const API = "https://inboxiq-9p2y.onrender.com";

const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const loadEmailsBtn = document.getElementById("loadEmails");
const sendEmailBtn = document.getElementById("sendEmail");
const inbox = document.getElementById("inbox");
const statusMessage = document.getElementById("statusMessage");
const authMessage = document.getElementById("authMessage");
const appContent = document.getElementById("appContent");

loginBtn.onclick = () => {
  window.location.href = `${API}/auth/login`;
};

logoutBtn.onclick = async () => {
  try {
    const res = await fetch(`${API}/auth/logout`, {
      method: "POST",
      credentials: "include"
    });

    if (!res.ok) {
      throw new Error("Failed to logout");
    }

    updateAuthUI(false);
    inbox.innerHTML = "";
    showStatus("Logged out successfully.");
  } catch (err) {
    showStatus(`Error: ${err.message}`);
  }
};

loadEmailsBtn.onclick = async () => {
  try {
    showStatus("Loading emails...");
    const res = await fetch(`${API}/emails`, {
      credentials: "include"
    });

    if (!res.ok) {
      throw new Error("Failed to load emails");
    }

    const data = await res.json();
    renderEmails(data);
    showStatus(`${data.length} email(s) loaded.`);
  } catch (err) {
    showStatus(`Error: ${err.message}`);
  }
};

sendEmailBtn.onclick = async () => {
  const to = document.getElementById("to").value.trim();
  const subject = document.getElementById("subject").value.trim();
  const body = document.getElementById("body").value.trim();

  if (!to || !subject || !body) {
    showStatus("Fill all compose fields.");
    return;
  }

  try {
    const res = await fetch(`${API}/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ to, subject, body })
    });

    if (!res.ok) {
      throw new Error("Failed to send email");
    }

    showStatus("Email sent successfully.");
    document.getElementById("to").value = "";
    document.getElementById("subject").value = "";
    document.getElementById("body").value = "";
  } catch (err) {
    showStatus(`Error: ${err.message}`);
  }
};

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

function renderEmails(emails) {
  inbox.innerHTML = "";

  if (!emails || emails.length === 0) {
    inbox.innerHTML = `
      <div class="card" style="padding:20px;">
        <p style="margin:0;color:#94a3b8;">No unread emails found.</p>
      </div>
    `;
    return;
  }

  emails.forEach((email) => {
    const div = document.createElement("div");
    div.className = "email-card";

    const safeSubject = escapeHtml(email.subject || "(No Subject)");
    const safeSender = escapeHtml(email.sender || "(Unknown Sender)");
    const safeBody = escapeHtml(email.body || "");
    const safeLabel = escapeHtml(email.label || "general");
    const safeId = escapeAttribute(email.id || "");

    div.innerHTML = `
      <div class="email-main">
        <div class="email-top">
          <div>
            <h3 class="email-subject">${safeSubject}</h3>
            <div class="email-meta">From: ${safeSender}</div>
          </div>
          <div class="label-chip">${safeLabel}</div>
        </div>

        <div class="email-body">
          <details>
            <summary>View Email Body</summary>
            <p>${safeBody}</p>
          </details>
        </div>

        <div class="reply-box">
          <textarea id="reply-${safeId}" placeholder="Write reply..."></textarea>
          <div class="reply-actions">
            <button class="btn btn-secondary" onclick="generateReply('${safeId}')">Generate Reply</button>
            <button class="btn btn-success" onclick="sendReply('${safeId}', '${jsEscape(email.sender || "")}', '${jsEscape(email.subject || "")}')">Send Reply</button>
          </div>
        </div>
      </div>
    `;

    inbox.appendChild(div);
  });
}

async function generateReply(id) {
  try {
    showStatus("Generating reply...");
    const res = await fetch(`${API}/generate-reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ id })
    });

    if (!res.ok) {
      throw new Error("Failed to generate reply");
    }

    const data = await res.json();
    const box = document.getElementById(`reply-${id}`);
    if (box) {
      box.value = data.reply || "";
    }
    showStatus("Reply generated.");
  } catch (err) {
    showStatus(`Error: ${err.message}`);
  }
}

async function sendReply(id, sender, subject) {
  try {
    const replyBox = document.getElementById(`reply-${id}`);
    const reply = replyBox ? replyBox.value.trim() : "";

    if (!reply) {
      showStatus("Reply is empty.");
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

    if (!res.ok) {
      throw new Error("Failed to send reply");
    }

    showStatus("Reply sent.");
  } catch (err) {
    showStatus(`Error: ${err.message}`);
  }
}

function showStatus(message) {
  statusMessage.textContent = message;
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

function escapeAttribute(str) {
  return String(str).replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function jsEscape(str) {
  return String(str)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "");
}

checkAuthStatus();
