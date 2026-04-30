/* Evidence Integrity Validator - Frontend Logic */

let currentResults = [];

// ===== INIT =====
document.addEventListener("DOMContentLoaded", () => {
    loadConfig();
    setupDragDrop();
});

// ===== CONFIG =====
function loadConfig() {
    fetch("/api/session")
        .then(r => r.json())
        .then(s => {
            if (s.case_ref) document.getElementById("case_ref").value = s.case_ref;
            if (s.examiner) document.getElementById("examiner").value = s.examiner;
            if (s.agency) document.getElementById("agency").value = s.agency;
            if (s.files && s.files.length > 0) renderFileList(s.files);
        });
}

function saveConfig() {
    const data = {
        case_ref: document.getElementById("case_ref").value,
        examiner: document.getElementById("examiner").value,
        agency: document.getElementById("agency").value,
    };
    fetch("/api/config", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data),
    }).then(r => r.json()).then(() => showToast("Configuration saved"));
}

// ===== DRAG & DROP =====
function setupDragDrop() {
    const dz = document.getElementById("dropzone");
    const input = document.getElementById("file-input");

    dz.addEventListener("dragover", (e) => {
        e.preventDefault();
        dz.classList.add("drag-over");
    });
    dz.addEventListener("dragleave", () => dz.classList.remove("drag-over"));
    dz.addEventListener("drop", (e) => {
        e.preventDefault();
        dz.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            uploadFiles(e.dataTransfer.files);
        }
    });
}

function handleFileSelect(input) {
    if (input.files.length > 0) {
        uploadFiles(input.files);
        input.value = "";
    }
}

function uploadFiles(fileList) {
    const formData = new FormData();
    for (const f of fileList) {
        formData.append("file", f);
    }

    showProgress("Uploading files...", 50);

    fetch("/api/upload", { method: "POST", body: formData })
        .then(r => r.json())
        .then(data => {
            hideProgress();
            showToast(`Uploaded ${data.total} file(s)`);
            loadConfig();
            renderFileList((data.results || []).map(r => r.path));
        })
        .catch(e => {
            hideProgress();
            showToast("Upload failed: " + e.message, "error");
        });
}

// ===== FILE LIST =====
function renderFileList(files) {
    const container = document.getElementById("file-list");
    const card = document.getElementById("files-card");

    if (!files || files.length === 0) {
        card.style.display = "none";
        return;
    }

    card.style.display = "block";
    document.getElementById("file-count").textContent = `${files.length} file${files.length > 1 ? 's' : ''}`;

    container.innerHTML = files.map(fp => {
        const name = fp.split("/").pop().replace(/^[a-f0-9]{32}_/, "");
        const size = "—";
        return `
            <div class="file-item">
                <span class="file-name" title="${fp}">📄 ${name}</span>
                <span class="file-size">${size}</span>
                <span class="file-delete" onclick="deleteFile('${fp}')">&times;</span>
            </div>
        `;
    }).join("");
}

function deleteFile(path) {
    fetch("/api/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({path}),
    }).then(r => r.json()).then(() => {
        showToast("File removed");
        loadConfig();
    });
}

function clearAll() {
    if (!confirm("Remove all files?")) return;
    fetch("/api/clear", { method: "POST" })
        .then(r => r.json())
        .then(() => {
            document.getElementById("files-card").style.display = "none";
            document.getElementById("results-card").style.display = "none";
            document.getElementById("metadata-card").style.display = "none";
            document.getElementById("file-count").textContent = "0 files";
            showToast("All files cleared");
        });
}

// ===== HASHING =====
function hashFiles() {
    const algo = document.getElementById("hash-algo").value;
    const btn = document.getElementById("btn-hash");
    btn.disabled = true;
    btn.innerHTML = "⏳ Hashing...";

    showProgress("Computing hashes...", 30);

    fetch("/api/hash", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({algorithm: algo}),
    })
    .then(r => r.json())
    .then(data => {
        hideProgress();
        btn.disabled = false;
        btn.innerHTML = "🔍 Compute Hashes";

        const results = data.results || [data];
        currentResults = results;
        renderResults(results);
    })
    .catch(e => {
        hideProgress();
        btn.disabled = false;
        btn.innerHTML = "🔍 Compute Hashes";
        showToast("Error: " + e.message, "error");
    });
}

