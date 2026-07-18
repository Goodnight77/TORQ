import { Link } from "react-router-dom";
import ThemeToggle from "./ThemeToggle.jsx";
import { useI18n } from "../i18n";
import styles from "./Navbar.module.css";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "fr", label: "FR" },
  { code: "ar", label: "AR" },
];

export default function Navbar() {
  const { locale, changeLocale } = useI18n();

  return (
    <nav className={styles.nav}>
      <div className={styles.inner}>
        <Link to="/" className={styles.brand} onClick={(e) => {
          if (window.location.pathname === '/') {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        }}>
          <svg className={styles.logoSvg} width="110" height="38" viewBox="0 0 519 182" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M63.2463 94.2015C61.2021 92.1572 61.2021 88.8428 63.2463 86.7985L68.7985 81.2463C70.8428 79.2021 74.1572 79.2021 76.2014 81.2463L81.7536 86.7985C83.7979 88.8428 83.7979 92.1572 81.7536 94.2015L76.2014 99.7537C74.1572 101.798 70.8428 101.798 68.7985 99.7537L63.2463 94.2015Z" />
            <path d="M132.699 51.2401H111.76V129.76H132.699V112.224H145V68.7762H132.699V51.2401Z" />
            <path d="M94.2238 30.3014V18H50.7762V30.3014H33.2401V51.2401H111.76V30.3014H94.2238Z" />
            <path d="M12.3014 112.224V129.76H33.2401V51.2401H12.3014V68.7762H0V112.224H12.3014Z" />
            <path d="M33.2401 150.699H50.7762V163H94.2238V150.699H111.76V129.76H33.2401V150.699Z" />
            <path d="M225.619 152V62.72H187.539V48H280.819V62.72H242.739V152H225.619ZM316.908 153.92C292.588 153.92 272.588 137.44 272.588 110.4C272.588 83.36 292.588 66.88 316.908 66.88C341.228 66.88 361.228 83.36 361.228 110.4C361.228 137.44 341.228 153.92 316.908 153.92ZM316.908 141.28C331.628 141.28 344.588 129.28 344.588 110.4C344.588 91.52 331.628 79.52 316.908 79.52C302.028 79.52 289.228 91.52 289.228 110.4C289.228 129.28 302.028 141.28 316.908 141.28ZM422.836 85.28C397.716 85.28 387.316 95.2 387.316 113.44V152H370.356V68.8H387.316V98.4C391.156 80.32 402.516 68.8 422.836 68.8V85.28ZM460.809 67.04C479.209 67.04 492.809 81.28 495.209 97.28V68.8H511.529V172.8H494.569V126.08C492.489 140.48 478.569 153.76 461.449 153.76C441.929 153.76 422.889 139.2 422.889 110.4C422.889 81.76 441.289 67.04 460.809 67.04ZM467.849 80C451.849 80 439.529 91.52 439.529 110.4C439.529 129.28 451.849 140.8 467.849 140.8C481.449 140.8 494.889 129.28 494.889 110.4C494.889 91.52 481.449 80 467.849 80Z" />
          </svg>
        </Link>
        <div className={styles.navLinks}>
          <a href="#pipeline" className={styles.link}>Pipeline</a>
          <a href="#features" className={styles.link}>Features</a>
          <a href="#how-it-works" className={styles.link}>How it works</a>
          <Link to="/dashboard" className={styles.link}>Dashboard</Link>
        </div>
        <div className={styles.right}>
          <div className={styles.langGroup}>
            {LANGS.map((l) => (
              <button
                key={l.code}
                className={`${styles.langBtn} ${locale === l.code ? styles.langActive : ""}`}
                onClick={() => changeLocale(l.code)}
              >
                {l.label}
              </button>
            ))}
          </div>
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
