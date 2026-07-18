// Thin client for the TORQ REST API (proxied to the FastAPI backend in dev).
const BASE = "/api";

async function j(path, opts) {
  const res = await fetch(BASE + path, opts);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.status === 204 ? null : res.json();
}

export const getMetrics = () => j("/metrics");
export const getWorkOrders = (status) =>
  j("/work-orders" + (status ? `?status=${status}` : ""));

export const reportFault = (body) =>
  j("/faults", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const approve = (id) => j(`/work-orders/${id}/approve`, { method: "POST" });
export const reject = (id) => j(`/work-orders/${id}/reject`, { method: "POST" });
export const recordOutcome = (id, body) =>
  j(`/work-orders/${id}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
