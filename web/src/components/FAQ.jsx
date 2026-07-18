import { useState } from "react";
import styles from "./FAQ.module.css";

const items = [
  {
    q: "What is TORQ?",
    a: "TORQ is an event-driven predictive-maintenance pipeline. When a machine faults, the AI autonomously diagnoses the root cause, generates a trilingual work order, and dispatches the right technician \u2014 all in real time.",
  },
  {
    q: "How does the AI diagnosis work?",
    a: "Hybrid search (dense + BM25 sparse + reranker) retrieves relevant manuals and past repairs. A reasoning LLM produces the diagnosis with grounded citations.",
  },
  {
    q: "What machines are supported?",
    a: "Any machine. If your equipment has a PLC or SCADA, TORQ ingests faults via MQTT or an edge gateway (Modbus, OPC-UA). If your machines are fully analog, operators can submit faults directly through the dashboard form or the REST API from any connected device.",
  },
  {
    q: "How do I integrate TORQ with my plant?",
    a: "Four paths: (1) POST faults directly to the REST API from any system (CMMS, ERP, custom script). (2) Publish MachineFaultEvent JSON to the configured MQTT topic. (3) Run the edge gateway (scripts/mqtt_gateway.py) on a Raspberry Pi to bridge Modbus or OPC-UA from legacy controllers. (4) Use the dashboard's manual fault form — no digital connectivity required.",
  },
  {
    q: "Is my data secure?",
    a: "TORQ runs on your infrastructure. LLM calls go to your endpoint. Vector DB can be self-hosted. No data leaves your network.",
  },
  {
    q: "What languages are supported?",
    a: "English, French, and Arabic (trilingual work-order PDF). Dashboard and API in English.",
  },
  {
    q: "Is this production-ready?",
    a: "Hackathon prototype demonstrating the architecture. Production deployment requires hardening, auth, and scalability testing.",
  },
];

export default function FAQ({ dark }) {
  const [openIndex, setOpenIndex] = useState(null);

  return (
    <div className={`${styles.faq} ${dark ? styles.dark : ""}`}>
      {items.map((item, i) => (
        <div key={i} className={`${styles.item} ${openIndex === i ? styles.open : ""}`}>
          <button className={styles.question} onClick={() => setOpenIndex(openIndex === i ? null : i)}>
            <span>{item.q}</span>
            <span className={styles.chevron}>+</span>
          </button>
          <div className={styles.answer}>
            <div className={styles.answerInner}>{item.a}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
