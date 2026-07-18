import styles from "./FeatureCard.module.css";

export default function FeatureCard({ icon, title, description }) {
  return (
    <div className={styles.card}>
      <span className={styles.iconFrame}>
        <span className={styles.icon}>{icon}</span>
      </span>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.desc}>{description}</p>
    </div>
  );
}
