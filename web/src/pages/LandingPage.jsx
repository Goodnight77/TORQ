import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import PipelineDiagram from "../components/PipelineDiagram.jsx";
import FeatureCard from "../components/FeatureCard.jsx";
import { IconDiagnosis, IconDocument, IconPin, IconRefresh, IconBroadcast, IconArrowRight, IconArrowDown } from "../components/icons.jsx";
import Footer from "../components/Footer.jsx";
import { useI18n } from "../i18n.jsx";
import styles from "./LandingPage.module.css";

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
  const { t } = useI18n();
  const [statsRef, statsVisible] = useInView(0.3);
  const [pipelineRef, pipelineVisible] = useInView(0.1);
  const [featuresRef, featuresVisible] = useInView(0.1);
  const [stepsRef, stepsVisible] = useInView(0.1);
  const [problemsRef, problemsVisible] = useInView(0.1);

  const features = [
    {
      icon: <IconDiagnosis />,
      title: t("landing.feature_1_title"),
      description: t("landing.feature_1_desc"),
    },
    {
      icon: <IconDocument />,
      title: t("landing.feature_2_title"),
      description: t("landing.feature_2_desc"),
    },
    {
      icon: <IconPin />,
      title: t("landing.feature_3_title"),
      description: t("landing.feature_3_desc"),
    },
    {
      icon: <IconRefresh />,
      title: t("landing.feature_4_title"),
      description: t("landing.feature_4_desc"),
    },
    {
      icon: <IconBroadcast />,
      title: t("landing.feature_5_title"),
      description: t("landing.feature_5_desc"),
    },
  ];

  const stats = [
    { value: "99.2", suffix: "%", label: t("landing.stat_diag_accuracy") },
    { value: "47", suffix: "s", label: t("landing.stat_avg_time") },
    { value: "1,240", suffix: "+", label: t("landing.stat_faults_resolved") },
    { value: "12", suffix: "x", label: t("landing.stat_faster") },
    { value: "0", suffix: "", label: t("landing.stat_data_leakage") },
  ];

  return (
    <div className={styles.page}>
      <Navbar />

      {/* ── Hero ── */}
      <section className={styles.hero}>
        <div className={styles.heroBg} />
        <div className={styles.heroGrid} />
        <div className={styles.heroContent}>
          <span className={styles.heroBadge}>{t("landing.badge")}</span>
          <h1 className={styles.heroTitle}>
            {t("landing.hero_title_1")}<br />
            <span className={styles.heroTitleAccent}>{t("landing.hero_title_2")}</span>
          </h1>
          <p className={styles.heroDesc}>
            {t("landing.hero_desc")}
          </p>
          <div className={styles.heroCta}>
            <Link to="/dashboard" className={styles.btnPrimary}>
              {t("landing.cta_demo")}
              <IconArrowRight />
            </Link>
            <a href="#how-it-works" className={styles.btnSecondary}>
              {t("landing.cta_how")}
              <IconArrowDown />
            </a>
          </div>
        </div>
        <div className={styles.heroCorner} />
      </section>

      <section className={styles.problemsSection} id="problems">
        <div className={styles.problemsInner}>
          <div className={styles.problemsLeft}>
            <h2 className={styles.problemsHeadline}>{t("landing.problems_headline")}</h2>
          </div>
          <div className={styles.problemsRight} ref={problemsRef}>
            <div className={`${styles.problemCard} ${styles.fadeUp} ${problemsVisible ? styles.fadeUpVisible : ""}`} style={{ transitionDelay: "0ms" }}>
              <h3>{t("landing.problem_1_title")}</h3>
              <p>{t("landing.problem_1_desc")}</p>
            </div>
            <div className={`${styles.problemCard} ${styles.fadeUp} ${problemsVisible ? styles.fadeUpVisible : ""}`} style={{ transitionDelay: "150ms" }}>
              <h3>{t("landing.problem_2_title")}</h3>
              <p>{t("landing.problem_2_desc")}</p>
            </div>
            <div className={`${styles.problemCard} ${styles.fadeUp} ${problemsVisible ? styles.fadeUpVisible : ""}`} style={{ transitionDelay: "300ms" }}>
              <h3>{t("landing.problem_3_title")}</h3>
              <p>{t("landing.problem_3_desc")}</p>
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
          <SectionTitle subtitle={t("landing.pipeline_subtitle")}>
            {t("landing.pipeline_title")}
          </SectionTitle>
          <div className={`${styles.fadeUp} ${pipelineVisible ? styles.fadeUpVisible : ""}`}>
            <PipelineDiagram />
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className={styles.featuresSection} id="features" ref={featuresRef}>
        <div className={styles.sectionInner}>
          <SectionTitle subtitle={t("landing.features_subtitle")}>
            {t("landing.features_title")}
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
          <SectionTitle subtitle={t("landing.how_subtitle")}>
            {t("landing.how_title")}
          </SectionTitle>
          <div className={`${styles.steps} ${styles.fadeUp} ${stepsVisible ? styles.fadeUpVisible : ""}`}>
            <div className={styles.step}>
              <span className={styles.stepNum}>1</span>
              <div className={styles.stepBody}>
                <h3 className={styles.stepTitle}>{t("landing.step_1_title")}</h3>
                <p className={styles.stepDesc}>{t("landing.step_1_desc")}</p>
              </div>
            </div>
            <div className={styles.step}>
              <span className={styles.stepNum}>2</span>
              <div className={styles.stepBody}>
                <h3 className={styles.stepTitle}>{t("landing.step_2_title")}</h3>
                <p className={styles.stepDesc}>{t("landing.step_2_desc")}</p>
              </div>
            </div>
            <div className={styles.step}>
              <span className={styles.stepNum}>3</span>
              <div className={styles.stepBody}>
                <h3 className={styles.stepTitle}>{t("landing.step_3_title")}</h3>
                <p className={styles.stepDesc}>{t("landing.step_3_desc")}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaInner}>
          <h2 className={styles.ctaTitle}>{t("landing.cta_title")}</h2>
          <p className={styles.ctaDesc}>{t("landing.cta_desc")}</p>
          <Link to="/dashboard" className={styles.btnPrimary}>
            {t("landing.cta_launch")}
            <IconArrowRight />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
