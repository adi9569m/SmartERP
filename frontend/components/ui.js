"use client";

import { useEffect, useRef } from "react";

export function Button({ variant = "primary", className = "", ...props }) {
  const style = variant === "secondary" ? "btn btn-secondary" : variant === "danger" ? "btn btn-danger" : "btn";
  return <button className={`${style} ${className}`} {...props} />;
}

export function Input({ label, ...props }) {
  return <label><span className="label">{label}</span><input className="field" {...props} /></label>;
}

export function Select({ label, children, ...props }) {
  return <label><span className="label">{label}</span><select className="field" {...props}>{children}</select></label>;
}

export function Modal({ title, open, onClose, children }) {
  const panelRef = useRef(null);
  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => {
      const focusable = panelRef.current?.querySelector("input, select, textarea, button, a[href]");
      focusable?.focus();
    }, 0);
    return () => clearTimeout(timer);
  }, [open]);
  if (!open) return null;
  function modalKey(e) {
    if (e.key === "Escape") { e.stopPropagation(); onClose(); return; }
    if (e.key !== "Tab") return;
    const focusable = [...panelRef.current.querySelectorAll("input:not(:disabled), select:not(:disabled), textarea:not(:disabled), button:not(:disabled), a[href]")];
    if (!focusable.length) return;
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }
  return <div role="dialog" aria-modal="true" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm" onMouseDown={onClose} onKeyDown={modalKey}>
    <div ref={panelRef} className="card max-h-[90vh] w-full max-w-2xl overflow-auto p-6 shadow-2xl md:p-7" onMouseDown={(e) => e.stopPropagation()}>
      <div className="mb-6 flex items-center justify-between border-b border-slate-100 pb-4"><h2 className="text-xl font-bold tracking-tight">{title}</h2><button onClick={onClose} className="text-2xl text-slate-400">Ã—</button></div>
      {children}
    </div>
  </div>;
}
