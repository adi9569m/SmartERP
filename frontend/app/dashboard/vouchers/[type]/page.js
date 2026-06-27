"use client";
import {use,useEffect,useState} from "react";
import {api} from "../../../../lib/api";
import {Button,Input,Select} from "../../../../components/ui";
export default function Voucher({params}){
 const {type}=use(params),[ledgers,setLedgers]=useState([]),[lines,setLines]=useState([{ledger_id:"",debit:0,credit:0},{ledger_id:"",debit:0,credit:0}]),[narration,setNarration]=useState(""),[message,setMessage]=useState("");
 useEffect(()=>{api("/ledgers").then(x=>setLedgers(x.items))},[]);
 function set(i,k,v){setLines(lines.map((x,j)=>j===i?{...x,[k]:v}:x))}
 async function save(e){e.preventDefault();try{const x=await api("/vouchers",{method:"POST",body:JSON.stringify({voucher_type:type,entries:lines,narration})});setMessage(`Posted ${x.voucher_number}`)}catch(e){setMessage(e.message)}}
 return <><h1 className="mb-1 text-2xl font-bold capitalize">{type} Voucher</h1><p className="mb-5 text-sm text-slate-500">Double-entry posting. Total debit must equal total credit.</p><form onSubmit={save} className="card p-5"><div className="space-y-3">{lines.map((x,i)=><div className="grid gap-3 rounded border p-3 md:grid-cols-3" key={i}><Select autoFocus={i===0} label="Ledger" value={x.ledger_id} onChange={e=>set(i,"ledger_id",e.target.value)} required><option value="">Select ledger</option>{ledgers.map(l=><option value={l.id} key={l.id}>{l.name}</option>)}</Select><Input label="Debit" type="number" min="0" step=".01" value={x.debit} onChange={e=>set(i,"debit",e.target.value)}/><Input label="Credit" type="number" min="0" step=".01" value={x.credit} onChange={e=>set(i,"credit",e.target.value)}/></div>)}</div><Button type="button" variant="secondary" className="my-4" onClick={()=>setLines([...lines,{ledger_id:"",debit:0,credit:0}])}>Add Entry</Button><Input label="Narration" value={narration} onChange={e=>setNarration(e.target.value)}/>{message&&<p className="my-3 text-sm">{message}</p>}<Button className="mt-4">Post Voucher</Button></form></>
}
