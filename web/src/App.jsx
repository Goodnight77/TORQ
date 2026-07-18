import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { useI18n } from "./i18n";
import LandingPage from "./pages/LandingPage.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import NotFound from "./pages/NotFound.jsx";

function PageTitle() {
  const { t } = useI18n();
  const { pathname } = useLocation();

  useEffect(() => {
    if (pathname === "/dashboard") {
      document.title = `${t("dashboard.title")} — TORQ`;
    } else {
      document.title = "TORQ — Fault-to-Fix Engine";
    }
  }, [pathname, t]);

  return null;
}

export default function App() {
  return (
    <>
      <PageTitle />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
