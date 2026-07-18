export const BASE = import.meta.env.VITE_API_URL || "/api";

async function j(path, opts) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const res = await fetch(BASE + path, { ...opts, signal: controller.signal });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.status === 204 ? null : res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export const getMetrics = () => j("/metrics");
export const getEval = () => j("/eval");
export const getWorkOrders = (status) =>
  j("/work-orders" + (status ? `?status=${status}` : ""));

export const getTrend = () =>
  j("/metrics/trend").catch(() => null);

export const getFaultsPerMachine = () =>
  j("/metrics/faults-per-machine").catch(() => null);

export const getRecentActivity = () =>
  j("/events/activity/recent").catch(() => []);

export const reportFault = (body) =>
  j("/faults", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const approve = (id) => j(`/work-orders/${id}/approve`, { method: "POST" });
export const reject = (id) => j(`/work-orders/${id}/reject`, { method: "POST" });
export const notify = (id) => j(`/work-orders/${id}/notify`, { method: "POST" });
export const recordOutcome = (id, body) =>
  j(`/work-orders/${id}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const getHealth = () => j("/health").catch(() => null);
