import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import PipelineDiagram from "../components/PipelineDiagram.jsx";
import FeatureCard from "../components/FeatureCard.jsx";
import { IconDiagnosis, IconDocument, IconPin, IconRefresh, IconArrowRight, IconArrowDown } from "../components/icons.jsx";
import Footer from "../components/Footer.jsx";
import styles from "./LandingPage.module.css";

const features = [
  {
    icon: <IconDiagnosis />,
    title: "AI Diagnosis",
    description: "Hybrid search across manuals and repair history pinpoints root causes in seconds, not hours.",
  },
  {
    icon: <IconDocument />,
    title: "Trilingual Work Orders",
    description: "Every work order auto-generates in English, French, and Arabic as a downloadable PDF.",
  },
  {
    icon: <IconPin />,
    title: "Smart Dispatch",
    description: "Routes the right technician based on skill, location, and availability.",
  },
  {
    icon: <IconRefresh />,
    title: "Self-Learning",
    description: "Every fix enriches the knowledge base. The model gets smarter with each resolved fault.",
  },
];

const stats = [
  { value: "99.2", suffix: "%", label: "Diagnosis accuracy" },
  { value: "47", suffix: "s", label: "Avg time to diagnose" },
  { value: "1,240", suffix: "+", label: "Faults resolved" },
  { value: "12", suffix: "x", label: "Faster than manual triage" },
  { value: "0", suffix: "", label: "Data leakage" },
];

function useInView(threshold = 0.15) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); obs.unobserve(el); } },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, inView];
}

function AnimatedStat({ value, suffix, label, visible }) {
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (!visible) return;
    const num = parseFloat(value.replace(/,/g, ""));
    const isDecimal = value.includes(".");
    const duration = 1200;
    const steps = 30;
    let i = 0;
    const timer = setInterval(() => {
      i++;
      const progress = Math.min(i / steps, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = (eased * num).toFixed(isDecimal ? 1 : 0);
      setDisplay(current);
      if (progress >= 1) clearInterval(timer);
    }, duration / steps);
    return () => clearInterval(timer);
  }, [visible, value]);

  return (
    <div className={`${styles.stat} ${visible ? styles.statVisible : ""}`}>
      <span className={styles.statValue}>
        {display}<span className={styles.statSuffix}>{suffix}</span>
      </span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}

function SectionTitle({ children, subtitle }) {
  return (
    <div className={styles.sectionHeader}>
      <h2 className={styles.sectionTitle}>{children}</h2>
      {subtitle && <p className={styles.sectionSubtitle}>{subtitle}</p>}
      <div className={styles.titleBar} />
    </div>
  );
}

