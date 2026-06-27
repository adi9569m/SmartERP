"use client";

import { useEffect, useState } from "react";
import DataTable from "./DataTable";
import { Button, Input, Select } from "./ui";
import { api } from "../lib/api";

export default function TradeVoucher({kind}){
  const isSale=kind==="sales", partyPath=isSale?"customers":"suppliers", partyKey=isSale?"customer_id":"supplier_id";
  const [parties,setParties]=useState([]),[items,setItems]=useState([]),[history,setHistory]=useState([]),[party,setParty]=useState(""),[lines,setLines]=useState([{item_id:"",quantity:1,unit_price:""}]),[notes,setNotes]=useState(""),[error,setError]=useState(""),[saved,setSaved]=useState(null);
  async function load(){const [p,i,h]=await Promise.all([api(`/${partyPath}`),api("/stock-items"),api(`/${kind}`)]);setParties(p.items);setItems(i.items);setHistory(h.items)}
  useEffect(()=>{load()},[kind]);
  function update(index,key,value){setLines(lines.map((x,i)=>i===index?{...x,[key]:value}:x))}
  function selectItem(index,value){
    const item=items.find(x=>x.id===Number(value));
    setLines(lines.map((line,i)=>i===index?{
      ...line,
      item_id:value,
      unit_price:item?(isSale?item.selling_price:item.purchase_price):""
    }:line));
  }
  async function submit(e){e.preventDefault();setError("");try{const result=await api(`/${kind}`,{method:"POST",body:JSON.stringify({[partyKey]:party,items:lines,notes})});setSaved(result);setLines([{item_id:"",quantity:1,unit_price:""}]);setNotes("");load()}catch(err){setError(err.message)}}
  return <><div className="mb-5"><h1 className="text-2xl font-bold">{isSale?"Sales Voucher":"Purchase Voucher"}</h1><p className="text-sm text-slate-500">{isSale?"Creates an invoice, reduces stock and updates the customer ledger.":"Increases stock and updates the supplier ledger."}</p></div>
    <form onSubmit={submit} className="card mb-6 p-5"><div className="max-w-sm"><Select autoFocus label={isSale?"Customer":"Supplier"} value={party} onChange={e=>setParty(e.target.value)} required><option value="">Select party</option>{parties.map(x=><option value={x.id} key={x.id}>{x.name}</option>)}</Select></div>
      <div className="my-5 space-y-3">{lines.map((line,index)=><div className="grid gap-3 rounded border bg-slate-50 p-3 md:grid-cols-[2fr_1fr_1fr_auto]" key={index}><Select label="Stock Item" value={line.item_id} onChange={e=>selectItem(index,e.target.value)} required><option value="">Select item</option>{items.map(x=><option value={x.id} key={x.id}>{x.name} ({x.quantity})</option>)}</Select><Input label="Quantity" type="number" min=".001" step=".001" value={line.quantity} onChange={e=>update(index,"quantity",e.target.value)} required/><Input label="Unit Price" type="number" min=".01" step=".01" value={line.unit_price} onChange={e=>update(index,"unit_price",e.target.value)} required/><Button type="button" variant="danger" className="self-end" disabled={lines.length===1} onClick={()=>setLines(lines.filter((_,i)=>i!==index))}>Remove</Button></div>)}</div>
      <Button type="button" variant="secondary" onClick={()=>setLines([...lines,{item_id:"",quantity:1,unit_price:""}])}>Add Line</Button><div className="mt-4"><Input label="Notes" value={notes} onChange={e=>setNotes(e.target.value)}/></div>
      {error&&<p className="mt-3 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}{saved&&<p className="mt-3 rounded bg-green-50 p-3 text-sm text-green-700">Saved {saved.voucher_number}{saved.invoice?` · Invoice ${saved.invoice.invoice_number}`:""}.</p>}<Button className="mt-4">Post {isSale?"Sale":"Purchase"}</Button>
    </form>
    <div className="card"><h2 className="border-b p-4 font-bold">Recent {isSale?"Sales":"Purchases"}</h2><DataTable data={history} columns={[{accessorKey:"voucher_number",header:"Voucher"},{accessorKey:"voucher_date",header:"Date"},{accessorKey:"subtotal",header:"Taxable"},{accessorKey:"gst_amount",header:"GST"},{accessorKey:"total",header:"Total"}]}/></div>
  </>
}
