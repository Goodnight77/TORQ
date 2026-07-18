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
