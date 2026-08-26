async function getJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

function pct(x) {
  return `${(Number(x) * 100).toFixed(2)}%`;
}

async function renderSpine() {
  const data = await getJSON("/api/spine");
  const status = data.status || {};
  document.getElementById("spine-status").textContent =
    `Epoch ${data.current_epoch} · status ${status.status || "unknown"} · ` +
    `paper binding ${status.paper_binding?.allowed ? "allowed" : "blocked"}`;

  const pipeline = document.getElementById("pipeline");
  pipeline.innerHTML = "";
  for (const step of data.pipeline) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="pid">${step.id}</span><span class="plabel">${step.label}</span><span class="pstate">${step.state}</span>`;
    pipeline.appendChild(li);
  }

  const f = data.falsification;
  const box = document.getElementById("falsification");
  box.innerHTML = `
    <h3>Falsification board</h3>
    <p><strong>H0:</strong> ${f.hypothesis}</p>
    <p><strong>Status:</strong> ${f.status}</p>
    <ul>${f.evidence.map((e) => `<li>${e}</li>`).join("")}</ul>
  `;
}

async function renderProvenance(bundle) {
  const map = document.getElementById("source-map");
  const detail = document.getElementById("source-detail");
  map.innerHTML = "";

  const sources = Object.values(bundle.sources || {});
  sources.forEach((src, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "source-btn" + (idx === 0 ? " active" : "");
    btn.innerHTML = `<strong>${src.label}</strong><span>${src.paper_use}</span>`;
    btn.addEventListener("click", async () => {
      map.querySelectorAll(".source-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const resolved = await getJSON(`/api/metrics/${src.metric_id}`);
      detail.hidden = false;
      detail.innerHTML = `
        <p><strong>Path:</strong> <code>${resolved.source.path}</code></p>
        <p><strong>Aggregation:</strong> ${resolved.source.aggregation}</p>
        <p><strong>Notes:</strong> ${resolved.source.notes}</p>
        <pre>${JSON.stringify(resolved.data, null, 2)}</pre>
      `;
    });
    map.appendChild(btn);
  });

  if (sources[0]) {
    map.querySelector(".source-btn")?.click();
  }
}

function renderCompare(bundle) {
  const rates = bundle.available?.t05_claim_weighted || {};
  const order = [
    ["B01", "B01 ad-hoc"],
    ["B02", "B02 linear"],
    ["full", "Full protocol"],
  ];
  const max = Math.max(
    0.01,
    ...order.map(([k]) => Number(rates[k]?.unsupported_claim_rate || 0)),
  );
  const host = document.getElementById("compare-bars");
  host.innerHTML = "";
  for (const [key, label] of order) {
    const ur = Number(rates[key]?.unsupported_claim_rate || 0);
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div>${label}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${(ur / max) * 100}%"></div></div>
      <div class="bar-val">${pct(ur)}</div>
    `;
    host.appendChild(row);
  }

  const abl = bundle.available?.ablation_delta;
  const note = document.getElementById("ablation-note");
  if (abl?.deltas) {
    const g = abl.deltas.nogate_ur_delta * 100;
    const a = abl.deltas.noaudit_ur_delta * 100;
    note.innerHTML = `
      <strong>Ablation lane (separate classifier):</strong>
      Nogate Δ ${g.toFixed(1)}pp · Noaudit Δ ${a >= 0 ? "+" : ""}${a.toFixed(1)}pp.
      Full claims here: ${abl.full?.total_claims ?? "n/a"} vs T05 Full ${rates.full?.total_claims ?? "n/a"}.
    `;
  }
}

async function wireAdmit() {
  const form = document.getElementById("admit-form");
  const out = document.getElementById("admit-result");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const claim = document.getElementById("claim").value;
    const body = {
      claim,
      require_artifact_path: document.getElementById("require-path").checked,
      allow_mock: document.getElementById("allow-mock").checked,
    };
    const result = await getJSON("/api/admit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    out.hidden = false;
    out.dataset.decision = result.decision;
    out.innerHTML = `
      <p class="decision">${result.decision}</p>
      <p>paper_allowed: <strong>${result.paper_allowed}</strong> ·
         evidence_trace: ${result.has_evidence_trace} ·
         mock_risk: ${result.mock_risk} ·
         overclaim_risk: ${result.overclaim_risk}</p>
      <ul>${result.reasons.map((r) => `<li>${r}</li>`).join("")}</ul>
    `;
  });
}

