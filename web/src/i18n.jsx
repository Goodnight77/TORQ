import { createContext, useContext, useState, useCallback } from "react";

const LOCALES = {
  en: {
    "dashboard.title": "Supervisor dashboard",
    "dashboard.subtitle": "Approval queue and downtime metrics",
    "dashboard.total": "Total work orders",
    "dashboard.avg_diag": "Avg time to diagnosis",
    "dashboard.avg_fix": "Avg time to fix",
    "dashboard.res_rate": "Resolution rate",
    "dashboard.pending": "Pending approval",
    "dashboard.all": "All work orders",
    "dashboard.queue_empty": "Queue empty",
    "dashboard.no_orders": "No work orders yet",
    "dashboard.id": "ID",
    "dashboard.machine": "Machine",
    "dashboard.fault": "Fault",
    "dashboard.cause": "Root cause",
    "dashboard.status": "Status",
    "dashboard.assigned": "Assigned",
    "dashboard.approve": "Approve",
    "dashboard.reject": "Reject",
    "dashboard.mark_fixed": "Mark fixed",
    "dashboard.close": "close",
    "dashboard.download_pdf": "Download PDF (EN/FR/AR)",
    "dashboard.grounded_in": "Grounded in",
    "dashboard.simulate": "Simulate fault (E-471, CM-350 Line 2)",
    "dashboard.footer": "From fault code to fixed.",
    "dashboard.live_feed": "Live fault feed",
    "dashboard.repair_steps": "Repair steps",
    "dashboard.parts": "Parts",
    "dashboard.tools": "Tools",
    "dashboard.safety": "Safety warnings",
    "dashboard.confidence": "Confidence",
    "dashboard.needs_review": "Needs human review",
    "dashboard.trend": "Time-to-diagnosis / MTTR trend",
    "dashboard.faults_per_machine": "Faults per machine",
    "dashboard.search": "Search machine…",
    "dashboard.all_statuses": "All statuses",
    "dashboard.just_now": "just now",
    "dashboard.min_ago": "min ago",
    "dashboard.hours_saved": "Hours saved / week",
    "dashboard.money_saved": "Money saved / year",
    "dashboard.roi_title": "ROI & Savings Calculator",
    "dashboard.eval_title": "Retrieval quality — MRR",
    "dashboard.eval_scenarios": "labeled scenarios",
    "dashboard.faults_per_week": "Faults / week",
    "dashboard.downtime_cost": "Downtime cost / min ($)",
    "dashboard.baseline_mttr": "Baseline MTTR (min)",
    "dashboard.toast_approved": "Approved",
    "dashboard.toast_dispatched": "Dispatched to",
    "dashboard.toast_rejected": "Rejected",
    "dashboard.toast_fixed": "Marked as fixed",
    "dashboard.toast_simulated": "Fault simulated",
  },
  fr: {
    "dashboard.title": "Tableau de bord superviseur",
    "dashboard.subtitle": "File d'approbation et métriques de temps d'arrêt",
    "dashboard.total": "Total ordres de travail",
    "dashboard.avg_diag": "Temps moyen de diagnostic",
    "dashboard.avg_fix": "Temps moyen de réparation",
    "dashboard.res_rate": "Taux de résolution",
    "dashboard.pending": "En attente d'approbation",
    "dashboard.all": "Tous les ordres de travail",
    "dashboard.queue_empty": "File d'attente vide",
    "dashboard.no_orders": "Aucun ordre de travail",
    "dashboard.id": "ID",
    "dashboard.machine": "Machine",
    "dashboard.fault": "Défaut",
    "dashboard.cause": "Cause racine",
    "dashboard.status": "Statut",
    "dashboard.assigned": "Assigné à",
    "dashboard.approve": "Approuver",
    "dashboard.reject": "Rejeter",
    "dashboard.mark_fixed": "Marquer réparé",
    "dashboard.close": "fermer",
    "dashboard.download_pdf": "Télécharger PDF (EN/FR/AR)",
    "dashboard.grounded_in": "Basé sur",
    "dashboard.simulate": "Simuler défaut (E-471, CM-350 Line 2)",
    "dashboard.footer": "Du code défaut à la réparation.",
    "dashboard.live_feed": "Flux de défauts en direct",
    "dashboard.repair_steps": "Étapes de réparation",
    "dashboard.parts": "Pièces",
    "dashboard.tools": "Outils",
    "dashboard.safety": "Avertissements de sécurité",
    "dashboard.confidence": "Confiance",
    "dashboard.needs_review": "Nécessite un examen humain",
    "dashboard.trend": "Tendance temps de diagnostic / MTTR",
    "dashboard.faults_per_machine": "Défauts par machine",
    "dashboard.search": "Rechercher machine…",
    "dashboard.all_statuses": "Tous les statuts",
    "dashboard.just_now": "à l'instant",
    "dashboard.min_ago": "min",
    "dashboard.hours_saved": "Heures économisées / semaine",
    "dashboard.money_saved": "Argent économisé / an",
    "dashboard.roi_title": "Calculateur ROI & Économies",
    "dashboard.eval_title": "Qualité de recherche — MRR",
    "dashboard.eval_scenarios": "scénarios étiquetés",
    "dashboard.faults_per_week": "Défauts / semaine",
    "dashboard.downtime_cost": "Coût d'arrêt / min ($)",
    "dashboard.baseline_mttr": "MTTR de référence (min)",
    "dashboard.toast_approved": "Approuvé",
    "dashboard.toast_dispatched": "Envoyé à",
    "dashboard.toast_rejected": "Rejeté",
    "dashboard.toast_fixed": "Marqué comme réparé",
    "dashboard.toast_simulated": "Défaut simulé",
  },
  ar: {
    "dashboard.title": "لوحة تحكم المشرف",
    "dashboard.subtitle": "قائمة الموافقات ومقاييس وقت التوقف",
    "dashboard.total": "إجمالي أوامر العمل",
    "dashboard.avg_diag": "متوسط وقت التشخيص",
    "dashboard.avg_fix": "متوسط وقت الإصلاح",
    "dashboard.res_rate": "معدل الحل",
    "dashboard.pending": "بانتظار الموافقة",
    "dashboard.all": "جميع أوامر العمل",
    "dashboard.queue_empty": "القائمة فارغة",
    "dashboard.no_orders": "لا توجد أوامر عمل بعد",
    "dashboard.id": "المعرف",
    "dashboard.machine": "الآلة",
    "dashboard.fault": "الخلل",
    "dashboard.cause": "السبب الجذري",
    "dashboard.status": "الحالة",
    "dashboard.assigned": "مسند إلى",
    "dashboard.approve": "موافقة",
    "dashboard.reject": "رفض",
    "dashboard.mark_fixed": "تحديد كمصلح",
    "dashboard.close": "إغلاق",
    "dashboard.download_pdf": "تنزيل PDF (EN/FR/AR)",
    "dashboard.grounded_in": "مستند على",
    "dashboard.simulate": "محاكاة خلل (E-471, CM-350 Line 2)",
    "dashboard.footer": "من رمز الخلل إلى الإصلاح.",
    "dashboard.live_feed": "تغذية الأخطاء المباشرة",
    "dashboard.repair_steps": "خطوات الإصلاح",
    "dashboard.parts": "قطع الغيار",
    "dashboard.tools": "الأدوات",
    "dashboard.safety": "تحذيرات السلامة",
    "dashboard.confidence": "الثقة",
    "dashboard.needs_review": "يحتاج إلى مراجعة بشرية",
    "dashboard.trend": "اتجاه وقت التشخيص / MTTR",
    "dashboard.faults_per_machine": "الأعطال لكل آلة",
    "dashboard.search": "بحث عن آلة…",
    "dashboard.all_statuses": "جميع الحالات",
    "dashboard.just_now": "الآن",
    "dashboard.min_ago": "دقيقة",
    "dashboard.hours_saved": "ساعات موفرة / أسبوع",
    "dashboard.money_saved": "توفير / سنة",
    "dashboard.roi_title": "حاسبة العائد على الاستثمار والتوفير",
    "dashboard.eval_title": "جودة الاسترجاع — MRR",
    "dashboard.eval_scenarios": "سيناريوهات موسومة",
    "dashboard.faults_per_week": "أعطال / أسبوع",
    "dashboard.downtime_cost": "تكلفة التوقف / دقيقة ($)",
    "dashboard.baseline_mttr": "MTTR الأساسي (دقيقة)",
    "dashboard.toast_approved": "تمت الموافقة",
    "dashboard.toast_dispatched": "تم الإرسال إلى",
    "dashboard.toast_rejected": "مرفوض",
    "dashboard.toast_fixed": "تم الإصلاح",
    "dashboard.toast_simulated": "تم محاكاة الخلل",
  },
};

const I18nContext = createContext();

export function I18nProvider({ children }) {
  const [locale, setLocale] = useState(() => {
    return localStorage.getItem("torq-lang") || "en";
  });

  const t = useCallback((key) => {
    return LOCALES[locale]?.[key] ?? LOCALES.en[key] ?? key;
  }, [locale]);

  const changeLocale = useCallback((l) => {
    setLocale(l);
    localStorage.setItem("torq-lang", l);
    document.documentElement.setAttribute("lang", l);
    if (l === "ar") {
      document.documentElement.setAttribute("dir", "rtl");
    } else {
      document.documentElement.setAttribute("dir", "ltr");
    }
  }, []);

  return (
    <I18nContext.Provider value={{ locale, t, changeLocale }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
