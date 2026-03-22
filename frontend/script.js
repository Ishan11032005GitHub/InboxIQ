const API = "https://inboxiq-9p2y.onrender.com"; // KEEP THIS

// ----------------------
// LOGIN
// ----------------------
document.getElementById("loginBtn").onclick = () => {
    // No change needed, just redirect
    window.location.href = `${API}/auth/login`;
};

// ----------------------
// LOAD EMAILS
// ----------------------
document.getElementById("loadEmails").onclick = async () => {
    try {
        const res = await fetch(`${API}/emails`);

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Failed to load emails");
            return;
        }

        const data = await res.json();
        renderEmails(data);

    } catch (err) {
        console.error(err);
        alert("Server error while loading emails");
    }
};

// ----------------------
// SEND EMAIL
// ----------------------
document.getElementById("sendEmail").onclick = async () => {
    const to = document.getElementById("to").value;
    const subject = document.getElementById("subject").value;
    const body = document.getElementById("body").value;

    try {
        const res = await fetch(`${API}/send-email`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ to, subject, body })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Failed to send email");
            return;
        }

        alert("Email sent");

    } catch (err) {
        console.error(err);
        alert("Server error while sending email");
    }
};

// ----------------------
// RENDER EMAILS
// ----------------------
function renderEmails(emails) {
    const inbox = document.getElementById("inbox");
    inbox.innerHTML = "";

    emails.forEach(email => {
        const div = document.createElement("div");
        div.className = "email-card";

        div.innerHTML = `
            <div class="email-header">${email.subject}</div>
            <div>From: ${email.sender}</div>
            <div class="label">Label: ${email.label}</div>
            <div>Confidence: ${email.confidence.toFixed(2)}</div>
            <details>
                <summary>View Body</summary>
                <p>${email.body}</p>
            </details>

            <textarea id="reply-${email.id}" placeholder="Reply..."></textarea>

            <button onclick="generateReply('${email.id}')">Generate Reply</button>
            <button onclick="sendReply('${email.id}', '${email.sender}', '${email.subject}')">Send Reply</button>

            ${email.confidence < 0.6 ? `
                <select id="feedback-${email.id}">
                    <option>job_alert</option>
                    <option>promotion</option>
                    <option>newsletter</option>
                    <option>event_invite</option>
                    <option>notification</option>
                    <option>work</option>
                    <option>security</option>
                    <option>general</option>
                </select>
                <button onclick="saveFeedback('${email.id}')">Save Feedback</button>
            ` : ""}
        `;

        inbox.appendChild(div);
    });
}

// ----------------------
// GENERATE REPLY
// ----------------------
async function generateReply(id) {
    try {
        const res = await fetch(`${API}/generate-reply`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ id })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Failed to generate reply");
            return;
        }

        const data = await res.json();
        document.getElementById(`reply-${id}`).value = data.reply;

    } catch (err) {
        console.error(err);
        alert("Server error while generating reply");
    }
}

// ----------------------
// SEND REPLY
// ----------------------
async function sendReply(id, sender, subject) {
    const reply = document.getElementById(`reply-${id}`).value;

    try {
        const res = await fetch(`${API}/send-email`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                to: sender,
                subject: "Re: " + subject,
                body: reply
            })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Failed to send reply");
            return;
        }

        alert("Reply sent");

    } catch (err) {
        console.error(err);
        alert("Server error while sending reply");
    }
}

// ----------------------
// SAVE FEEDBACK
// ----------------------
async function saveFeedback(id) {
    const label = document.getElementById(`feedback-${id}`).value;

    try {
        const res = await fetch(`${API}/save-feedback`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ id, label })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Failed to save feedback");
            return;
        }

        alert("Feedback saved");

    } catch (err) {
        console.error(err);
        alert("Server error while saving feedback");
    }
}