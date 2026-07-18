import { useI18n } from "../i18n";
import styles from "./PipelineDiagram.module.css";

export default function PipelineDiagram() {
  const { t } = useI18n();

  const steps = [
    { label: t("pipeline.step_1_label"), desc: t("pipeline.step_1_desc") },
    { label: t("pipeline.step_2_label"), desc: t("pipeline.step_2_desc") },
    { label: t("pipeline.step_3_label"), desc: t("pipeline.step_3_desc") },
    { label: t("pipeline.step_4_label"), desc: t("pipeline.step_4_desc") },
    { label: t("pipeline.step_5_label"), desc: t("pipeline.step_5_desc") },
  ];

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
