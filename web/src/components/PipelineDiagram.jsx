import styles from "./PipelineDiagram.module.css";

const steps = [
  { label: "1. Machine", desc: "Fault code emitted" },
  { label: "2. TORQ Agent", desc: "AI diagnoses" },
  { label: "3. Work Order", desc: "Trilingual PDF" },
  { label: "4. Supervisor", desc: "Approval queue" },
  { label: "5. Technician", desc: "Dispatched" },
];

export default function PipelineDiagram() {
  return (
    <div className={styles.wrapper}>
      {/* Desktop / Tablet View */}
      <div className={styles.diagramDesktop}>
        <div className={styles.svgContainer}>
          <svg viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" className={styles.linesSvg}>
            {/* The base faint line */}
            <path
              d="M 100 250 L 500 50 L 900 250 L 750 500 L 250 500 Z"
              className={styles.basePath}
            />
            {/* The animated data pulse line */}
            <path
              d="M 100 250 L 500 50 L 900 250 L 750 500 L 250 500 Z"
              className={styles.animatedPath}
            />
          </svg>
        </div>
        <div className={styles.nodesContainer}>
          {steps.map((s, i) => (
            <div key={i} className={`${styles.node} ${styles[`node${i + 1}`]}`}>
              <span className={styles.label}>{s.label}</span>
              <span className={styles.desc}>{s.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Mobile Fallback View */}
      <div className={styles.diagramMobile}>
        <div className={styles.mobileLine} />
        <div className={styles.mobileAnimatedLine} />
        {steps.map((s, i) => (
          <div key={i} className={`${styles.node} ${styles.nodeMobile}`}>
            <span className={styles.label}>{s.label}</span>
            <span className={styles.desc}>{s.desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
