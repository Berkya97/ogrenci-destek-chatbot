/**
 * Öğrenci Destek – Sohbet Arayüzü
 *
 * Polling ile sunucu tarafındaki güncellemeleri (admin ticket değişiklikleri vb.)
 * otomatik olarak sohbet ekranına yansıtır.
 */

// ── Oturum yönetimi ──────────────────────────────────────────────────
function getSessionId() {
    let sid = localStorage.getItem("session_id");
    if (!sid) {
        sid = crypto.randomUUID ? crypto.randomUUID() : generateUUID();
        localStorage.setItem("session_id", sid);
    }
    return sid;
}

function generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

const SESSION_ID = getSessionId();
const chatMessages = document.getElementById("chatMessages");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

let welcomeRemoved = false;

/** Son bilinen mesaj id'si – polling'de after_id olarak kullanılır */
let lastMessageId = 0;

/** Render edilmiş mesaj id'leri – tekrar eklemeyi önler */
const renderedIds = new Set();

const POLL_INTERVAL_MS = 2500;

// ── Karşılama ekranını kaldır ────────────────────────────────────────
function removeWelcome() {
    if (!welcomeRemoved) {
        const welcome = chatMessages.querySelector(".welcome-message");
        if (welcome) welcome.remove();
        welcomeRemoved = true;
    }
}

// ── Mesaj ekleme (sunucudan gelen, id'li) ────────────────────────────
/**
 * Sunucudan gelen bir mesajı sohbet alanına ekler.
 * Dedup: aynı id iki kez eklenmez.
 */
function renderServerMessage(msg) {
    if (renderedIds.has(msg.id)) return;
    renderedIds.add(msg.id);
    if (msg.id > lastMessageId) lastMessageId = msg.id;

    removeWelcome();

    const wrapper = document.createElement("div");
    wrapper.classList.add("message", msg.role);

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    const textEl = document.createElement("div");
    textEl.textContent = msg.text;
    bubble.appendChild(textEl);

    // Meta bilgileri (bot mesajlarında)
    if (msg.role === "bot" && (msg.category || msg.ticket_id)) {
        const meta = document.createElement("div");
        meta.classList.add("meta");

        if (msg.category) {
            const badge = document.createElement("span");
            badge.classList.add("category-badge");
            badge.textContent = msg.category;
            meta.appendChild(badge);
        }
        if (msg.ticket_id) {
            const ticket = document.createElement("span");
            ticket.classList.add("ticket-badge");
            ticket.textContent = msg.ticket_id;
            meta.appendChild(ticket);
        }
        if (msg.confidence != null) {
            const conf = document.createElement("span");
            conf.textContent = `%${Math.round(msg.confidence * 100)}`;
            meta.appendChild(conf);
        }
        bubble.appendChild(meta);
    }

    // Zaman damgası
    const timeEl = document.createElement("div");
    timeEl.classList.add("meta");
    if (msg.created_at) {
        const d = new Date(msg.created_at);
        timeEl.textContent = d.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
    } else {
        timeEl.textContent = new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
    }
    bubble.appendChild(timeEl);

    wrapper.appendChild(bubble);
    chatMessages.appendChild(wrapper);
    scrollToBottom();
}

// ── Yerel mesaj ekleme (anında, id'siz – optimistic UI) ──────────────
/**
 * Kullanıcı mesajını anında göstermek için kullanılır.
 * Sunucu id'si henüz bilinmez, dedup takibi yapılmaz.
 */
function renderLocalMessage(role, text) {
    removeWelcome();

    const wrapper = document.createElement("div");
    wrapper.classList.add("message", role);

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    const textEl = document.createElement("div");
    textEl.textContent = text;
    bubble.appendChild(textEl);

    const timeEl = document.createElement("div");
    timeEl.classList.add("meta");
    timeEl.textContent = new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
    bubble.appendChild(timeEl);

    wrapper.appendChild(bubble);
    chatMessages.appendChild(wrapper);
    scrollToBottom();
}

// ── Yazıyor göstergesi ───────────────────────────────────────────────
function showTyping() {
    const el = document.createElement("div");
    el.classList.add("typing-indicator");
    el.id = "typingIndicator";
    el.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    chatMessages.appendChild(el);
    scrollToBottom();
}

function hideTyping() {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── Geçmişi yükleme (ilk açılış) ────────────────────────────────────
async function loadHistory() {
    try {
        const res = await fetch(
            `/api/chat/history?session_id=${encodeURIComponent(SESSION_ID)}`
        );
        if (!res.ok) return;
        const messages = await res.json();
        for (const m of messages) {
            renderServerMessage(m);
        }
    } catch (e) {
        console.warn("Geçmiş yüklenemedi:", e);
    }
}

// ── Polling: yeni mesajları getir ────────────────────────────────────
let pollPaused = false;

async function pollNewMessages() {
    if (pollPaused) return;

    try {
        const url =
            `/api/chat/history?session_id=${encodeURIComponent(SESSION_ID)}` +
            `&after_id=${lastMessageId}`;
        const res = await fetch(url);
        if (!res.ok) return;

        const messages = await res.json();
        for (const m of messages) {
            renderServerMessage(m);
        }
    } catch (e) {
        // Sessizce devam et – ağ kesintisi vb.
    }
}

// ── Mesaj gönderme ───────────────────────────────────────────────────
async function sendMessage(text) {
    text = text.trim();
    if (!text) return;

    // Gönderim sırasında polling'i duraklat – çift mesaj olmasın
    pollPaused = true;

    // Kullanıcı mesajını anında göster (optimistic UI)
    renderLocalMessage("user", text);
    messageInput.value = "";
    messageInput.disabled = true;
    sendBtn.disabled = true;
    showTyping();

    try {
        const res = await fetch("/api/chat/message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: SESSION_ID, text }),
        });

        hideTyping();

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            renderLocalMessage("bot", `Bir hata oluştu: ${err.detail || res.statusText}`);
            return;
        }

        const data = await res.json();

        // Bot cevabını anında göster (optimistic UI)
        renderLocalMessage("bot", data.reply_text);

        // Sunucu id'lerini senkronize et – zaten gösterilen mesajları
        // tekrar eklemez, sadece lastMessageId/renderedIds günceller
        await syncIds();
    } catch (e) {
        hideTyping();
        renderLocalMessage("bot", "Bağlantı hatası. Lütfen tekrar deneyin.");
        console.error(e);
    } finally {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
        pollPaused = false;
    }
}

/**
 * POST sonrası sunucudaki en son id'leri al ve takip state'ini güncelle.
 * Mesajlar zaten yerel olarak render edildi, burada sadece id kaydı yapılır.
 */
async function syncIds() {
    try {
        const url =
            `/api/chat/history?session_id=${encodeURIComponent(SESSION_ID)}` +
            `&after_id=${lastMessageId}`;
        const res = await fetch(url);
        if (!res.ok) return;

        const messages = await res.json();
        for (const m of messages) {
            // Id'yi kaydet ama tekrar render etme
            renderedIds.add(m.id);
            if (m.id > lastMessageId) lastMessageId = m.id;
        }
    } catch (e) {
        // Sessizce devam et
    }
}

// ── Olay dinleyicileri ───────────────────────────────────────────────
function handleSubmit(e) {
    e.preventDefault();
    sendMessage(messageInput.value);
}

function sendQuickMessage(text) {
    sendMessage(text);
}

// ── Başlatma ─────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", async () => {
    await loadHistory();
    messageInput.focus();

    // Polling başlat
    setInterval(pollNewMessages, POLL_INTERVAL_MS);
});