async function renderResearchPoints() {
  const data = await getJSON("/api/research-points");
  const stats = document.getElementById("rp-stats");
  const gr = data.gate_redundancy;
  const cv = data.claim_volume;
  const drift = data.cross_classifier_drift;
  stats.innerHTML = `
    <div class="rp-stat"><strong>${gr.gate_redundancy_index.toFixed(3)}</strong><span>Gate redundancy index</span></div>
    <div class="rp-stat"><strong>${gr.gate_extra_over_linear_pp.toFixed(2)}pp</strong><span>Gate extra over B02</span></div>
    <div class="rp-stat"><strong>${cv.ratios.full_over_b01_claims_per_run.toFixed(2)}×</strong><span>Full/B01 claims per run</span></div>
    <div class="rp-stat"><strong>${drift.ur_abs_diff_pp.toFixed(2)}pp</strong><span>T05↔ablation Full UR drift</span></div>
    <div class="rp-stat"><strong>${data.pairwise_wins.full_better_than_b01}/${data.pairwise_wins.n_tasks}</strong><span>Tasks where Full &lt; B01 UR</span></div>
    <div class="rp-stat"><strong>${((data.label_taxonomy.fractions.supported || 0) * 100).toFixed(1)}%</strong><span>Supported label share</span></div>
    <div class="rp-stat"><strong>${data.provenance_verify.ok ? "PASS" : "FAIL"}</strong><span>Provenance verify</span></div>
  `;
  const list = document.getElementById("rp-list");
  list.innerHTML = data.research_points
    .map((rp) => `<li><b>${rp.id}</b> — ${rp.title}: ${rp.statement}</li>`)
    .join("");
}

async function renderCoreDirections() {
  const data = await getJSON("/api/core-directions");
  const ep = data.error_propagation;
  const cost = data.token_cost_efficiency;
  const conv = data.semantic_convergence;
  const stats = document.getElementById("rd-stats");
  stats.innerHTML = `
    <div class="rp-stat"><strong>${(ep.cascade_lift || 0).toFixed(2)}×</strong><span>Cascade lift (bad→bad)</span></div>
    <div class="rp-stat"><strong>${((ep.recovery_rate_any_supported_after_first_bad || 0) * 100).toFixed(1)}%</strong><span>Recovery after first bad</span></div>
    <div class="rp-stat"><strong>${cost.v6_proxy_by_condition.full.quality_per_1k_proxy_tokens.toFixed(3)}</strong><span>Full quality / 1k tok</span></div>
    <div class="rp-stat"><strong>${cost.v6_proxy_by_condition.B01.quality_per_1k_proxy_tokens.toFixed(3)}</strong><span>B01 quality / 1k tok</span></div>
    <div class="rp-stat"><strong>${conv.early_stop_simulation.claims_saved_vs_full}</strong><span>Claims saved at B02 budget</span></div>
    <div class="rp-stat"><strong>${conv.plateau_stopping_rule.mean_stop_index}</strong><span>Mean plateau stop index</span></div>
  `;
  document.getElementById("rd-list").innerHTML = data.research_directions
    .map((rd) => `<li><b>${rd.id}</b> — ${rd.title}: ${rd.statement}</li>`)
    .join("");
}

async function renderStrengthenedClaims() {
  const data = await getJSON("/api/strengthened-claims");
  const ne = data.near_equivalence;
  const ct = data.cosmetics_traces;
  const harm = data.task_harm_asymmetry;
  const si = data.seed_instability;
  document.getElementById("sc-stats").innerHTML = `
    <div class="rp-stat"><strong>${(ct.traced_but_not_supported_rate * 100).toFixed(1)}%</strong><span>Traced but not supported</span></div>
    <div class="rp-stat"><strong>${ne.abs_full_minus_b02_claim_weighted_pp.toFixed(2)}pp</strong><span>|Full−B02| UR (near-zero Δ)</span></div>
    <div class="rp-stat"><strong>${harm.n_full_worse_than_b02}/${harm.n_full_better_than_b02}</strong><span>Worse/better tasks vs B02</span></div>
    <div class="rp-stat"><strong>${si.full.range_pp.toFixed(2)}pp</strong><span>Full seed UR range</span></div>
    <div class="rp-stat"><strong>${data.gate_negative_tasks.length}</strong><span>Gate-negative tasks (≥5pp)</span></div>
    <div class="rp-stat"><strong>${data.pairwise_nulls.all_pairwise_p_gt_0_5 ? "YES" : "NO"}</strong><span>All Wilcoxon p&gt;0.5</span></div>
  `;
  document.getElementById("sc-list").innerHTML = data.claims
    .map((c) => `<li><b>${c.id}</b> [${c.strength}] — ${c.title}: ${c.statement}</li>`)
    .join("");
}

async function boot() {
  await renderSpine();
  const bundle = await getJSON("/api/metrics");
  await renderProvenance(bundle);
  renderCompare(bundle);
  await wireAdmit();
  await renderResearchPoints();
  await renderCoreDirections();
  await renderStrengthenedClaims();
}

boot().catch((err) => {
  console.error(err);
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<p style="padding:1rem;color:#9f1239">Console failed to load: ${err.message}</p>`,
  );
});
