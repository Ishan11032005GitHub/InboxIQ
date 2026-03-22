const API = "https://inboxiq-9p2y.onrender.com"; // CHANGE THIS

// ----------------------
// LOGIN
// ----------------------
document.getElementById("loginBtn").onclick = () => {
    window.location.href = `${API}/auth/login`;
};

// ----------------------
// LOAD EMAILS
// ----------------------
document.getElementById("loadEmails").onclick = async () => {
    const res = await fetch(`${API}/emails`);
    const data = await res.json();
    renderEmails(data);
};

// ----------------------
// SEND EMAIL
// ----------------------
document.getElementById("sendEmail").onclick = async () => {
    const to = document.getElementById("to").value;
    const subject = document.getElementById("subject").value;
    const body = document.getElementById("body").value;

    await fetch(`${API}/send-email`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ to, subject, body })
    });

    alert("Email sent");
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
    const res = await fetch(`${API}/generate-reply`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ id })
    });

    const data = await res.json();
    document.getElementById(`reply-${id}`).value = data.reply;
}

// ----------------------
// SEND REPLY
// ----------------------
async function sendReply(id, sender, subject) {
    const reply = document.getElementById(`reply-${id}`).value;

    await fetch(`${API}/send-email`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            to: sender,
            subject: "Re: " + subject,
            body: reply
        })
    });

    alert("Reply sent");
}

// ----------------------
// SAVE FEEDBACK
// ----------------------
async function saveFeedback(id) {
    const label = document.getElementById(`feedback-${id}`).value;

    await fetch(`${API}/save-feedback`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ id, label })
    });

    alert("Feedback saved");
}
