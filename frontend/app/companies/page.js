"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, logout } from "../../lib/api";
import { Button, Input, Modal } from "../../components/ui";

const empty = { name:"", address:"", gst_number:"", financial_year:"2026-27", contact_information:"", state:"" };
export default function Companies() {
  const router = useRouter();
  const [items,setItems] = useState([]), [form,setForm] = useState(empty), [open,setOpen] = useState(false), [error,setError] = useState("");
  async function load(){ try { setItems((await api("/companies")).items); } catch { logout(); } }
  useEffect(()=>{load()},[]);
  async function save(e){e.preventDefault(); try { await api(form.id ? `/companies/${form.id}` : "/companies",{method:form.id?"PUT":"POST",body:JSON.stringify(form)}); setOpen(false);setForm(empty);load(); } catch(err){setError(err.message)}}
  function select(id){localStorage.setItem("smarterp_company",id);router.push("/dashboard")}
  async function remove(id){if(confirm("Delete this company and its records?")){await api(`/companies/${id}`,{method:"DELETE"});load()}}
  return <main className="min-h-screen p-6 md:p-10">
    <div className="mx-auto max-w-5xl">
      <header className="mb-8 flex items-center justify-between"><div><div className="text-sm font-bold uppercase tracking-[.2em] text-blue-800">SmartERP</div><h1 className="text-3xl font-bold">Choose your company</h1></div><div className="flex gap-2"><Button onClick={()=>{setForm(empty);setOpen(true)}}>+ New company</Button><Button variant="secondary" onClick={logout}>Logout</Button></div></header>
      <div className="grid gap-4 md:grid-cols-2">{items.map(c=><div className="card p-6 transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-lg" key={c.id}><h2 className="text-lg font-bold">{c.name}</h2><p className="mt-1 text-sm text-slate-500">{c.state} Â· FY {c.financial_year}</p><p className="mt-1 text-xs text-slate-400">{c.gst_number || "GST not specified"}</p><div className="mt-5 flex gap-2"><Button onClick={()=>select(c.id)}>Open</Button><Button variant="secondary" onClick={()=>{setForm(c);setOpen(true)}}>Edit</Button><Button variant="danger" onClick={()=>remove(c.id)}>Delete</Button></div></div>)}</div>
      {!items.length&&<div className="card p-14 text-center text-slate-500">Create your first company to begin.</div>}
    </div>
    <Modal title={form.id?"Edit Company":"+ New company"} open={open} onClose={()=>setOpen(false)}><form onSubmit={save} className="grid gap-4 md:grid-cols-2">
      {["name","address","gst_number","financial_year","contact_information","state"].map(k=><Input key={k} label={k.replaceAll("_"," ")} value={form[k]||""} onChange={e=>setForm({...form,[k]:e.target.value})} required={["name","financial_year","state"].includes(k)}/>)}
      {error&&<p className="text-red-600 md:col-span-2">{error}</p>}<Button className="md:col-span-2">Save Company</Button>
    </form></Modal>
  </main>
}
