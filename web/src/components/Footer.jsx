import { Link } from "react-router-dom";
import styles from "./Footer.module.css";
import FAQ from "./FAQ.jsx";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          <div className={styles.col}>
            <h4 className={styles.heading}>Product</h4>
            <Link to="/" className={styles.link}>Features</Link>
            <Link to="/" className={styles.link}>Pipeline</Link>
            <Link to="/" className={styles.link}>How it works</Link>
            <Link to="/dashboard" className={styles.link}>Dashboard</Link>
          </div>
          <div className={styles.col}>
            <h4 className={styles.heading}>Use Cases</h4>
            <span className={styles.link}>Manufacturing</span>
            <span className={styles.link}>Warehousing</span>
            <span className={styles.link}>Energy</span>
          </div>
          <div className={styles.col}>
            <h4 className={styles.heading}>Support</h4>
            <span className={styles.link}>Documentation</span>
            <span className={styles.link}>API Reference</span>
            <span className={styles.link}>Contact sales</span>
            <span className={styles.link}>Status</span>
          </div>
          <div className={styles.col}>
            <h4 className={styles.heading}>FAQ</h4>
            <FAQ dark={true} />
          </div>
        </div>
        <div className={styles.bottom}>
          TORQ &middot; From fault code to fixed. Built for the factory floor.
        </div>
      </div>
    </footer>
  );
}