export default function LandingPage() {
  const [statsRef, statsVisible] = useInView(0.3);
  const [pipelineRef, pipelineVisible] = useInView(0.1);
  const [featuresRef, featuresVisible] = useInView(0.1);
  const [stepsRef, stepsVisible] = useInView(0.1);
  const [problemsRef, problemsVisible] = useInView(0.1);

  return (
    <div className={styles.page}>
      <Navbar />

      {/* ── Hero ── */}
      <section className={styles.hero}>
        <div className={styles.heroBg} />
        <div className={styles.heroGrid} />
        <div className={styles.heroContent}>
          <span className={styles.heroBadge}>Fault-to-Fix Engine</span>
          <h1 className={styles.heroTitle}>
            From fault code<br />
            <span className={styles.heroTitleAccent}>to fixed.</span>
          </h1>
          <p className={styles.heroDesc}>
            TORQ autonomously diagnoses machine faults, generates trilingual work orders, and dispatches the right technician &mdash; all in real time.
          </p>
          <div className={styles.heroCta}>
            <Link to="/dashboard" className={styles.btnPrimary}>
              Live Demo
              <IconArrowRight />
            </Link>
            <a href="#how-it-works" className={styles.btnSecondary}>
              How it works
              <IconArrowDown />
            </a>
          </div>
        </div>
        <div className={styles.heroCorner} />
      </section>

      <section className={styles.problemsSection} id="problems">
        <div className={styles.problemsInner}>
          <div className={styles.problemsLeft}>
            <h2 className={styles.problemsHeadline}>The Hidden Cost of Legacy Downtime</h2>
          </div>
          <div className={styles.problemsRight} ref={problemsRef}>
            <div className={`${styles.problemCard} ${styles.fadeUp} ${problemsVisible ? styles.fadeUpVisible : ""}`} style={{ transitionDelay: "0ms" }}>
              <h3>Hours lost to manual searches</h3>
              <p>Technicians waste hours digging though dusty, 500 page physical manuals or fragmented PDFs to translate a single PLC fault code.</p>
            </div>
            <div className={`${styles.problemCard} ${styles.fadeUp} ${problemsVisible ? styles.fadeUpVisible : ""}`} style={{ transitionDelay: "150ms" }}>
              <h3>The tribal knowledge expiry</h3>
              <p>Critical maintenance workarounds live only in the heads of senior engineers. When they retire or exit the plant floor, operational wisdom is permanently lost.</p>
            </div>
            <div className={`${styles.problemCard} ${styles.fadeUp} ${problemsVisible ? styles.fadeUpVisible : ""}`} style={{ transitionDelay: "300ms" }}>
              <h3>Trilingual friction</h3>
              <p>Mismatches between machine logs, manufacturer documentation, and technician field languages (English, French, Arabic) create costly communication bottlenecks.</p>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.statsSection} ref={statsRef}>
        <div className={styles.statsInner}>
          {stats.map((s, i) => (
            <AnimatedStat key={i} {...s} visible={statsVisible} />
          ))}
        </div>
      </section>

      {/* ── Pipeline ── */}
      <section className={styles.pipelineSection} id="pipeline" ref={pipelineRef}>
        <div className={styles.sectionInner}>
          <SectionTitle subtitle="From fault event to resolved work order — entirely automated.">
            Pipeline
          </SectionTitle>
          <div className={`${styles.fadeUp} ${pipelineVisible ? styles.fadeUpVisible : ""}`}>
            <PipelineDiagram />
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className={styles.featuresSection} id="features" ref={featuresRef}>
        <div className={styles.sectionInner}>
          <SectionTitle subtitle="Built for the factory floor. No frills. No latency.">
            Features
          </SectionTitle>
          <div className={`${styles.featureGrid} ${styles.fadeUp} ${featuresVisible ? styles.fadeUpVisible : ""}`}>
            {features.map((f, i) => (
              <FeatureCard key={i} icon={f.icon} title={f.title} description={f.description} />
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className={styles.howSection} id="how-it-works" ref={stepsRef}>
        <div className={styles.sectionInner}>
          <SectionTitle subtitle="Three steps from alarm to resolution.">
            How it works
          </SectionTitle>
          <div className={`${styles.steps} ${styles.fadeUp} ${stepsVisible ? styles.fadeUpVisible : ""}`}>
            <div className={styles.step}>
              <span className={styles.stepNum}>1</span>
              <div className={styles.stepBody}>
                <h3 className={styles.stepTitle}>Fault arrives via MQTT</h3>
                <p className={styles.stepDesc}>Machine emits a fault code to the TORQ edge gateway. The event is ingested and enriched with machine context in milliseconds.</p>
              </div>
            </div>
            <div className={styles.step}>
              <span className={styles.stepNum}>2</span>
              <div className={styles.stepBody}>
                <h3 className={styles.stepTitle}>AI diagnoses against manuals + history</h3>
                <p className={styles.stepDesc}>Hybrid search (dense + BM25 + reranker) retrieves relevant documentation. A reasoning LLM produces a grounded diagnosis with citations.</p>
              </div>
            </div>
            <div className={styles.step}>
              <span className={styles.stepNum}>3</span>
              <div className={styles.stepBody}>
                <h3 className={styles.stepTitle}>Supervisor approves &rarr; technician routed</h3>
                <p className={styles.stepDesc}>The trilingual work order lands in the dashboard queue. One click to approve. The technician is dispatched with full context.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaInner}>
          <h2 className={styles.ctaTitle}>Ready to see it in action?</h2>
          <p className={styles.ctaDesc}>Launch the live dashboard to watch faults flow through the pipeline in real time.</p>
          <Link to="/dashboard" className={styles.btnPrimary}>
            Launch Dashboard
            <IconArrowRight />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
