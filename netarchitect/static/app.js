// NetArchitect Dashboard Application Logic

const API_BASE = "";

// ── State ────────────────────────────────────────────────────────────
let currentScenario = null;
let currentDesign = null;
let currentConfig = "";

// ── DOM refs ─────────────────────────────────────────────────────────
const presetGrid   = document.getElementById("preset-grid");
const scenarioCard = document.getElementById("scenario-detail");
const scenarioMeta = document.getElementById("scenario-meta");
const subnetTbody  = document.getElementById("subnet-tbody");
const btnRun       = document.getElementById("btn-run-design");
const loadingOvl   = document.getElementById("loading-overlay");

const vlsmTbody    = document.getElementById("vlsm-tbody");
const vlsmStats    = document.getElementById("vlsm-stats");
const mediaTbody   = document.getElementById("media-tbody");
const opticalCard  = document.getElementById("optical-card");
const opticalTbody = document.getElementById("optical-tbody");
const routingInfo  = document.getElementById("routing-info");
const rationaleList= document.getElementById("rationale-list");
const configOutput = document.getElementById("config-output");

const navBtns      = document.querySelectorAll(".nav-btn");
const sections     = document.querySelectorAll(".section");

const PRESET_META = {
    campus_lan: { icon: "🏫", desc: "3-Building University Network — 1,600 endpoints, PoE APs, VoIP, CCTV" },
    metro_man:  { icon: "🏙️", desc: "FinTech HQ + 2 Remote Branches — 15–35 km OS2 fibre links" },
    global_wan: { icon: "🌍", desc: "4-City Enterprise + AWS/Azure Cloud VPC — IPsec, BGP, MPLS" },
};



navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        navBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const target = btn.dataset.section;
        sections.forEach(s => {
            s.classList.toggle("active", s.id === `section-${target}`);
        });
    });
});

function switchSection(name) {
    navBtns.forEach(b => {
        b.classList.toggle("active", b.dataset.section === name);
    });
    sections.forEach(s => {
        s.classList.toggle("active", s.id === `section-${name}`);
    });
}



async function loadPresets() {
    try {
        const res = await fetch(`${API_BASE}/api/presets`);
        const data = await res.json();
        presetGrid.innerHTML = "";
        data.presets.forEach(name => {
            const meta = PRESET_META[name] || { icon: "📦", desc: name };
            const card = document.createElement("div");
            card.className = "preset-card";
            card.innerHTML = `
                <span class="preset-icon">${meta.icon}</span>
                <h3>${name.replace(/_/g, " ")}</h3>
                <p>${meta.desc}</p>
            `;
            card.addEventListener("click", () => selectPreset(name, card));
            presetGrid.appendChild(card);
        });
    } catch (e) {
        presetGrid.innerHTML = `<p style="color:var(--accent-red)">Failed to load presets: ${e.message}</p>`;
    }
}

async function selectPreset(name, cardEl) {
    document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("selected"));
    cardEl.classList.add("selected");

    const res = await fetch(`${API_BASE}/api/presets/${name}`);
    currentScenario = await res.json();

    // Populate meta
    scenarioMeta.innerHTML = `
        <div class="meta-item"><div class="meta-label">Scenario</div><div class="meta-value">${currentScenario.scenario_name}</div></div>
        <div class="meta-item"><div class="meta-label">Scale</div><div class="meta-value">${currentScenario.scale}</div></div>
        <div class="meta-item"><div class="meta-label">Root Network</div><div class="meta-value">${currentScenario.root_network}</div></div>
        <div class="meta-item"><div class="meta-label">Sites</div><div class="meta-value">${currentScenario.num_sites}</div></div>
        <div class="meta-item"><div class="meta-label">Subnets</div><div class="meta-value">${currentScenario.subnet_requirements.length}</div></div>
        <div class="meta-item"><div class="meta-label">Links</div><div class="meta-value">${currentScenario.links.length}</div></div>
    `;

    // Populate subnet table
    subnetTbody.innerHTML = currentScenario.subnet_requirements.map(s => `
        <tr>
            <td>${s.name}</td>
            <td>${s.vlan_id ?? "—"}</td>
            <td>${s.required_hosts}</td>
            <td>${s.description ?? ""}</td>
        </tr>
    `).join("");

    scenarioCard.style.display = "block";
    scenarioCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}



btnRun.addEventListener("click", runDesign);

async function runDesign() {
    if (!currentScenario) return;

    loadingOvl.style.display = "flex";
    try {
        // Get design
        const designRes = await fetch(`${API_BASE}/api/design`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentScenario),
        });
        if (!designRes.ok) throw new Error(await designRes.text());
        currentDesign = await designRes.json();

        // Get config
        const cfgRes = await fetch(`${API_BASE}/api/config`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentScenario),
        });
        currentConfig = await cfgRes.text();

        renderResults();
        switchSection("results");

    } catch (e) {
        alert("Pipeline error: " + e.message);
    } finally {
        loadingOvl.style.display = "none";
    }
}



