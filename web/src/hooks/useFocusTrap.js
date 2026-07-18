import { useEffect, useRef } from "react";

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function useFocusTrap(active) {
  const ref = useRef(null);

  useEffect(() => {
    if (!active) return;
    const el = ref.current;
    if (!el) return;

    const handle = (e) => {
      if (e.key !== "Tab") return;
      const nodes = el.querySelectorAll(FOCUSABLE);
      if (nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    el.addEventListener("keydown", handle);
    return () => el.removeEventListener("keydown", handle);
  }, [active]);

  return ref;
}