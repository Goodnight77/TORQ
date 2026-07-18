import { useEffect, useState, useCallback, useMemo, useRef, useDeferredValue } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import * as api from "../api.js";
import Navbar from "../components/Navbar.jsx";
import { useI18n } from "../i18n";
import { useToast } from "../toast.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import useFocusTrap from "../hooks/useFocusTrap";
import styles from "./Dashboard.module.css";

const CONFIDENCE_THRESHOLD = 0.6;

const FIX = {
  resolved: true,
  actual_fix: "Applied recommended fix; verified stable.",
  time_to_fix_min: 30,
};

// Varied demo faults across skills (E=electromechanical, J=packaging, C/P/A=general)
// so repeated clicks exercise different machines and route to different techs.
const SIM_FAULTS = [
  { fault_code: "E-471", machine: "CM-350 Line 2", context: "Motor tripped after hours running." },
  { fault_code: "E-201", machine: "CM-350 Line 1", context: "Overcurrent on start, grinding noise." },
  { fault_code: "J-108", machine: "PK-9 Line 3", context: "Film feed jammed at the roller nip." },
  { fault_code: "J-233", machine: "PK-9 Line 3", context: "Seal temperature low, weak seals." },
  { fault_code: "C-207", machine: "Chiller 6", context: "Condenser water flow dropping, efficiency down." },
  { fault_code: "P-410", machine: "Pump 3", context: "High vibration and bearing noise." },
  { fault_code: "A-120", machine: "AHU 2", context: "Filter differential pressure over setpoint." },
];

function Tile({ label, value }) {
  return (
    <div className={styles.tile}>
      <b>{value}</b>
      <small>{label}</small>
    </div>
  );
}

function Badge({ status }) {
  return <span className={`${styles.badge} ${styles[status] || ""}`}>{status}</span>;
}

// A work order is "open" until it reaches a terminal state.
const OPEN_STATUS = new Set(["pending", "approved", "dispatched"]);
const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString() : "-");

