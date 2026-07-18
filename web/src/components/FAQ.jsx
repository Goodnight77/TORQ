import { useState } from "react";
import { useI18n } from "../i18n";
import styles from "./FAQ.module.css";

export default function FAQ({ dark }) {
  const { t } = useI18n();
  const [openIndex, setOpenIndex] = useState(null);

  const items = [
    { q: t("faq.q1"), a: t("faq.a1") },
    { q: t("faq.q2"), a: t("faq.a2") },
    { q: t("faq.q3"), a: t("faq.a3") },
    { q: t("faq.q4"), a: t("faq.a4") },
    { q: t("faq.q5"), a: t("faq.a5") },
    { q: t("faq.q6"), a: t("faq.a6") },
    { q: t("faq.q7"), a: t("faq.a7") },
  ];

  return (
    <div className={`${styles.faq} ${dark ? styles.dark : ""}`}>
      {items.map((item, i) => {
        const isOpen = openIndex === i;
        const panelId = `faq-panel-${i}`;
        const btnId = `faq-btn-${i}`;
        return (
          <div key={i} className={`${styles.item} ${isOpen ? styles.open : ""}`}>
            <button
              id={btnId}
              className={styles.question}
              onClick={() => setOpenIndex(isOpen ? null : i)}
              aria-expanded={isOpen}
              aria-controls={panelId}
            >
              <span>{item.q}</span>
              <span className={styles.chevron}>+</span>
            </button>
            <div id={panelId} className={styles.answer} role="region" aria-labelledby={btnId}>
              <div className={styles.answerInner}>{item.a}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
