import { Link } from "react-router-dom";
import { useI18n } from "../i18n";
import Navbar from "../components/Navbar.jsx";
import styles from "./NotFound.module.css";

export default function NotFound() {
  const { t } = useI18n();
  return (
    <div className={styles.page}>
      <a href="#main-content" className="skip-link">{t("nav.skip_to_content")}</a>
      <Navbar />
      <main id="main-content" className={styles.body}>
        <h1 className={styles.code}>404</h1>
        <p className={styles.title}>{t("not_found.title")}</p>
        <Link to="/" className={styles.link}>{t("not_found.back")}</Link>
      </main>
    </div>
  );
}