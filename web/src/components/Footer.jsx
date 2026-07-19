
import styles from "./Footer.module.css";
import FAQ from "./FAQ.jsx";
import { useI18n } from "../i18n";

export default function Footer() {
  const { t } = useI18n();
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          <div className={styles.col}>
            <h4 className={styles.heading}>{t("footer.product")}</h4>
            <a href="/#features" className={styles.link}>{t("footer.features")}</a>
            <a href="/#pipeline" className={styles.link}>{t("footer.pipeline")}</a>
            <a href="/#how_it_works" className={styles.link}>{t("footer.how_it_works")}</a>
            <a href="/dashboard" className={styles.link}>{t("footer.dashboard")}</a>
          </div>
          <div className={styles.col}>
            <h4 className={styles.heading}>{t("footer.use_cases")}</h4>
            <span className={styles.link}>{t("footer.manufacturing")}</span>
            <span className={styles.link}>{t("footer.warehousing")}</span>
            <span className={styles.link}>{t("footer.energy")}</span>
          </div>
          <div className={styles.col}>
            <h4 className={styles.heading}>{t("footer.support")}</h4>
            <span className={styles.link}>{t("footer.documentation")}</span>
            <span className={styles.link}>{t("footer.api_reference")}</span>
            <span className={styles.link}>{t("footer.contact_sales")}</span>
            <span className={styles.link}>{t("footer.status")}</span>
          </div>
          <div className={styles.col}>
            <h4 className={styles.heading}>{t("footer.faq")}</h4>
            <FAQ />
          </div>
        </div>
        <div className={styles.bottom}>
          {t("footer.tagline")}
        </div>
      </div>
    </footer>
  );
}
