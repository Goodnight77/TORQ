import { useEffect, useState, useCallback, useMemo } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import * as api from "../api.js";
import Navbar from "../components/Navbar.jsx";
import { useI18n } from "../i18n";
import { useToast } from "../toast.jsx";
import styles from "./Dashboard.module.css";

const CONFIDENCE_THRESHOLD = 0.6;

const FIX = {
  resolved: true,
  actual_fix: "Applied recommended fix; verified stable.",
  time_to_fix_min: 30,
};

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

function MachineDrawer({ machine, workOrders, downtime, onClose, onSelectWorkOrder }) {
  if (!machine) return null;
  const history = workOrders.filter((w) => w.machine === machine);
  const open = history.filter((w) => OPEN_STATUS.has(w.status));
  const model = downtime?.model || machine;
  const location = downtime?.location;

  return (
    <div className={styles.drawer} onClick={onClose}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>close</button>
        <h3 className={styles.panelTitle}>{machine}</h3>
        <p className={styles.sub}>{model}{location ? ` - ${location}` : ""}</p>

        <section className={styles.tiles} style={{ margin: "16px 0" }}>
          <Tile label="Total downtime" value={`${downtime?.downtime_min ?? 0} min`} />
          <Tile label="Work orders" value={history.length} />
          <Tile label="Open faults" value={open.length} />
        </section>

        <div className={styles.langLabel}>Open faults</div>
        {open.length === 0 ? (
          <p className={styles.muted}>None open.</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>ID</th><th>Fault</th><th>Status</th><th>Root cause</th></tr>
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

        <div className={styles.langLabel} style={{ marginTop: 24 }}>Work-order history</div>
        {history.length === 0 ? (
          <p className={styles.muted}>No work orders for this machine.</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>ID</th><th>Fault</th><th>Status</th><th>Created</th></tr>
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

function ConfidenceBadge({ confidence }) {
  if (confidence == null) return null;
  const low = confidence < CONFIDENCE_THRESHOLD;
  return (
    <span className={`${styles.badge} ${low ? styles.lowConfidence : styles.highConfidence}`}>
      {low ? "Needs human review" : `${(confidence * 100).toFixed(0)}%`}
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
        <div className={styles.feedEmpty}>No recent faults detected</div>
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

function EvalCard({ data }) {
  if (!data || !data.configs?.length) return null;
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>
        Retrieval quality &mdash; MRR ({data.scenarios} labeled scenarios)
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
              <div>*based on measured TORQ avg MTTR of {torqMttr.toFixed(1)} mins</div>
            ) : (
              <div>*configure your assumptions above to preview savings</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TrendChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className={styles.card} style={{ minHeight: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className={styles.chartEmpty}>No trend data yet</span>
      </div>
    );
  }
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>Time-to-diagnosis / MTTR trend</div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
          <ReTooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-color)", borderRadius: 8, fontSize: 12 }} />
          <Line type="monotone" dataKey="diagnosis" stroke="var(--text-primary)" strokeWidth={2} name="Diagnosis (s)" dot={{ r: 3 }} />
          <Line type="monotone" dataKey="mttr" stroke="#1a8a3a" strokeWidth={2} name="MTTR (min)" dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function FaultsPerMachineChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className={styles.card} style={{ minHeight: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className={styles.chartEmpty}>No machine data yet</span>
      </div>
    );
  }
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>Faults per machine</div>
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

function Drawer({ workOrder, onClose }) {
  const w = workOrder;
  if (!w) return null;

  const meta = [
    { label: "Status", value: w.status },
    { label: "Assigned to", value: w.assigned_to },
    { label: "Confidence", value: w.confidence != null ? `${(w.confidence * 100).toFixed(0)}%` : null },
    { label: "Created", value: w.created_at ? new Date(w.created_at).toLocaleString() : null },
    { label: "Resolved", value: w.resolved_at ? new Date(w.resolved_at).toLocaleString() : null },
  ].filter((m) => m.value);

  return (
    <div className={styles.drawer} onClick={onClose}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>close</button>
        <h3 className={styles.panelTitle}>{w.machine} &mdash; {w.fault_code}</h3>

        <div className={styles.drawerMeta}>
          {meta.map((m) => (
            <div key={m.label} className={styles.drawerMetaRow}>
              <span className={styles.drawerMetaLabel}>{m.label}</span>
              <span className={styles.drawerMetaVal}>
                {m.label === "Status" ? <Badge status={m.value} /> : m.value}
              </span>
            </div>
          ))}
          <ConfidenceBadge confidence={w.confidence} />
        </div>

        <a className={styles.pdfLink} href={`/api/work-orders/${w.id}/pdf`} target="_blank" rel="noreferrer">
          Download PDF (EN/FR/AR)
        </a>

        {w.root_cause && <p className={styles.cause}>{w.root_cause}</p>}

        {w.repair_steps && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>Repair steps</div>
            <pre className={styles.drawerPre}>{w.repair_steps}</pre>
          </div>
        )}

        {w.parts?.length > 0 && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>Parts</div>
            <ul className={styles.drawerUl}>
              {w.parts.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </div>
        )}

        {w.tools?.length > 0 && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>Tools</div>
            <ul className={styles.drawerUl}>
              {w.tools.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          </div>
        )}

        {w.safety_warnings?.length > 0 && (
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionLabel}>Safety warnings</div>
            <ul className={styles.drawerUl}>
              {w.safety_warnings.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        )}

        {w.sources?.length > 0 && (
          <div className={styles.sources}>
            <div className={styles.sourceLabel}>Grounded in</div>
            <ul>
              {w.sources.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        )}

        {w.investigation?.length > 0 && (
          <details className={styles.investigation}>
            <summary>Agent investigation ({w.investigation.length} steps)</summary>
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
    <select className={styles.filterSelect} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">{t("dashboard.all_statuses")}</option>
      <option value="pending">Pending</option>
      <option value="dispatched">Dispatched</option>
      <option value="resolved">Resolved</option>
      <option value="rejected">Rejected</option>
    </select>
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
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const load = useCallback(async () => {
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
    } catch (e) {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const tId = setInterval(load, 4000);
    return () => clearInterval(tId);
  }, [load]);

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
      () => api.reportFault({
        fault_code: "E-471",
        machine: "CM-350 Line 2",
        context: "Motor tripped after hours running.",
      }),
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
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
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
      <Navbar />

      <div className={styles.app}>
        <header className={styles.header}>
          <h1 className={styles.heading}>{t("dashboard.title")}</h1>
          <p className={styles.sub}>{t("dashboard.subtitle")}</p>
        </header>

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

        <div className={styles.grid}>
          {loading ? (
            <>
              <div className={styles.card}><Skeleton height={14} width={180} /><Skeleton height={10} style={{ marginTop: 16 }} /><Skeleton height={10} style={{ marginTop: 8 }} /><Skeleton height={10} style={{ marginTop: 8 }} /></div>
              <div className={styles.card}><Skeleton height={14} width={180} /><Skeleton height={10} style={{ marginTop: 16 }} /><Skeleton height={10} style={{ marginTop: 8 }} /></div>
            </>
          ) : (
            <>
              <EvalCard data={evalData} />
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
            <TrendChart data={trendData} />
            <FaultsPerMachineChart data={fpmData} />
          </div>
        )}

        <button className={styles.simBtn} disabled={busy || loading} onClick={simulate}>
          {t("dashboard.simulate")}
        </button>

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
                <tr><td colSpan={5} className={styles.muted}>Loading…</td></tr>
              ) : pending.length === 0 ? (
                <tr><td colSpan={5} className={styles.muted}>{t("dashboard.queue_empty")}</td></tr>
              ) : (
                pending.map((w) => (
                  <tr key={w.id}>
                    <td><a className={styles.link} onClick={() => setSelected(w)}>{w.id}</a></td>
                    <td>{w.machine ? <a className={styles.link} onClick={() => setMachineDetail(w.machine)}>{w.machine}</a> : "-"}</td>
                    <td>{w.fault_code} <ConfidenceBadge confidence={w.confidence} /></td>
                    <td className={styles.cause}>{w.root_cause}</td>
                    <td className={styles.actions}>
                      <button className={styles.approveBtn} disabled={busy} onClick={() => act(() => api.approve(w.id), `${t("dashboard.toast_approved")} — ${w.id}`)}>
                        {t("dashboard.approve")}
                      </button>
                      <button className={styles.rejectBtn} disabled={busy} onClick={() => act(() => api.reject(w.id), `${t("dashboard.toast_rejected")} — ${w.id}`)}>
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
          <input
            className={styles.searchInput}
            type="text"
            placeholder={t("dashboard.search")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
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
                <tr><td colSpan={6} className={styles.muted}>Loading…</td></tr>
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

        <Drawer workOrder={selected} onClose={() => setSelected(null)} />

        <MachineDrawer
          machine={machineDetail}
          workOrders={all}
          downtime={metrics?.machine_downtime?.find((m) => m.machine_id === machineDetail)}
          onClose={() => setMachineDetail(null)}
          onSelectWorkOrder={(w) => {
            setMachineDetail(null);
            setSelected(w);
          }}
        />

        <p className={styles.footer}>{t("dashboard.footer")}</p>
      </div>
    </div>
  );
}
