import styles from "./PipelineDiagram.module.css";

const steps = [
  { label: "Machine", desc: "Fault code emitted" },
  { label: "TORQ Agent", desc: "AI diagnoses" },
  { label: "Work Order", desc: "Trilingual PDF" },
  { label: "Supervisor", desc: "Approval queue" },
  { label: "Technician", desc: "Dispatched" },
];

function ArrowRight() {
  return (
    <div className={styles.arrow}>
      <svg className={styles.arrowSvg} width="28" height="24" viewBox="0 0 28 24" fill="none">
        <path d="M2 12H24M24 12L16 4M24 12L16 20" stroke="#E4E7EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </div>
  );
}

export default function PipelineDiagram() {
  return (
    <div className={styles.wrapper}>
      <div className={styles.pipeline}>
        {steps.map((s, i) => (
          <div key={i} className={styles.step}>
            <div className={styles.box}>
              <span className={styles.label}>{s.label}</span>
              <span className={styles.desc}>{s.desc}</span>
            </div>
            {i < steps.length - 1 && <ArrowRight />}
          </div>
        ))}
      </div>
      <div className={styles.feedback}>
        <svg viewBox="0 0 640 72" className={styles.feedbackSvg}>
          <path
            d="M 40 28 Q 320 68 600 28"
            className={styles.feedbackPath}
          />
          <text x="320" y="62" textAnchor="middle" className={styles.feedbackText}>
            feedback loop — model improves with every fix
          </text>
        </svg>
      </div>
    </div>
  );
}
