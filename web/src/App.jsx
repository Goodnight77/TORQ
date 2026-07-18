import { useEffect, useState, useCallback } from "react";
import * as api from "./api.js";

const FIX = {
  resolved: true,
  actual_fix: "Applied recommended fix; verified stable.",
  time_to_fix_min: 30,
};

function Tile({ label, value }) {
  return (
    <div className="tile">
      <b>{value}</b>
      <small>{label}</small>
    </div>
  );
}

function Badge({ status }) {
  return <span className={`badge ${status}`}>{status}</span>;
}

function EvalCard({ data }) {
  if (!data || !data.configs?.length) return null;
  return (
    <div className="evalcard">
      <div className="evalhead">
        Retrieval quality - MRR ({data.scenarios} labeled scenarios)
      </div>
      {data.configs.map((c) => (
        <div className="evalrow" key={c.config}>
          <span className="evallabel">{c.config}</span>
          <span className="evalbar">
            <i style={{ width: `${Math.round((c.mrr || 0) * 100)}%` }} />
          </span>
          <span className="evalval">{(c.mrr ?? 0).toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

function SavingsCalculator({ metrics }) {
  const [faults, setFaults] = useState(10);
  const [cost, setCost] = useState(50);
  const [baseline, setBaseline] = useState(60);

  const torqDiagnosis = (metrics?.avg_time_to_diagnosis_sec || 0) / 60;
  const torqFix = metrics?.avg_time_to_fix_min || 0;
  let torqMttr = torqDiagnosis + torqFix;
  let isEstimate = false;

  if (torqMttr === 0) {
    torqMttr = 5;
    isEstimate = true;
  }

  const savedMinsPerFault = Math.max(0, baseline - torqMttr);
  const savedHoursPerWeek = (savedMinsPerFault * faults) / 60;
  const savedMoneyPerWeek = savedMinsPerFault * faults * cost;
  const savedMoneyPerYear = savedMoneyPerWeek * 52;

  return (
    <div className="evalcard calc-card">
      <div className="evalhead">ROI & Savings Calculator</div>
      <div className="calc-grid">
        <div className="calc-inputs">
          <label>
            <span>Faults / week</span>
            <input type="number" value={faults} onChange={e => setFaults(Number(e.target.value))} />
          </label>
          <label>
            <span>Downtime cost / min ($)</span>
            <input type="number" value={cost} onChange={e => setCost(Number(e.target.value))} />
          </label>
          <label>
            <span>Baseline MTTR (min)</span>
            <input type="number" value={baseline} onChange={e => setBaseline(Number(e.target.value))} />
          </label>
        </div>
        <div className="calc-outputs">
          <div className="calc-res">
            <small>Hours saved / week</small>
            <div className="calc-res-row">
              <b>{savedHoursPerWeek.toFixed(1)}h</b>
              <span className="calc-formula">
                ({faults} faults × {savedMinsPerFault.toFixed(1)} min saved) / 60
              </span>
            </div>
          </div>
          <div className="calc-res">
            <small>Money saved / year</small>
            <div className="calc-res-row">
              <b className="money">${Math.round(savedMoneyPerYear).toLocaleString()}</b>
              <span className="calc-formula">
                ({faults} faults × {savedMinsPerFault.toFixed(1)} min × ${cost} × 52 wks)
              </span>
            </div>
          </div>
          <div className="calc-note">
            {isEstimate ? (
              <div>*based on est. TORQ avg MTTR of {torqMttr.toFixed(1)} mins</div>
            ) : (
              <div>*based on measured TORQ avg MTTR of {torqMttr.toFixed(1)} mins</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [evalData, setEvalData] = useState(null);
  const [pending, setPending] = useState([]);
  const [all, setAll] = useState([]);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    try {
      const [m, p, a, ev] = await Promise.all([
        api.getMetrics(),
        api.getWorkOrders("pending"),
        api.getWorkOrders(),
        api.getEval().catch(() => null),
      ]);
      setMetrics(m);
      setPending(p);
      setAll(a);
      setEvalData(ev);
      setErr(null);
    } catch (e) {
      setErr("Backend unreachable. Start it: uv run uvicorn torq.api.main:app");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  const act = async (fn) => {
    setBusy(true);
    try {
      await fn();
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const simulate = () =>
    act(() =>
      api.reportFault({
        fault_code: "E-471",
        machine: "CM-350 Line 2",
        context: "Motor tripped after hours running.",
      })
    );

  const pct = (x) => (x == null ? "-" : Math.round(x * 100) + "%");
  const secs = (x) => (x == null ? "-" : x + "s");
  const mins = (x) => (x == null ? "-" : x + " min");

  return (
    <div className="app">
      <header>
        <h1>
          <img src="/logos/inline_logo.svg" alt="TORQ" />
        </h1>
        <div className="sub">Supervisor and downtime dashboard</div>
      </header>

      {err && <div className="err">{err}</div>}

      <section className="tiles">
        <Tile label="Total work orders" value={metrics?.total_work_orders ?? "-"} />
        <Tile label="Avg time to diagnosis" value={secs(metrics?.avg_time_to_diagnosis_sec)} />
        <Tile label="Avg time to fix" value={mins(metrics?.avg_time_to_fix_min)} />
        <Tile label="Resolution rate" value={pct(metrics?.resolution_rate)} />
      </section>

      <div className="dashboard-grid">
        <EvalCard data={evalData} />
        <SavingsCalculator metrics={metrics} />
      </div>

      <button className="sim" disabled={busy} onClick={simulate}>
        Simulate fault (E-471, CM-350 Line 2)
      </button>

      <h2>Pending approval</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Machine</th>
            <th>Fault</th>
            <th>Root cause</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {pending.length === 0 && (
            <tr>
              <td colSpan={5} className="muted">
                Queue empty
              </td>
            </tr>
          )}
          {pending.map((w) => (
            <tr key={w.id}>
              <td>
                <a onClick={() => setSelected(w)}>{w.id}</a>
              </td>
              <td>{w.machine}</td>
              <td>{w.fault_code}</td>
              <td className="cause">{w.root_cause}</td>
              <td className="actions">
                <button className="approve" disabled={busy} onClick={() => act(() => api.approve(w.id))}>
                  Approve
                </button>
                <button className="r" disabled={busy} onClick={() => act(() => api.reject(w.id))}>
                  Reject
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>All work orders</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Machine</th>
            <th>Fault</th>
            <th>Status</th>
            <th>Assigned</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {all.map((w) => (
            <tr key={w.id}>
              <td>
                <a onClick={() => setSelected(w)}>{w.id}</a>
              </td>
              <td>{w.machine}</td>
              <td>{w.fault_code}</td>
              <td>
                <Badge status={w.status} />
              </td>
              <td>{w.assigned_to || "-"}</td>
              <td>
                {w.status === "dispatched" && (
                  <button className="approve" disabled={busy} onClick={() => act(() => api.recordOutcome(w.id, FIX))}>
                    Mark fixed
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <div className="drawer" onClick={() => setSelected(null)}>
          <div className="panel" onClick={(e) => e.stopPropagation()}>
            <button className="close" onClick={() => setSelected(null)}>
              close
            </button>
            <h3>
              {selected.machine} - {selected.fault_code}
            </h3>
            <a className="pdf" href={`/api/work-orders/${selected.id}/pdf`} target="_blank" rel="noreferrer">
              Download PDF (EN/FR/AR)
            </a>
            <p className="cause">{selected.root_cause}</p>
            {selected.sources?.length > 0 && (
              <div className="sources">
                <div className="langlabel">Grounded in</div>
                <ul>
                  {selected.sources.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            {["en", "fr", "ar"].map((lng) =>
              selected.content?.[lng] ? (
                <div key={lng} className="lang">
                  <div className="langlabel">{lng.toUpperCase()}</div>
                  <pre dir={lng === "ar" ? "rtl" : "ltr"}>{selected.content[lng]}</pre>
                </div>
              ) : null
            )}
          </div>
        </div>
      )}

      <footer>From fault code to fixed.</footer>
    </div>
  );
}
