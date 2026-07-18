"""FastAPI entrypoint: REST API + a self-contained supervisor/downtime dashboard.

Run:  uv run uvicorn torq.api.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from torq.api.routes import router
from torq.db import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.init_db()
    yield


app = FastAPI(title="TORQ — Fault-to-Fix Engine", lifespan=lifespan)
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


DASHBOARD_HTML = """
<!doctype html><html><head><meta charset="utf-8">
<title>TORQ Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{font:15px system-ui,sans-serif;margin:0;background:#0f1720;color:#e6edf3}
  header{padding:16px 24px;background:#111c28;border-bottom:1px solid #223}
  h1{font-size:18px;margin:0}h1 span{color:#3fb950}
  main{padding:24px;max-width:1000px;margin:0 auto}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:24px}
  .tile{background:#111c28;border:1px solid #223;border-radius:10px;padding:16px}
  .tile b{display:block;font-size:26px;color:#3fb950}.tile small{color:#8b98a5}
  table{width:100%;border-collapse:collapse;background:#111c28;border-radius:10px;overflow:hidden}
  th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #223;font-size:14px}
  th{color:#8b98a5;font-weight:600}
  .st{padding:2px 8px;border-radius:20px;font-size:12px}
  .pending{background:#3a2d00;color:#e3b341}.dispatched{background:#0d3320;color:#3fb950}
  .resolved{background:#132f5e;color:#79c0ff}.rejected,.failed{background:#3d1a1a;color:#f85149}
  button{background:#238636;color:#fff;border:0;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:13px}
  button.r{background:#8b3232;margin-left:6px}button.sim{background:#1f6feb}
  h2{font-size:15px;color:#8b98a5;margin:24px 0 8px}
</style></head><body>
<header><h1>TORQ <span>Fault-to-Fix</span> — Supervisor Dashboard</h1></header>
<main>
  <div class="tiles" id="tiles"></div>
  <button class="sim" onclick="simulate()">⚡ Simulate fault (E-471, CM-350 Line 2)</button>
  <h2>PENDING APPROVAL</h2><table id="pending"></table>
  <h2>ALL WORK ORDERS</h2><table id="all"></table>
</main>
<script>
const api = p => fetch('/api'+p).then(r=>r.json());
const post = p => fetch('/api'+p,{method:'POST'}).then(r=>r.json());

async function simulate(){
  await fetch('/api/faults',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({fault_code:'E-471',machine:'CM-350 Line 2',context:'Motor tripped after hours running.'})});
  load();
}
async function approve(id){await post('/work-orders/'+id+'/approve');load();}
async function reject(id){await post('/work-orders/'+id+'/reject');load();}
async function resolve(id){
  await fetch('/api/work-orders/'+id+'/outcome',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({resolved:true,actual_fix:'Cleaned louvers, replaced filter mat AF-12',time_to_fix_min:30})});
  load();
}
const badge = s => `<span class="st ${s}">${s}</span>`;

async function load(){
  const m = await api('/metrics');
  document.getElementById('tiles').innerHTML = [
    ['Total work orders', m.total_work_orders],
    ['Avg time to diagnosis', m.avg_time_to_diagnosis_sec!=null?m.avg_time_to_diagnosis_sec+'s':'—'],
    ['Avg time to fix', m.avg_time_to_fix_min!=null?m.avg_time_to_fix_min+' min':'—'],
    ['Resolution rate', m.resolution_rate!=null?Math.round(m.resolution_rate*100)+'%':'—'],
  ].map(([l,v])=>`<div class="tile"><b>${v}</b><small>${l}</small></div>`).join('');

  const pend = await api('/work-orders?status=pending');
  document.getElementById('pending').innerHTML =
    '<tr><th>ID</th><th>Machine</th><th>Fault</th><th>Root cause</th><th></th></tr>'+
    (pend.length?pend.map(w=>`<tr><td>${w.id}</td><td>${w.machine}</td><td>${w.fault_code}</td>
      <td>${(w.root_cause||'').slice(0,60)}…</td>
      <td><button onclick="approve('${w.id}')">Approve</button>
      <button class="r" onclick="reject('${w.id}')">Reject</button></td></tr>`).join('')
     :'<tr><td colspan=5 style="color:#8b98a5">Queue empty</td></tr>');

  const all = await api('/work-orders');
  document.getElementById('all').innerHTML =
    '<tr><th>ID</th><th>Machine</th><th>Fault</th><th>Status</th><th>Assigned</th><th></th></tr>'+
    all.map(w=>`<tr><td>${w.id}</td><td>${w.machine}</td><td>${w.fault_code}</td>
      <td>${badge(w.status)}</td><td>${w.assigned_to||'—'}</td>
      <td>${w.status==='dispatched'?`<button onclick="resolve('${w.id}')">Mark fixed</button>`:''}</td></tr>`).join('');
}
load(); setInterval(load, 4000);
</script></body></html>
"""
