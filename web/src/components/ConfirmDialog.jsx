import { useEffect, useRef, useCallback } from "react";
import useFocusTrap from "../hooks/useFocusTrap";
import styles from "./ConfirmDialog.module.css";

export default function ConfirmDialog({ open, message, confirmLabel, cancelLabel, onConfirm, onCancel, busy }) {
  const confirmRef = useRef(null);
  const previousFocus = useRef(null);
  const dialogRef = useFocusTrap(open);

  useEffect(() => {
    if (open) {
      previousFocus.current = document.activeElement;
      requestAnimationFrame(() => confirmRef.current?.focus());
    } else if (previousFocus.current) {
      previousFocus.current.focus();
      previousFocus.current = null;
    }
  }, [open]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === "Escape") {
      onCancel();
    }
  }, [onCancel]);

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div
        ref={dialogRef}
        className={styles.dialog}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-message"
        onClick={(e) => e.stopPropagation()}
      >
        <p id="confirm-message" className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </button>
          <button
            className={styles.confirmBtn}
            ref={confirmRef}
            onClick={onConfirm}
            disabled={busy}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}