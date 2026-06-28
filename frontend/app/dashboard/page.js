"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";

const format = new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR"});
export default function Dashboard(){
  const [data,setData]=useState(null);
  useEffect(()=>{api("/dashboard").then(setData)},[]);
  const cards=[["Total Sales",data?.sales_total],["Total Purchases",data?.purchase_total],["Receivables",data?.receivables],["Payables",data?.payables],["Stock Value",data?.stock_value],["Low Stock Items",data?.low_stock,true]];
  return <><div className="mb-7 flex items-end justify-between gap-4"><div><p className="mb-1 text-xs font-bold uppercase tracking-[.18em] text-green-700">Overview</p><h1 className="text-2xl font-bold tracking-tight md:text-3xl">Your business, at a glance</h1><p className="mt-1 text-sm text-slate-500">Billing, inventory and accounts in one clear view.</p></div><div className="hidden size-11 place-items-center rounded-2xl bg-green-100 text-xl md:grid">↗</div></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{cards.map(([label,value,count])=><div className="card p-5 transition duration-200 hover:-translate-y-0.5 hover:shadow-lg" key={label}><div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-500">{label}</p><span className={`size-2 rounded-full ${label==="Low Stock Items"?"bg-amber-400":"bg-green-400"}`}/></div><p className="mt-3 text-2xl font-bold tracking-tight text-slate-900">{data?count?value:format.format(value):"—"}</p></div>)}</div>
    <div className="mt-7"><p className="mb-3 text-xs font-bold uppercase tracking-[.16em] text-slate-500">Quick actions</p><div className="grid gap-3 md:grid-cols-4">{[["Create sale","/dashboard/sales"],["Record purchase","/dashboard/purchases"],["Adjust stock","/dashboard/inventory"],["View reports","/dashboard/reports"]].map(([x,h])=><Link className="card group p-4 font-semibold transition hover:-translate-y-0.5 hover:border-green-200 hover:shadow-md" href={h} key={h}>{x}<span className="float-right text-slate-400 transition group-hover:translate-x-1 group-hover:text-green-700">→</span></Link>)}</div></div>
  </>
}

