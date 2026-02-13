/**
 * Öğrenci Destek – Admin Panel
 */

// ── Kimlik bilgileri (HTTP Basic Auth) ───────────────────────────────
let authHeader = null;

function getAuthHeader() {
    return authHeader;
}

/** Login formu ile giriş yapma */
async function handleLogin() {
    const passwordInput = document.getElementById("loginPassword");
    const errorEl = document.getElementById("loginError");
    const password = passwordInput.value.trim();

    if (!password) {
        errorEl.textContent = "Şifre boş olamaz.";
        errorEl.style.display = "block";
        return;
    }

    authHeader = "Basic " + btoa("admin:" + password);

    // Doğrulama için stats endpoint'ini dene
    try {
        const res = await fetch("/api/admin/stats", {
            headers: { Authorization: authHeader },
        });

        if (res.status === 401) {
            authHeader = null;
            errorEl.textContent = "Geçersiz şifre. Tekrar deneyin.";
            errorEl.style.display = "block";
            passwordInput.value = "";
            passwordInput.focus();
            return;
        }

        if (!res.ok) {
            errorEl.textContent = "Sunucu hatası. Tekrar deneyin.";
            errorEl.style.display = "block";
            return;
        }

        // Başarılı giriş – paneli göster
        errorEl.style.display = "none";
        document.getElementById("loginScreen").style.display = "none";
        document.getElementById("adminPanel").style.display = "block";

        // Verileri yükle
        loadStats();
        loadTickets();
    } catch (e) {
        errorEl.textContent = "Bağlantı hatası. Sunucu çalışıyor mu?";
        errorEl.style.display = "block";
        console.error("Login hatası:", e);
    }
}

// Enter tuşuyla giriş
document.getElementById("loginPassword").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleLogin();
});

async function apiCall(url, options = {}) {
    const auth = getAuthHeader();
    if (!auth) return null;

    const res = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            Authorization: auth,
            ...(options.headers || {}),
        },
    });

    if (res.status === 401) {
        authHeader = null;
        document.getElementById("adminPanel").style.display = "none";
        document.getElementById("loginScreen").style.display = "flex";
        document.getElementById("loginError").textContent = "Oturum süresi doldu. Tekrar giriş yapın.";
        document.getElementById("loginError").style.display = "block";
        return null;
    }

    return res;
}

// ── İstatistikleri yükle ─────────────────────────────────────────────
async function loadStats() {
    try {
        const res = await apiCall("/api/admin/stats");
        if (!res || !res.ok) return;

        const data = await res.json();
        document.getElementById("statTotal").textContent = data.total_tickets;
        document.getElementById("statOpen").textContent = data.by_status["Açık"] || 0;
        document.getElementById("statProgress").textContent = data.by_status["İşlemde"] || 0;
        document.getElementById("statResolved").textContent = data.by_status["Çözüldü"] || 0;
    } catch (e) {
        console.error("İstatistik yükleme hatası:", e);
    }
}

// ── Ticketları yükle ─────────────────────────────────────────────────
let currentFilter = null;

async function loadTickets(statusFilter = null) {
    const tbody = document.getElementById("ticketsBody");

    try {
        let url = "/api/admin/tickets";
        if (statusFilter) url += `?status_filter=${encodeURIComponent(statusFilter)}`;

        const res = await apiCall(url);
        if (!res || !res.ok) return;

        const tickets = await res.json();

        if (tickets.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <div class="icon">✅</div>
                        <p>Henüz destek talebi yok.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = tickets
            .map((t) => {
                const date = new Date(t.created_at).toLocaleDateString("tr-TR", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                });

                const statusClass =
                    t.status === "Açık"
                        ? "open"
                        : t.status === "İşlemde"
                        ? "progress"
                        : "resolved";

                const shortText =
                    t.original_text.length > 60
                        ? t.original_text.substring(0, 60) + "..."
                        : t.original_text;

                return `
                    <tr>
                        <td><strong>TCK-${t.id}</strong></td>
                        <td>${date}</td>
                        <td title="${escapeHtml(t.original_text)}">${escapeHtml(shortText)}</td>
                        <td>${t.predicted_category || "-"}</td>
                        <td>%${Math.round((t.confidence || 0) * 100)}</td>
                        <td><span class="status-badge ${statusClass}">${t.status}</span></td>
                        <td><button class="action-btn" onclick="openEditModal(${t.id}, '${escapeAttr(t.status)}', '${escapeAttr(t.admin_note || "")}')">Düzenle</button></td>
                    </tr>
                `;
            })
            .join("");
    } catch (e) {
        console.error("Ticket yükleme hatası:", e);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <div class="icon">⚠️</div>
                    <p>Veriler yüklenirken hata oluştu.</p>
                </td>
            </tr>
        `;
    }
}

// ── Filtre ────────────────────────────────────────────────────────────
function filterTickets(status, btnEl) {
    currentFilter = status;

    document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    if (btnEl) btnEl.classList.add("active");

    loadTickets(status);
}

// ── Modal ─────────────────────────────────────────────────────────────
let editingTicketId = null;

function openEditModal(id, status, note) {
    editingTicketId = id;
    document.getElementById("modalTicketId").textContent = `TCK-${id}`;
    document.getElementById("modalStatus").value = status;
    document.getElementById("modalNote").value = note;
    document.getElementById("editModal").classList.add("active");
}

function closeModal() {
    editingTicketId = null;
    document.getElementById("editModal").classList.remove("active");
}

async function saveTicket() {
    if (!editingTicketId) return;

    const status = document.getElementById("modalStatus").value;
    const admin_note = document.getElementById("modalNote").value;

    try {
        const res = await apiCall(`/api/admin/tickets/${editingTicketId}`, {
            method: "PATCH",
            body: JSON.stringify({ status, admin_note }),
        });

        if (res && res.ok) {
            closeModal();
            loadTickets(currentFilter);
            loadStats();
        } else {
            alert("Güncelleme başarısız oldu.");
        }
    } catch (e) {
        console.error("Kaydetme hatası:", e);
        alert("Bir hata oluştu.");
    }
}

// ── Yardımcılar ──────────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// Modal dışına tıklayınca kapat
document.getElementById("editModal").addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) closeModal();
});

// ── Sayfa yükleme ────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
    document.getElementById("loginPassword").focus();
});