function renderResults(results) {
    const card = document.getElementById("results-card");
    const body = document.getElementById("results-body");
    card.style.display = "block";

    body.innerHTML = results.map((r, i) => {
        const hasError = r.error;
        const verified = r.match !== undefined;
        const matchClass = r.match ? "match" : "no-match";
        const matchText = r.match ? "✅ MATCH" : "❌ MISMATCH";

        return `
            <div class="result-item">
                <div class="result-header">
                    <span class="result-filename">📄 ${r.filename || "Unknown"}</span>
                    <span class="result-algo">${r.algorithm || "ERROR"}</span>
                </div>
                ${hasError ? `<div style="color:#ef4444;font-size:13px;">⚠️ ${r.error}</div>` : `
                <div class="result-hash" title="Click to select all">${r.hash || "—"}</div>
                <div class="result-meta">
                    <span>📦 ${r.filesize_hr || "—"}</span>
                    <span>🕐 ${r.modified || "—"}</span>
                </div>
                ${verified ? `<div class="result-match ${matchClass}">${matchText}</div>` : ""}
                <div class="result-actions">
                    <button class="btn btn-outline" onclick="showMetadata(${i})">🔎 Metadata</button>
                    <button class="btn btn-outline" onclick="showDetails(${i})">📋 Details</button>
                </div>
                `}
            </div>
        `;
    }).join("");
}

function verifyFromSelected() {
    const hashInput = document.getElementById("verify-hash").value.trim();
    if (!hashInput) {
        showToast("Paste a hash to verify against", "error");
        return;
    }

    // Use last result's file
    const results = currentResults;
    if (!results || results.length === 0) {
        showToast("Hash files first", "error");
        return;
    }

    showProgress("Verifying...", 50);

    const algo = document.getElementById("hash-algo").value;
    const filepath = results[0].filepath;

    fetch("/api/verify", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({path: filepath, expected: hashInput, algorithm: algo}),
    })
    .then(r => r.json())
    .then(data => {
        hideProgress();
        if (data.error) {
            showToast(data.error, "error");
            return;
        }
        currentResults = [data];
        renderResults([data]);
        showToast(data.match ? "✅ Hash MATCHES!" : "❌ Hash MISMATCH!", data.match ? "success" : "error");
    })
    .catch(e => {
        hideProgress();
        showToast("Error: " + e.message, "error");
    });
}

// ===== METADATA =====
function showMetadata(index) {
    const r = currentResults[index];
    if (!r || !r.metadata) {
        showToast("No metadata available", "error");
        return;
    }

    const card = document.getElementById("metadata-card");
    const body = document.getElementById("metadata-body");
    card.style.display = "block";

    const meta = r.metadata;
    let html = "";

    if (meta.type === "image") {
        html += renderMetaSection("Image Info", meta.metadata?.basic || {});
        html += renderMetaSection("EXIF Data", meta.metadata?.exif || {});
        if (meta.metadata?.gps_coordinates) {
            const gps = meta.metadata.gps_coordinates;
            html += `<div class="meta-section"><h4>📍 GPS Coordinates</h4>
                <div class="meta-grid">
                    <span class="meta-key">Latitude</span>
                    <span class="meta-val">${gps.latitude}</span>
                    <span class="meta-key">Longitude</span>
                    <span class="meta-val">${gps.longitude}</span>
                    <span class="meta-key">Google Maps</span>
                    <span class="meta-val"><a href="https://www.google.com/maps?q=${gps.latitude},${gps.longitude}" target="_blank">Open in Maps →</a></span>
                </div></div>`;
        }
        if (meta.metadata?.gps) {
            html += renderMetaSection("GPS Raw", meta.metadata.gps);
        }
    } else if (meta.type === "pdf" || meta.type === "office") {
        html += renderMetaSection("Document Info", meta.metadata?.info || {});
        if (meta.metadata?.pages) {
            html += `<div class="meta-section"><h4>Document</h4><div class="meta-grid">
                <span class="meta-key">Pages</span><span class="meta-val">${meta.metadata.pages}</span>
            </div></div>`;
        }
    } else if (meta.type === "video") {
        html += renderMetaSection("Video Info", meta.metadata?.info || {});
    } else {
        html += renderMetaSection("File Info", meta.metadata || {});
    }

    body.innerHTML = html;
}