function MachineDrawer({ machine, workOrders, downtime, onClose, onSelectWorkOrder, t }) {
  if (!machine) return null;
  const history = workOrders.filter((w) => w.machine === machine);
  const open = history.filter((w) => OPEN_STATUS.has(w.status));
  const model = downtime?.model || machine;
  const location = downtime?.location;
  const panelRef = useFocusTrap(!!machine);

  return (
    <div className={styles.drawer} onClick={onClose}>
      <div ref={panelRef} className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>{t("dashboard.close")}</button>
        <h3 className={styles.panelTitle}>{machine}</h3>
        <p className={styles.sub}>{model}{location ? ` - ${location}` : ""}</p>

        <section className={styles.tiles} style={{ margin: "16px 0" }}>
          <Tile label={t("dashboard.total_downtime")} value={`${downtime?.downtime_min ?? 0} min`} />
          <Tile label={t("dashboard.work_orders")} value={history.length} />
          <Tile label={t("dashboard.open_faults")} value={open.length} />
        </section>

        <div className={styles.langLabel}>{t("dashboard.open_faults")}</div>
        {open.length === 0 ? (
          <p className={styles.muted}>{t("dashboard.none_open")}</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>{t("dashboard.id")}</th><th>{t("dashboard.fault")}</th><th>{t("dashboard.status")}</th><th>{t("dashboard.cause")}</th></tr>
              </thead>
              <tbody>
                {open.map((w) => (
                  <tr key={w.id}>
                    <td><a className={styles.link} onClick={() => onSelectWorkOrder(w)}>{w.id}</a></td>
                    <td>{w.fault_code}</td>
                    <td><Badge status={w.status} /></td>
                    <td className={styles.cause}>{w.root_cause}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className={styles.langLabel} style={{ marginTop: 24 }}>{t("dashboard.work_orders")}</div>
        {history.length === 0 ? (
          <p className={styles.muted}>{t("dashboard.no_work_orders")}</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>{t("dashboard.id")}</th><th>{t("dashboard.fault")}</th><th>{t("dashboard.status")}</th><th>{t("dashboard.created")}</th></tr>
              </thead>
              <tbody>
                {history.map((w) => (
                  <tr key={w.id}>
                    <td><a className={styles.link} onClick={() => onSelectWorkOrder(w)}>{w.id}</a></td>
                    <td>{w.fault_code}</td>
                    <td><Badge status={w.status} /></td>
                    <td className={styles.muted}>{fmtDate(w.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function ConfidenceBadge({ confidence, t }) {
  if (confidence == null) return null;
  const low = confidence < CONFIDENCE_THRESHOLD;
  return (
    <span className={`${styles.badge} ${low ? styles.lowConfidence : styles.highConfidence}`}>
      {low ? t("dashboard.needs_review") : `${(confidence * 100).toFixed(0)}%`}
    </span>
  );
}

function Skeleton({ width, height, style }) {
  return (
    <div
      className="skeleton"
      style={{ width: width || "100%", height: height || 20, ...style }}
    />
  );
}

function LiveFeed({ faults, t }) {
  if (!faults || faults.length === 0) {
    return (
      <div className={styles.feedCard}>
        <div className={styles.feedHead}>{t("dashboard.live_feed")}</div>
        <div className={styles.feedEmpty}>{t("dashboard.no_recent_faults")}</div>
      </div>
    );
  }
  const displayed = faults.slice(0, 8);
  return (
    <div className={styles.feedCard}>
      <div className={styles.feedHead}>{t("dashboard.live_feed")}</div>
      <div className={styles.feedList}>
        {displayed.map((f) => (
          <div key={f.id} className={styles.feedItem}>
            <div className={styles.feedDot} />
            <div className={styles.feedBody}>
              <div className={styles.feedTop}>
                <span className={styles.feedMachine}>{f.machine}</span>
                <span className={styles.feedCode}>{f.fault_code}</span>
                <Badge status={f.status} />
              </div>
              <div className={styles.feedMeta}>
                {f.root_cause && <span className={styles.feedCause}>{f.root_cause}</span>}
                <span className={styles.feedTime}>{formatTime(f.created_at, t)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTime(ts, t) {
  if (!ts) return "";
  const diff = (Date.now() - new Date(ts).getTime()) / 1000;
  if (diff < 60) return t("dashboard.just_now");
  const mins = Math.floor(diff / 60);
  if (mins < 120) return `${mins} ${t("dashboard.min_ago")}`;
  return new Date(ts).toLocaleDateString();
}

const STAGE_KEYS = {
  fault_received: "dashboard.stage_fault_received",
  diagnosing: "dashboard.stage_diagnosing",
  work_order_created: "dashboard.stage_work_order_created",
  approved: "dashboard.stage_approved",
  dispatched: "dashboard.stage_dispatched",
  dispatch_failed: "dashboard.stage_dispatch_failed",
  rejected: "dashboard.stage_rejected",
};

function stageLabel(stage, t) {
  const key = STAGE_KEYS[stage];
  return key ? t(key) : stage;
}

function clockTime(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// Live pipeline log. Backfills from REST, then streams new stages over SSE
// (EventSource auto-reconnects on drop, so no polling and no manual retry).
function ActivityLog({ t }) {
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    let alive = true;
    api.getRecentActivity().then((rows) => {
      if (alive && Array.isArray(rows)) setEntries(rows);
    });
    const es = new EventSource(api.BASE + "/events/activity/stream");
    es.addEventListener("activity", (ev) => {
      try {
        const e = JSON.parse(ev.data);
        setEntries((prev) => [...prev, e].slice(-100));
      } catch {
        /* ignore malformed frame */
      }
    });
    es.onerror = () => setEntries((prev) => [...prev, { type: "disconnected", detail: t("dashboard.load_error") }]);
    return () => {
      alive = false;
      es.close();
    };
  }, []);

  const rows = [...entries].reverse().slice(0, 20); // newest first

  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>{t("dashboard.activity_log")}</div>
      {rows.length === 0 ? (
        <div className={styles.feedEmpty}>{t("dashboard.no_activity")}</div>
      ) : (
        <div className={styles.activityList}>
          {rows.map((e, i) => (
            <div key={i} className={styles.activityRow}>
              <span className={styles.activityTime}>{clockTime(e.ts)}</span>
              <span className={`${styles.activityStage} ${styles[e.stage] || ""}`}>
                {stageLabel(e.stage, t)}
              </span>
              <span className={styles.activityText}>
                {e.machine} {e.fault_code}
                {e.detail ? ` — ${e.detail}` : ""}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EvalCard({ data, t }) {
  if (!data || !data.configs?.length) return null;
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>
        {t("dashboard.retrieval_quality")} ({data.scenarios} {t("dashboard.eval_scenarios")})
      </div>
      {data.configs.map((c) => (
        <div className={styles.evalRow} key={c.config}>
          <span className={styles.evalLabel}>{c.config}</span>
          <span className={styles.evalBar}>
            <i style={{ width: `${Math.round((c.mrr || 0) * 100)}%` }} />
          </span>
          <span className={styles.evalVal}>{(c.mrr ?? 0).toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

function SavingsCalculator({ metrics, t }) {
  const [faults, setFaults] = useState(10);
  const [cost, setCost] = useState(50);
  const [baseline, setBaseline] = useState(60);

  const hasRealMetrics = metrics &&
    (Number(metrics?.avg_time_to_diagnosis_sec) > 0 || Number(metrics?.avg_time_to_fix_min) > 0);

  const torqDiagnosis = (metrics?.avg_time_to_diagnosis_sec || 0) / 60;
  const torqFix = metrics?.avg_time_to_fix_min || 0;
  const torqMttr = torqDiagnosis + torqFix;

  const savedMinsPerFault = Math.max(0, baseline - torqMttr);
  const savedHoursPerWeek = (savedMinsPerFault * faults) / 60;
  const savedMoneyPerWeek = savedMinsPerFault * faults * cost;
  const savedMoneyPerYear = savedMoneyPerWeek * 52;

  return (
    <div className={`${styles.card} ${styles.calcCard}`}>
      <div className={styles.cardHead}>{t("dashboard.roi_title")}</div>
      <div className={styles.calcGrid}>
        <div className={styles.calcInputs}>
          <label>
            <span>{t("dashboard.faults_per_week")}</span>
            <input type="number" value={faults} onChange={e => setFaults(Number(e.target.value))} />
          </label>
          <label>
            <span>{t("dashboard.downtime_cost")}</span>
            <input type="number" value={cost} onChange={e => setCost(Number(e.target.value))} />
          </label>
          <label>
            <span>{t("dashboard.baseline_mttr")}</span>
            <input type="number" value={baseline} onChange={e => setBaseline(Number(e.target.value))} />
          </label>
        </div>
        <div className={styles.calcOutputs}>
          <div className={styles.calcRes}>
            <small>{t("dashboard.hours_saved")}</small>
            <div className={styles.calcResRow}>
              <b className={styles.hours}>{savedHoursPerWeek.toFixed(1)}h</b>
              <span className={styles.calcFormula}>
                ({faults} faults &times; {savedMinsPerFault.toFixed(1)} min) &divide; 60
              </span>
            </div>
          </div>
          <div className={styles.calcRes}>
            <small>{t("dashboard.money_saved")}</small>
            <div className={styles.calcResRow}>
              <b className={styles.money}>${Math.round(savedMoneyPerYear).toLocaleString()}</b>
              <span className={styles.calcFormula}>
                ({faults} faults &times; {savedMinsPerFault.toFixed(1)} min &times; ${cost} &times; 52 wks)
              </span>
            </div>
          </div>
          <div className={styles.calcNote}>
            {hasRealMetrics ? (
              <div>{t("dashboard.based_on_measured")} {torqMttr.toFixed(1)} mins</div>
            ) : (
              <div>{t("dashboard.configure_assumptions")}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TrendChart({ data, t }) {
  if (!data || data.length === 0) {
    return (
      <div className={styles.card} style={{ minHeight: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className={styles.chartEmpty}>{t("dashboard.no_trend_data")}</span>
      </div>
    );
  }
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>{t("dashboard.trend")}</div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <ReTooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-color)", borderRadius: 8, fontSize: 12 }} />
          <Line type="monotone" dataKey="diagnosis" stroke="var(--text-primary)" strokeWidth={2} name={t("dashboard.diagnosis_label")} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="mttr" stroke="#1a8a3a" strokeWidth={2} name={t("dashboard.mttr_label")} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function FaultsPerMachineChart({ data, t }) {
  if (!data || data.length === 0) {
    return (
      <div className={styles.card} style={{ minHeight: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className={styles.chartEmpty}>{t("dashboard.no_machine_data")}</span>
      </div>
    );
  }
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>{t("dashboard.faults_per_machine")}</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="machine" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <ReTooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-color)", borderRadius: 8, fontSize: 12 }} />
          <Bar dataKey="count" fill="var(--text-primary)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function Drawer({ workOrder, onClose, onNotify, busy, t }) {
  const w = workOrder;
  if (!w) return null;
  const panelRef = useFocusTrap(!!w);

  const meta = [
    { key: "status", label: t("dashboard.status"), value: w.status },
    { key: "assigned", label: t("dashboard.assigned"), value: w.assigned_to },
    { key: "confidence", label: t("dashboard.confidence"), value: w.confidence != null ? `${(w.confidence * 100).toFixed(0)}%` : null },
    { key: "created", label: t("dashboard.created"), value: w.created_at ? new Date(w.created_at).toLocaleString() : null },
    { key: "resolved", label: t("dashboard.resolved"), value: w.resolved_at ? new Date(w.resolved_at).toLocaleString() : null },
  ].filter((m) => m.value);

  return (
    <div className={styles.drawer} onClick={onClose}>
      <div ref={panelRef} className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>{t("dashboard.close")}</button>
        <h3 className={styles.panelTitle}>{w.machine} &mdash; {w.fault_code}</h3>

        <div className={styles.drawerMeta}>
          {meta.map((m) => (
            <div key={m.key} className={styles.drawerMetaRow}>
              <span className={styles.drawerMetaLabel}>{m.label}</span>
              <span className={styles.drawerMetaVal}>
                {m.key === "status" ? <Badge status={m.value} /> : m.value}
              </span>
            </div>
          ))}
          <ConfidenceBadge confidence={w.confidence} t={t} />
        </div>

        <a className={styles.pdfLink} href={`/api/work-orders/${w.id}/pdf`} target="_blank" rel="noreferrer">
          {t("dashboard.download_pdf")}
        </a>

        <button className={styles.simBtn} style={{ marginTop: 12 }} disabled={busy} onClick={() => onNotify(w)}>
          {t("dashboard.send_whatsapp")}
        </button>

        {w.root_cause && <p className={styles.cause}>{w.root_cause}</p>}

        {w.repair_steps && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>{t("dashboard.repair_steps")}</div>
            <pre className={styles.drawerPre}>{w.repair_steps}</pre>
          </div>
        )}

        {w.parts?.length > 0 && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>{t("dashboard.parts")}</div>
            <ul className={styles.drawerUl}>
              {w.parts.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </div>
        )}

        {w.tools?.length > 0 && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>{t("dashboard.tools")}</div>
            <ul className={styles.drawerUl}>
              {w.tools.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          </div>
        )}

        {w.safety_warnings?.length > 0 && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>{t("dashboard.safety")}</div>
            <ul className={styles.drawerUl}>
              {w.safety_warnings.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        )}

        {w.sources?.length > 0 && (
          <div className={styles.sources}>
            <div className={styles.sourceLabel}>{t("dashboard.grounded_in")}</div>
            <ul>
              {w.sources.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        )}

        {w.investigation?.length > 0 && (
          <details className={styles.investigation}>
            <summary>{t("dashboard.agent_investigation")} ({w.investigation.length} {t("dashboard.steps")})</summary>
            <ol>
              {w.investigation.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          </details>
        )}

        {["en", "fr", "ar"].map((lng) =>
          w.content?.[lng] ? (
            <div key={lng} className={styles.langBlock}>
              <div className={styles.langLabel}>{lng.toUpperCase()}</div>
              <pre dir={lng === "ar" ? "rtl" : "ltr"}>{w.content[lng]}</pre>
            </div>
          ) : null
        )}
      </div>
    </div>
  );
}

function StatusFilter({ value, onChange, t }) {
  return (
    <select className={styles.filterSelect} value={value} onChange={(e) => onChange(e.target.value)} aria-label={t("dashboard.filter_by_status")}>
      <option value="">{t("dashboard.all_statuses")}</option>
      <option value="pending">{t("dashboard.pending")}</option>
      <option value="dispatched">{t("dashboard.dispatched")}</option>
      <option value="resolved">{t("dashboard.resolved")}</option>
      <option value="rejected">{t("dashboard.rejected")}</option>
    </select>
  );
}

function ManualFaultForm({ onReport, busy, t }) {
  const [open, setOpen] = useState(false);
  const [machine, setMachine] = useState("");
  const [faultCode, setFaultCode] = useState("");
  const [context, setContext] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!machine || !faultCode) return;
    onReport({ machine, fault_code: faultCode, context });
    setMachine("");
    setFaultCode("");
    setContext("");
    setOpen(false);
  };

  return (
    <div className={styles.manualForm}>
      <button className={styles.manualFormToggle} onClick={() => setOpen(!open)}>
        {open ? "−" : "+"} {t("dashboard.report_fault")}
      </button>
      {open && (
        <form className={styles.manualFormBody} onSubmit={handleSubmit}>
          <input
            className={styles.manualFormInput}
            placeholder={t("dashboard.machine_placeholder")}
            value={machine}
            onChange={(e) => setMachine(e.target.value)}
            required
          />
          <input
            className={styles.manualFormInput}
            placeholder={t("dashboard.fault_code_placeholder")}
            value={faultCode}
            onChange={(e) => setFaultCode(e.target.value)}
            required
          />
          <textarea
            className={styles.manualFormInput}
            placeholder={t("dashboard.context_placeholder")}
            value={context}
            onChange={(e) => setContext(e.target.value)}
            rows={2}
          />
          <button className={styles.approveBtn} type="submit" disabled={busy}>
            {t("dashboard.submit_fault")}
          </button>
        </form>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { t } = useI18n();
  const toast = useToast();

  const [metrics, setMetrics] = useState(null);
  const [evalData, setEvalData] = useState(null);
  const [pending, setPending] = useState([]);
  const [all, setAll] = useState([]);
  const [trendData, setTrendData] = useState(null);
  const [fpmData, setFpmData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [machineDetail, setMachineDetail] = useState(null);
  const [confirmReject, setConfirmReject] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [errored, setErrored] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const deferredQuery = useDeferredValue(searchQuery);

  const inflight = useRef(false);
  const load = useCallback(async () => {
    if (inflight.current) return;
    inflight.current = true;
    try {
      const [m, p, a, ev, trend, fpm] = await Promise.all([
        api.getMetrics(),
        api.getWorkOrders("pending"),
        api.getWorkOrders(),
        api.getEval().catch(() => null),
        api.getTrend(),
        api.getFaultsPerMachine(),
      ]);
      setMetrics(m);
      setPending(p);
      setAll(a);
      setEvalData(ev);
      setTrendData(trend);
      setFpmData(fpm);
      setLoading(false);
      setErrored(false);
    } catch (e) {
      setLoading(false);
      setErrored(true);
    } finally {
      inflight.current = false;
    }
  }, []);

  useEffect(() => {
    load();
    const tId = setInterval(load, 4000);
    return () => clearInterval(tId);
  }, [load]);

  useEffect(() => {
    if (!selected && !machineDetail) return;
    const handler = (e) => { if (e.key === "Escape") { setSelected(null); setMachineDetail(null); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selected, machineDetail]);

  const act = async (fn, toastMsg, toastType = "success") => {
    setBusy(true);
    try {
      await fn();
      if (toastMsg) toast(toastMsg, toastType);
      await load();
    } catch (e) {
      toast(String(e.message || e), "error");
    } finally {
      setBusy(false);
    }
  };

  const simulate = () =>
    act(
      () => api.reportFault(SIM_FAULTS[Math.floor(Math.random() * SIM_FAULTS.length)]),
      t("dashboard.toast_simulated")
    );

  const sortedFaults = useMemo(() => {
    return [...all]
      .filter((w) => w.created_at)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 10);
  }, [all]);

  const filteredAll = useMemo(() => {
    let list = all;
    if (statusFilter) {
      list = list.filter((w) => w.status === statusFilter);
    }
    if (deferredQuery) {
      const q = deferredQuery.toLowerCase();
      list = list.filter((w) =>
        (w.machine || "").toLowerCase().includes(q) ||
        (w.fault_code || "").toLowerCase().includes(q) ||
        (w.root_cause || "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [all, statusFilter, searchQuery]);

  const pct = (x) => (x == null || x === 0 ? "—" : Math.round(x * 100) + "%");
  const secs = (x) => (x == null || x === 0 ? "—" : x + "s");
  const mins = (x) => (x == null || x === 0 ? "—" : x + " min");

  return (
    <div className={styles.page}>
      <a href="#main-content" className="skip-link">{t("nav.skip_to_content")}</a>
      <Navbar />

      <main id="main-content" className={styles.app}>
        <header className={styles.header}>
          <h1 className={styles.heading}>{t("dashboard.title")}</h1>
          <p className={styles.sub}>{t("dashboard.subtitle")}</p>
        </header>

        {errored && <div className="dashboardError">{t("dashboard.load_error")}</div>}

        <section className={styles.tiles}>
          {loading ? (
            <>
              <div className={styles.tile}><Skeleton height={32} width={80} /><Skeleton height={14} width={120} style={{ marginTop: 8 }} /></div>
              <div className={styles.tile}><Skeleton height={32} width={80} /><Skeleton height={14} width={120} style={{ marginTop: 8 }} /></div>
              <div className={styles.tile}><Skeleton height={32} width={80} /><Skeleton height={14} width={120} style={{ marginTop: 8 }} /></div>
              <div className={styles.tile}><Skeleton height={32} width={80} /><Skeleton height={14} width={120} style={{ marginTop: 8 }} /></div>
            </>
          ) : (
            <>
              <Tile label={t("dashboard.total")} value={metrics?.total_work_orders ?? "-"} />
              <Tile label={t("dashboard.avg_diag")} value={secs(metrics?.avg_time_to_diagnosis_sec)} />
              <Tile label={t("dashboard.avg_fix")} value={mins(metrics?.avg_time_to_fix_min)} />
              <Tile label={t("dashboard.res_rate")} value={pct(metrics?.resolution_rate)} />
            </>
          )}
        </section>

        <LiveFeed faults={sortedFaults} t={t} />

        <ActivityLog t={t} />

        <div className={styles.grid}>
          {loading ? (
            <>
              <div className={styles.card}><Skeleton height={14} width={180} /><Skeleton height={10} style={{ marginTop: 16 }} /><Skeleton height={10} style={{ marginTop: 8 }} /><Skeleton height={10} style={{ marginTop: 8 }} /></div>
              <div className={styles.card}><Skeleton height={14} width={180} /><Skeleton height={10} style={{ marginTop: 16 }} /><Skeleton height={10} style={{ marginTop: 8 }} /></div>
            </>
          ) : (
            <>
              <EvalCard data={evalData} t={t} />
              <SavingsCalculator metrics={metrics} t={t} />
            </>
          )}
        </div>

        {loading ? (
          <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
            <div className={styles.card} style={{ flex: 1 }}><Skeleton height={200} /></div>
            <div className={styles.card} style={{ flex: 1 }}><Skeleton height={200} /></div>
          </div>
        ) : (
          <div className={styles.grid}>
            <TrendChart data={trendData} t={t} />
            <FaultsPerMachineChart data={fpmData} t={t} />
          </div>
        )}

        <div className={styles.actionRow}>
          <button className={styles.simBtn} disabled={busy || loading} onClick={simulate}>
            {t("dashboard.simulate")}
          </button>
          <ManualFaultForm onReport={(msg) => act(() => api.reportFault(msg), t("dashboard.toast_simulated"))} busy={busy} t={t} />
        </div>

        <h2 className={styles.sectionTitle}>{t("dashboard.pending")}</h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>{t("dashboard.id")}</th>
                <th>{t("dashboard.machine")}</th>
                <th>{t("dashboard.fault")}</th>
                <th>{t("dashboard.cause")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className={styles.muted}>{t("dashboard.loading")}</td></tr>
              ) : pending.length === 0 ? (
                <tr><td colSpan={5} className={styles.muted}>{t("dashboard.queue_empty")}</td></tr>
              ) : (
                pending.map((w) => (
                  <tr key={w.id}>
                    <td><a className={styles.link} onClick={() => setSelected(w)}>{w.id}</a></td>
                    <td>{w.machine ? <a className={styles.link} onClick={() => setMachineDetail(w.machine)}>{w.machine}</a> : "-"}</td>
                    <td>{w.fault_code} <ConfidenceBadge confidence={w.confidence} t={t} /></td>
                    <td className={styles.cause}>{w.root_cause}</td>
                    <td className={styles.actions}>
                      <button className={styles.approveBtn} disabled={busy} onClick={() => act(() => api.approve(w.id), `${t("dashboard.toast_approved")} — ${w.id}`)}>
                        {t("dashboard.approve")}
                      </button>
                      <button className={styles.rejectBtn} disabled={busy} onClick={() => setConfirmReject(w)}>
                        {t("dashboard.reject")}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <h2 className={styles.sectionTitle}>{t("dashboard.all")}</h2>
        <div className={styles.toolbar}>
          <StatusFilter value={statusFilter} onChange={setStatusFilter} t={t} />
          <div className={styles.searchWrap}>
            <input
              className={styles.searchInput}
              type="text"
              placeholder={t("dashboard.search")}
              aria-label={t("dashboard.search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className={styles.clearBtn} onClick={() => setSearchQuery("")} aria-label={t("dashboard.clear_search")}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>{t("dashboard.id")}</th>
                <th>{t("dashboard.machine")}</th>
                <th>{t("dashboard.fault")}</th>
                <th>{t("dashboard.status")}</th>
                <th>{t("dashboard.assigned")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className={styles.muted}>{t("dashboard.loading")}</td></tr>
              ) : filteredAll.length === 0 ? (
                <tr><td colSpan={6} className={styles.muted}>{t("dashboard.no_orders")}</td></tr>
              ) : (
                filteredAll.map((w) => (
                  <tr key={w.id}>
                    <td><a className={styles.link} onClick={() => setSelected(w)}>{w.id}</a></td>
                    <td>{w.machine ? <a className={styles.link} onClick={() => setMachineDetail(w.machine)}>{w.machine}</a> : "-"}</td>
                    <td>{w.fault_code}</td>
                    <td><Badge status={w.status} /></td>
                    <td>{w.assigned_to || "-"}</td>
                    <td>
                      {w.status === "dispatched" && (
                        <button className={styles.approveBtn} disabled={busy} onClick={() => act(() => api.recordOutcome(w.id, FIX), `${t("dashboard.toast_fixed")} — ${w.id}`)}>
                          {t("dashboard.mark_fixed")}
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <Drawer
          workOrder={selected}
          onClose={() => setSelected(null)}
          onNotify={(w) => act(() => api.notify(w.id), t("dashboard.whatsapp_sent"))}
          busy={busy}
          t={t}
        />

        <ConfirmDialog
          open={!!confirmReject}
          message={t("dashboard.confirm_reject")}
          confirmLabel={t("dashboard.reject")}
          cancelLabel={t("dashboard.cancel")}
          onConfirm={() => {
            const w = confirmReject;
            setConfirmReject(null);
            act(() => api.reject(w.id), `${t("dashboard.toast_rejected")} — ${w.id}`);
          }}
          onCancel={() => setConfirmReject(null)}
          busy={busy}
        />

        <MachineDrawer
          machine={machineDetail}
          workOrders={all}
          downtime={metrics?.machine_downtime?.find((m) => m.machine_id === machineDetail)}
          onClose={() => setMachineDetail(null)}
          onSelectWorkOrder={(w) => {
            setMachineDetail(null);
            setSelected(w);
          }}
          t={t}
        />

        <p className={styles.footer}>{t("dashboard.footer")}</p>
      </main>
    </div>
  );
}
