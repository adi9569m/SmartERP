"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, logout } from "../lib/api";
import { Button, Input, Modal } from "./ui";

const sections = [
  ["Overview", [["Dashboard","/dashboard"]]],
  ["Masters", [["Ledgers","/dashboard/masters/ledgers"],["Groups","/dashboard/masters/groups"],["Stock Groups","/dashboard/masters/stock-groups"],["Stock Items","/dashboard/masters/stock-items"],["Units","/dashboard/masters/units"],["Customers","/dashboard/masters/customers"],["Suppliers","/dashboard/masters/suppliers"]]],
  ["Transactions", [["Sales (F8)","/dashboard/sales"],["Purchase (F9)","/dashboard/purchases"],["Payment (F5)","/dashboard/vouchers/payment"],["Receipt (F6)","/dashboard/vouchers/receipt"],["Journal (F7)","/dashboard/vouchers/journal"]]],
  ["Operations", [["Inventory","/dashboard/inventory"],["Accounting","/dashboard/reports/trial-balance"],["Banking","/dashboard/banking"],["GST","/dashboard/gst"],["Reports","/dashboard/reports"],["Administration","/dashboard/administration"]]],
];
const shortcuts = {F5:"/dashboard/vouchers/payment",F6:"/dashboard/vouchers/receipt",F7:"/dashboard/vouchers/journal",F8:"/dashboard/sales",F9:"/dashboard/purchases"};
const routeShortcuts = {
  "alt+l":"/dashboard/masters/ledgers?action=create",
  "alt+a":"/dashboard/masters/ledgers?action=alter",
  "alt+g":"/dashboard/masters/groups?action=create",
  "alt+s":"/dashboard/masters/stock-items?action=create",
  "alt+u":"/dashboard/masters/units?action=create",
  "alt+b":"/dashboard/reports/balance-sheet",
  "alt+p":"/dashboard/reports/profit-loss",
  "alt+t":"/dashboard/reports/trial-balance",
  "alt+c":"/dashboard/reports/cash-flow",
  "alt+r":"/dashboard/reports/stock-summary",
  "alt+x":"/dashboard/gst",
  "ctrl+i":"/dashboard/inventory",
  "ctrl+n":"/dashboard/masters/stock-items?action=create",
  "ctrl+e":"/dashboard/masters/stock-items?action=alter",
  "ctrl+t":"/dashboard/inventory?action=transfer",
  "ctrl+r":"/dashboard/reports/stock-summary",
  "ctrl+b":"/dashboard/sales",
  "ctrl+h":"/dashboard"
};

