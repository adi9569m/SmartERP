"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";
import { Button, Input } from "../../components/ui";

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      const result = await api(`/auth/${mode}`, { method: "POST", body: JSON.stringify(form) });
      localStorage.setItem("smarterp_token", result.access_token);
      router.push("/companies");
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <main className="grid min-h-screen place-items-center bg-[#0b1f3a] p-4">
    <form onSubmit={submit} className="card w-full max-w-md p-8">
      <div className="mb-7"><div className="text-sm font-bold uppercase tracking-[.25em] text-blue-800">SmartERP</div><h1 className="mt-2 text-2xl font-bold">{mode === "login" ? "Welcome back" : "Create administrator"}</h1><p className="mt-1 text-sm text-slate-500">Billing, Inventory & Accounting</p></div>
      <div className="space-y-4">
        {mode === "register" && <Input label="Full name" value={form.full_name} onChange={(e) => setForm({...form, full_name:e.target.value})} required />}
        <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({...form, email:e.target.value})} required />
        <Input label="Password" type="password" minLength="8" value={form.password} onChange={(e) => setForm({...form, password:e.target.value})} required />
        {error && <p className="rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <Button className="w-full" disabled={busy}>{busy ? "Please waitâ€¦" : mode === "login" ? "Login" : "Register"}</Button>
      </div>
      <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")} className="mt-5 w-full text-sm font-medium text-blue-800">{mode === "login" ? "First time? Create an account" : "Already registered? Login"}</button>
    </form>
  </main>;
}
