"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";

const format = new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR"});
export default function Dashboard(){
  const [data,setData]=useState(null);
  useEffect(()=>{api("/dashboard").then(setData)},[]);
  const cards=[["Total Sales",data?.sales_total],["Total Purchases",data?.purchase_total],["Receivables",data?.receivables],["Payables",data?.payables],["Stock Value",data?.stock_value],["Low Stock Items",data?.low_stock,true]];
  return <><div className="mb-6"><h1 className="text-2xl font-bold">Business Dashboard</h1><p className="text-sm text-slate-500">A live view of billing, inventory and accounting.</p></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{cards.map(([label,value,count])=><div className="card p-5" key={label}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold">{data?count?value:format.format(value):"—"}</p></div>)}</div>
    <div className="mt-6 grid gap-4 md:grid-cols-4">{[["Create Sale","/dashboard/sales"],["Record Purchase","/dashboard/purchases"],["Adjust Stock","/dashboard/inventory"],["View Reports","/dashboard/reports"]].map(([x,h])=><Link className="card p-5 font-semibold hover:border-blue-400" href={h} key={h}>{x}<span className="float-right">→</span></Link>)}</div>
  </>
}