function effBadge(pct) {
    if (pct > 75) return `<span class="badge badge-green">${pct}%</span>`;
    if (pct > 50) return `<span class="badge badge-yellow">${pct}%</span>`;
    return `<span class="badge badge-red">${pct}%</span>`;
}

function renderResults() {
    const d = currentDesign;

    // ── VLSM ──
    if (d.vlsm_result) {
        vlsmTbody.innerHTML = d.vlsm_result.allocations.map(a => `
            <tr>
                <td>${a.name}</td>
                <td>${a.vlan_id ?? "—"}</td>
                <td style="color:var(--accent-yellow)">${a.network_address}/${a.cidr_prefix}</td>
                <td>${a.subnet_mask}</td>
                <td style="color:var(--accent-purple)">${a.wildcard_mask}</td>
                <td style="color:var(--accent-green)">${a.first_usable_host}</td>
                <td style="color:var(--accent-red)">${a.broadcast_address}</td>
                <td>${a.required_hosts}</td>
                <td>${a.usable_host_capacity}</td>
                <td>${effBadge(a.efficiency_pct)}</td>
            </tr>
        `).join("");

        vlsmStats.innerHTML = `
            <div class="stat-item"><span class="stat-label">Root Network</span><span class="stat-value">${d.vlsm_result.root_network}</span></div>
            <div class="stat-item"><span class="stat-label">Total Hosts</span><span class="stat-value">${d.vlsm_result.total_requested_hosts.toLocaleString()}</span></div>
            <div class="stat-item"><span class="stat-label">Overall Efficiency</span><span class="stat-value">${d.vlsm_result.overall_efficiency_pct}%</span></div>
        `;
    }

    // ── Media ──
    if (d.media_decisions && d.media_decisions.length) {
        mediaTbody.innerHTML = d.media_decisions.map(m => `
            <tr>
                <td>${m.source_node} ↔ ${m.destination_node}</td>
                <td>${Number(m.distance_m).toLocaleString()} m</td>
                <td><span class="badge badge-blue">${m.recommended_medium}</span></td>
                <td>${m.transceiver}</td>
                <td>${Number(m.max_reach_m).toLocaleString()} m</td>
                <td style="color:var(--text-muted)">${m.ieee_standard}</td>
            </tr>
        `).join("");
    }

    // ── Optical ──
    if (d.optical_budgets && d.optical_budgets.length) {
        opticalCard.style.display = "block";
        opticalTbody.innerHTML = d.optical_budgets.map(b => {
            const viable = b.is_viable
                ? '<span class="badge badge-green">✅ Yes</span>'
                : '<span class="badge badge-red">❌ No</span>';
            const marginCls = b.link_margin_dB > 3 ? "accent-green" : (b.link_margin_dB > 0 ? "accent-yellow" : "accent-red");
            return `
                <tr>
                    <td>${b.link_id}</td>
                    <td>${b.distance_km.toFixed(2)}</td>
                    <td>${b.total_loss_dB.toFixed(2)}</td>
                    <td style="color:var(--${marginCls})">${b.link_margin_dB.toFixed(2)}</td>
                    <td>${viable}</td>
                </tr>
            `;
        }).join("");
    } else {
        opticalCard.style.display = "none";
    }

    // ── Routing ──
    if (d.routing_decision) {
        const r = d.routing_decision;
        routingInfo.innerHTML = `
            <div class="routing-protocol">${r.protocol}</div>
            <p><strong>OSPF Areas:</strong> ${r.ospf_areas.join(", ")}</p>
            <p><strong>BGP ASN:</strong> ${r.bgp_asn ?? "N/A"}</p>
            <p class="routing-detail">${r.rationale}</p>
            <div class="routing-refs">
                ${r.rfc_references.map(ref => `<span class="badge badge-blue">${ref}</span>`).join("")}
            </div>
        `;
    }

    // ── Rationales ──
    if (d.rationales && d.rationales.length) {
        rationaleList.innerHTML = d.rationales.map(r => `
            <div class="rationale-item">
                <div class="rationale-category">${r.decision_category}</div>
                <h4>${r.decision_summary}</h4>
                <p>${r.detail}</p>
            </div>
        `).join("");
    }

    // ── Config ──
    configOutput.textContent = currentConfig || "No configuration generated.";
}



document.getElementById("btn-copy-config").addEventListener("click", () => {
    if (!currentConfig) return;
    navigator.clipboard.writeText(currentConfig).then(() => {
        const btn = document.getElementById("btn-copy-config");
        btn.textContent = "✅ Copied!";
        setTimeout(() => { btn.textContent = "📋 Copy to Clipboard"; }, 2000);
    });
});

document.getElementById("btn-download-config").addEventListener("click", () => {
    if (!currentConfig) return;
    const blob = new Blob([currentConfig], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `netarchitect_${(currentScenario?.scenario_name || "config").replace(/\s+/g, "_")}.cfg`;
    a.click();
    URL.revokeObjectURL(url);
});



loadPresets();