export default function ERPLayout({children}) {
  const path=usePathname(), router=useRouter(), [company,setCompany]=useState(null), [open,setOpen]=useState(false);
  const [dialog,setDialog]=useState(""),[year,setYear]=useState(""),[expression,setExpression]=useState(""),[result,setResult]=useState("");
  useEffect(()=>{api("/companies").then(x=>setCompany(x.items.find(c=>String(c.id)===localStorage.getItem("smarterp_company")))).catch(()=>logout())},[]);
  useEffect(()=>{
    function key(e){
      const target=e.target.tagName;
      const commandKey=e.ctrlKey||e.altKey||/^F\d+$/.test(e.key);
      if(["INPUT","TEXTAREA","SELECT"].includes(target)&&e.key!=="Escape"&&!commandKey)return;
      const combo=`${e.ctrlKey?"ctrl+":""}${e.altKey?"alt+":""}${e.key.toLowerCase()}`;
      if(e.key==="F1"){e.preventDefault();router.push("/companies")}
      else if(e.key==="F2"){e.preventDefault();setYear(company?.financial_year||"");setDialog("year")}
      else if(e.key==="F3"){e.preventDefault();setDialog("company")}
      else if(e.key==="F4"){e.preventDefault();setDialog("calculator")}
      else if(shortcuts[e.key]&&!e.altKey){e.preventDefault();router.push(shortcuts[e.key])}
      else if(e.altKey&&e.key==="F8"){e.preventDefault();router.push("/dashboard/vouchers/credit-note")}
      else if(e.altKey&&e.key==="F9"){e.preventDefault();router.push("/dashboard/vouchers/debit-note")}
      else if(routeShortcuts[combo]){e.preventDefault();router.push(routeShortcuts[combo])}
      else if(e.ctrlKey&&e.key.toLowerCase()==="k"){e.preventDefault();document.querySelector("[data-global-search]")?.focus()}
      else if(e.ctrlKey&&e.key.toLowerCase()==="q"){e.preventDefault();logout()}
      else if(e.ctrlKey&&e.shiftKey&&e.key.toLowerCase()==="p"){e.preventDefault();window.dispatchEvent(new Event("erp-pdf"))}
      else if(e.ctrlKey&&e.key.toLowerCase()==="p"){e.preventDefault();window.dispatchEvent(new Event("erp-print"))}
      else if(e.key==="?"&&!e.ctrlKey&&!e.altKey){e.preventDefault();setDialog("help")}
      else if(e.key==="Escape"){e.preventDefault();if(dialog)setDialog("");else router.back()}
    } window.addEventListener("keydown",key);return()=>window.removeEventListener("keydown",key)
  },[router,company,dialog]);
  async function saveYear(e){e.preventDefault();const updated=await api(`/companies/${company.id}`,{method:"PUT",body:JSON.stringify({financial_year:year})});setCompany(updated);setDialog("")}
  function calculate(e){e.preventDefault();if(!/^[\d\s()+\-*/.]+$/.test(expression)){setResult("Invalid expression");return}try{const tokens=expression.match(/\d+(?:\.\d+)?|[()+\-*/]/g)||[];let pos=0;const parsePrimary=()=>{if(tokens[pos]==="("){pos++;const v=parseAdd();if(tokens[pos++]!==")")throw 0;return v}const v=Number(tokens[pos++]);if(!Number.isFinite(v))throw 0;return v};const parseMul=()=>{let v=parsePrimary();while(tokens[pos]==="*"||tokens[pos]==="/"){const op=tokens[pos++],n=parsePrimary();v=op==="*"?v*n:v/n}return v};const parseAdd=()=>{let v=parseMul();while(tokens[pos]==="+"||tokens[pos]==="-"){const op=tokens[pos++],n=parseMul();v=op==="+"?v+n:v-n}return v};const value=parseAdd();if(pos!==tokens.length||!Number.isFinite(value))throw 0;setResult(String(value))}catch{setResult("Invalid expression")}}
  return <div className="min-h-screen md:flex">
    <aside className={`${open?"block":"hidden"} fixed inset-y-0 z-40 w-64 overflow-y-auto bg-slate-900 p-4 text-slate-200 md:static md:block`}>
      <div className="mb-6 px-2"><div className="text-lg font-extrabold tracking-[.18em] text-white">SMARTERP</div><div className="mt-1 truncate text-xs text-slate-400">{company?.name||"Loading company…"}</div></div>
      {sections.map(([title,links])=><div className="mb-5" key={title}><p className="mb-1 px-2 text-[10px] font-bold uppercase tracking-[.2em] text-slate-500">{title}</p>{links.map(([label,href])=><Link key={href} href={href} onClick={()=>setOpen(false)} className={`block rounded px-2 py-2 text-sm ${path===href?"bg-blue-600 text-white":"hover:bg-slate-800"}`}>{label}</Link>)}</div>)}
    </aside>
    <div className="min-w-0 flex-1">
      <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b bg-white px-4 md:px-7"><button className="md:hidden" onClick={()=>setOpen(!open)}>☰</button><input data-global-search placeholder="Search current table…  Ctrl+K" className="field max-w-md" onChange={e=>window.dispatchEvent(new CustomEvent("erp-search",{detail:e.target.value}))}/><div className="ml-auto flex gap-2"><button className="text-sm text-slate-600" onClick={()=>router.push("/companies")}>Switch Company</button><button className="text-sm text-red-600" onClick={logout}>Logout</button></div></header>
      <main className="p-4 md:p-7">{children}</main>
      <footer className="sticky bottom-0 z-20 flex gap-4 overflow-x-auto border-t bg-slate-800 px-4 py-2 text-[11px] text-white">
        <span>F1 Company</span><span>F4 Calculator</span><span>F5 Payment</span><span>F6 Receipt</span><span>F7 Journal</span><span>F8 Sales</span><span>F9 Purchase</span><span>? All Keys</span>
      </footer>
    </div>
    <Modal title="Change Financial Year (F2)" open={dialog==="year"} onClose={()=>setDialog("")}><form onSubmit={saveYear}><Input autoFocus label="Financial Year" value={year} onChange={e=>setYear(e.target.value)} required/><Button className="mt-4">Save</Button></form></Modal>
    <Modal title="Company Information (F3)" open={dialog==="company"} onClose={()=>setDialog("")}><dl className="grid grid-cols-[auto_1fr] gap-3 text-sm"><dt className="font-bold">Company</dt><dd>{company?.name}</dd><dt className="font-bold">Financial Year</dt><dd>{company?.financial_year}</dd><dt className="font-bold">GSTIN</dt><dd>{company?.gst_number||"Not specified"}</dd><dt className="font-bold">State</dt><dd>{company?.state}</dd><dt className="font-bold">Address</dt><dd>{company?.address}</dd></dl></Modal>
    <Modal title="Calculator (F4)" open={dialog==="calculator"} onClose={()=>setDialog("")}><form onSubmit={calculate}><Input autoFocus label="Expression" placeholder="Example: (1250 + 450) * 1.18" value={expression} onChange={e=>setExpression(e.target.value)}/><p className="my-4 min-h-8 text-2xl font-bold">{result}</p><Button>Calculate</Button></form></Modal>
    <Modal title="Keyboard Shortcuts (?)" open={dialog==="help"} onClose={()=>setDialog("")}><div className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2">{[
      ["F1","Company Selection"],["F2","Financial Year"],["F3","Company Information"],["F4","Calculator"],["Esc","Previous Screen"],["Ctrl+H","Dashboard"],["Ctrl+K","Search"],["Ctrl+Q","Logout"],["Alt+L","Create Ledger"],["Alt+A","Alter Ledger"],["Alt+G","Create Group"],["Alt+S","Create Stock Item"],["Alt+U","Create Unit"],["F5/F6/F7","Payment/Receipt/Journal"],["F8/F9","Sales/Purchase"],["Alt+F8/F9","Credit/Debit Note"],["Ctrl+I","Inventory"],["Ctrl+N/E","New/Edit Item"],["Ctrl+T","Stock Transfer"],["Ctrl+R","Stock Report"],["Ctrl+B","Create Invoice/Sale"],["Ctrl+P","Print Invoice"],["Ctrl+Shift+P","PDF Invoice"],["Alt+B/P/T/C","Financial Reports"],["Alt+R/X","Stock/GST Reports"],["↑ ↓ Enter","Navigate/Select rows"]
    ].map(([key,label])=><p key={key}><kbd className="mr-2 inline-block min-w-24 rounded bg-slate-100 px-2 py-1 font-bold">{key}</kbd>{label}</p>)}</div></Modal>
  </div>
}