function renderMetaSection(title, data) {
    if (!data || Object.keys(data).length === 0) return "";
    const items = Object.entries(data)
        .filter(([k, v]) => v && v !== "None" && v !== "")
        .map(([k, v]) => `
            <span class="meta-key">${k}</span>
            <span class="meta-val">${escapeHtml(String(v))}</span>
        `).join("");
    if (!items) return "";
    return `<div class="meta-section"><h4>${title}</h4><div class="meta-grid">${items}</div></div>`;
}

// ===== DETAILS MODAL =====
function showDetails(index) {
    const r = currentResults[index];
    if (!r) return;

    const modal = document.getElementById("modal");
    const title = document.getElementById("modal-title");
    const body = document.getElementById("modal-body");

    title.textContent = `📋 ${r.filename || "Details"}`;

    body.innerHTML = `
        <div class="meta-section">
            <h4>File Information</h4>
            <div class="meta-grid">
                <span class="meta-key">Filename</span><span class="meta-val">${r.filename || "—"}</span>
                <span class="meta-key">Filepath</span><span class="meta-val" style="font-size:10px;">${r.filepath || "—"}</span>
                <span class="meta-key">Size</span><span class="meta-val">${r.filesize_hr || "—"}</span>
                <span class="meta-key">Last Modified</span><span class="meta-val">${r.modified || "—"}</span>
            </div>
        </div>
        <div class="meta-section">
            <h4>Hash (${r.algorithm || "SHA256"})</h4>
            <div class="result-hash">${r.hash || "—"}</div>
        </div>
        ${r.match !== undefined ? `
        <div class="meta-section">
            <h4>Verification</h4>
            <div class="meta-grid">
                <span class="meta-key">Expected</span><span class="meta-val" style="font-family:monospace;font-size:11px;">${r.expected || "—"}</span>
                <span class="meta-key">Status</span><span class="meta-val" style="font-weight:600;color:${r.match ? '#10b981' : '#ef4444'}">${r.match ? '✅ MATCH' : '❌ MISMATCH'}</span>
            </div>
        </div>
        ` : ""}
    `;

    modal.style.display = "flex";
}

function closeModal(e) {
    if (e && e.target !== document.getElementById("modal")) return;
    document.getElementById("modal").style.display = "none";
}

// ===== REPORT GENERATION =====
function generateReport() {
    const btn = document.getElementById("btn-report");
    const algo = document.getElementById("hash-algo").value;

    btn.disabled = true;
    btn.innerHTML = "⏳ Generating...";
    showProgress("Generating PDF report...", 60);

    fetch("/api/report", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            algorithm: algo,
            case_ref: document.getElementById("case_ref").value,
            examiner: document.getElementById("examiner").value,
            agency: document.getElementById("agency").value,
        }),
    })
    .then(r => r.json())
    .then(data => {
        hideProgress();
        btn.disabled = false;
        btn.innerHTML = "📄 Generate Report (PDF)";

        if (data.error) {
            showToast("Report error: " + data.error, "error");
            return;
        }

        // Download the report
        const link = document.createElement("a");
        link.href = data.report_path;
        link.download = data.report;
        link.click();

        showToast("✅ Report generated & downloaded!", "success");
    })
    .catch(e => {
        hideProgress();
        btn.disabled = false;
        btn.innerHTML = "📄 Generate Report (PDF)";
        showToast("Error: " + e.message, "error");
    });
}

// ===== CSV EXPORT =====
function exportCSV() {
    if (!currentResults || currentResults.length === 0) {
        showToast("Hash files first before exporting", "error");
        return;
    }

    fetch("/api/export_csv", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            results: currentResults,
            algorithm: document.getElementById("hash-algo").value.toUpperCase(),
        }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.path) {
            showToast("CSV exported to: " + data.path, "success");
        }
    });
}

// ===== UTILITIES =====
function showProgress(text, percent) {
    const bar = document.getElementById("progress");
    const fill = document.getElementById("progress-fill");
    const txt = document.getElementById("progress-text");
    bar.style.display = "block";
    fill.style.width = percent + "%";
    txt.textContent = text;
}

function hideProgress() {
    document.getElementById("progress").style.display = "none";
}

function clearResults() {
    document.getElementById("results-card").style.display = "none";
    document.getElementById("metadata-card").style.display = "none";
    currentResults = [];
}

function showToast(message, type = "") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = "toast " + type;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 4000);
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
