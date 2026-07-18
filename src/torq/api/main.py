"""FastAPI entrypoint: REST API + a self-contained supervisor/downtime dashboard.

Run:  uv run uvicorn torq.api.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from torq.api.routes import router
from torq.config import settings
from torq.db import models
from torq.events import listener


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    import asyncio
    from torq.events import live
    live.loop = asyncio.get_running_loop()

    models.init_db()
    mqtt_client = None
    if settings.enable_fallbacks:
        print("[MQTT] fallbacks enabled, skipping broker connection")
    else:
        mqtt_client = listener.build_client()
        live.mqtt_client = mqtt_client
        try:
            mqtt_client.connect(
                settings.mqtt_broker_url,
                settings.mqtt_port,
                keepalive=60,
            )
            mqtt_client.loop_start()
            print("[MQTT] background listener started")
        except Exception as exc:
            print(f"[MQTT] broker unreachable ({exc}), continuing without live feed")
            mqtt_client = None
            live.mqtt_client = None
    yield
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("[MQTT] listener stopped")
    live.mqtt_client = None


app = FastAPI(title="TORQ - Fault-to-Fix Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: allow the SPA dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


DASHBOARD_HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<title>TORQ Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{font:15px system-ui,sans-serif;margin:0;background:#0f1720;color:#e6edf3}
  header{padding:16px 24px;background:#111c28;border-bottom:1px solid #223;display:flex;align-items:center;gap:12px}
  h1{font-size:18px;margin:0}h1 span{color:#3fb950}
  .status-dot{width:10px;height:10px;border-radius:50%;display:inline-block}
  .status-dot.connected{background:#3fb950}
  .status-dot.disconnected{background:#f85149}
  main{padding:24px;max-width:1100px;margin:0 auto}
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
  #live-feed{max-height:280px;overflow-y:auto;background:#0d1a28;border:1px solid #1a3040;border-radius:10px;margin-bottom:20px}
  #live-feed table{background:transparent}#live-feed td{padding:6px 12px;font-size:13px}
  @keyframes flash{0%{background:rgba(63,185,80,.25)}100%{background:transparent}}
  .flash{animation:flash 1.5s ease-out}
  .sev-1{color:#3fb950}.sev-2{color:#7ee97e}.sev-3{color:#e3b341}.sev-4{color:#f0883e}.sev-5{color:#f85149}
  .sev-badge{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
  .sev-badge.s1{background:#3fb950}.sev-badge.s2{background:#7ee97e}.sev-badge.s3{background:#e3b341}
  .sev-badge.s4{background:#f0883e}.sev-badge.s5{background:#f85149}
  .feed-empty{color:#4a5a6a;padding:20px;text-align:center;font-style:italic}
  .mqtt-status{font-size:13px;color:#8b98a5;margin-left:auto}
</style></head><body>
<header>
  <h1>TORQ <span>Fault-to-Fix</span> &mdash; Supervisor Dashboard</h1>
  <span class="mqtt-status"><span class="status-dot disconnected" id="mqtt-dot"></span> MQTT <span id="mqtt-label">disconnected</span></span>
</header>
<main>
  <div class="tiles" id="tiles"></div>

  <h2>&#9889; LIVE FAULT FEED</h2>
  <div id="live-feed"><div class="feed-empty">Waiting for faults&hellip;</div></div>

  <button class="sim" onclick="simulate()">&#9889; Simulate fault (E-471, CM-350 Line 2)</button>
  <h2>PENDING APPROVAL</h2><table id="pending"></table>
  <h2>ALL WORK ORDERS</h2><table id="all"></table>
</main>
<script>
const api = p => fetch('/api'+p).then(r=>r.json());
const post = p => fetch('/api'+p,{method:'POST'}).then(r=>r.json());
const esc = s => String(s).replace(/[&<>"]/g,function(m){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]||m});

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
const sevClass = s => 's' + Math.min(Math.max(parseInt(s)||3,1),5);
const sevLabel = {1:'INFO',2:'LOW',3:'WARN',4:'HIGH',5:'CRIT'};

const feed = document.getElementById('live-feed');
const evtSource = new EventSource('/api/events/stream');
evtSource.addEventListener('fault', function(e){
  const d = JSON.parse(e.data);
  const ts = (d.timestamp||'').slice(11,19);
  const s = Math.min(Math.max(parseInt(d.severity)||3,1),5);
  const row = document.createElement('div');
  row.className = 'flash';
  row.innerHTML = '<table><tr><td style="width:40px"><span class="sev-badge '+sevClass(s)+'"></span><b class="sev-'+s+'">'+sevLabel[s]+'</b></td>'+
    '<td style="width:70px;color:#8b98a5">'+esc(ts)+'</td>'+
    '<td style="width:200px">'+esc(d.machine_id)+'</td>'+
    '<td><b>'+esc(d.fault_code)+'</b></td></tr></table>';
  feed.prepend(row);
  const rows = feed.children;
  for(let i=20;i<rows.length;i++) rows[i].remove();
  evtSource.dispatchEvent(new Event('heartbeat'));
});
evtSource.addEventListener('heartbeat', function(){
  document.getElementById('mqtt-dot').className = 'status-dot connected';
  document.getElementById('mqtt-label').textContent = 'connected';
});
evtSource.onerror = function(){
  document.getElementById('mqtt-dot').className = 'status-dot disconnected';
  document.getElementById('mqtt-label').textContent = 'disconnected';
};

async function load(){
  const m = await api('/metrics');
  document.getElementById('tiles').innerHTML = [
    ['Total work orders', m.total_work_orders],
    ['Avg time to diagnosis', m.avg_time_to_diagnosis_sec!=null?m.avg_time_to_diagnosis_sec+'s':'-'],
    ['Avg time to fix', m.avg_time_to_fix_min!=null?m.avg_time_to_fix_min+' min':'-'],
    ['Resolution rate', m.resolution_rate!=null?Math.round(m.resolution_rate*100)+'%':'-'],
  ].map(([l,v])=>`<div class="tile"><b>${v}</b><small>${l}</small></div>`).join('');

  const pend = await api('/work-orders?status=pending');
  document.getElementById('pending').innerHTML =
    '<tr><th>ID</th><th>Machine</th><th>Fault</th><th>Root cause</th><th></th></tr>'+
    (pend.length?pend.map(w=>'<tr><td>'+esc(w.id)+'</td><td>'+esc(w.machine)+'</td><td>'+esc(w.fault_code)+'</td>'+
      '<td>'+esc((w.root_cause||'').slice(0,60))+'&#8230;</td>'+
      '<td><button onclick="approve(\''+w.id+'\')">Approve</button>'+
      '<button class="r" onclick="reject(\''+w.id+'\')">Reject</button></td></tr>').join('')
     :'<tr><td colspan=5 style="color:#8b98a5">Queue empty</td></tr>');

  const all = await api('/work-orders');
  document.getElementById('all').innerHTML =
    '<tr><th>ID</th><th>Machine</th><th>Fault</th><th>Status</th><th>Assigned</th><th></th></tr>'+
    all.map(w=>'<tr><td>'+esc(w.id)+'</td><td>'+esc(w.machine)+'</td><td>'+esc(w.fault_code)+'</td>'+
      '<td>'+badge(w.status)+'</td><td>'+esc(w.assigned_to||'-')+'</td>'+
      '<td>'+(w.status==='dispatched'?'<button onclick="resolve(\''+w.id+'\')">Mark fixed</button>':'')+'</td></tr>').join('');
}
load(); setInterval(load, 4000);
</script></body></html>
"""
