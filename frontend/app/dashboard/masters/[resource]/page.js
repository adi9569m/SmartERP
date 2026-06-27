"use client";

import { use, useEffect, useMemo, useState } from "react";
import DataTable from "../../../../components/DataTable";
import { Button, Input, Modal, Select } from "../../../../components/ui";
import { api } from "../../../../lib/api";

const configs={
  groups:{title:"Group Management",fields:[["name","Name"],["category","Category","select",["Assets","Liabilities","Income","Expenses"]]]},
  ledgers:{title:"Ledger Management",fields:[["name","Ledger Name"],["ledger_type","Type","select",["customer","supplier","expense","income","bank","cash","asset","liability"]],["opening_balance","Opening Balance","number"]]},
  "stock-groups":{title:"Stock Groups",fields:[["name","Name"]]},
  units:{title:"Units",fields:[["name","Unit Name"],["symbol","Symbol"]]},
  "stock-items":{title:"Stock Items",fields:[["name","Item Name"],["sku","SKU"],["hsn_code","HSN Code"],["purchase_price","Purchase Price","number"],["selling_price","Selling Price","number"],["quantity","Quantity","number"],["gst_percent","GST %","number"],["reorder_level","Reorder Level","number"],["reserved_stock","Reserved","number"],["damaged_stock","Damaged","number"]]},
  customers:{title:"Customers",fields:[["name","Customer Name"],["gst","GST Number"],["mobile","Mobile"],["address","Address"],["outstanding_balance","Outstanding Balance","number"]]},
  suppliers:{title:"Suppliers",fields:[["name","Supplier Name"],["gst","GST Number"],["mobile","Mobile"],["address","Address"],["outstanding_balance","Outstanding Balance","number"]]},
};
export default function ResourcePage({params}){
  const {resource}=use(params), cfg=configs[resource], [data,setData]=useState([]),[search,setSearch]=useState(""),[form,setForm]=useState({}),[open,setOpen]=useState(false),[error,setError]=useState("");
  async function load(q=search){const rows=(await api(`/${resource}?search=${encodeURIComponent(q)}`)).items;setData(rows);return rows}
  useEffect(()=>{load().then(rows=>{const action=new URLSearchParams(location.search).get("action");if(action==="create"){setForm({});setOpen(true)}else if(action==="alter"){setTimeout(()=>document.querySelector("[data-erp-row]")?.focus(),0)}});const fn=e=>{setSearch(e.detail);load(e.detail)};window.addEventListener("erp-search",fn);return()=>window.removeEventListener("erp-search",fn)},[resource]);
  async function save(e){e.preventDefault();setError("");try{await api(`/${resource}${form.id?`/${form.id}`:""}`,{method:form.id?"PUT":"POST",body:JSON.stringify(form)});setOpen(false);load()}catch(e){setError(e.message)}}
  async function remove(id){if(confirm("Delete this record?")){await api(`/${resource}/${id}`,{method:"DELETE"});load()}}
  const columns=useMemo(()=>[...cfg.fields.slice(0,6).map(([key,label])=>({accessorKey:key,header:label})),{id:"actions",header:"Actions",cell:({row})=><div className="flex gap-2"><button className="text-blue-600" onClick={()=>{setForm(row.original);setOpen(true)}}>Edit</button><button className="text-red-600" onClick={()=>remove(row.original.id)}>Delete</button>{["customers","suppliers"].includes(resource)&&<a className="text-slate-600" href={`/dashboard/parties/${resource}/${row.original.id}`}>Statement</a>}</div>}],[resource]);
  if(!cfg)return <p>Unknown master.</p>;
  return <><div className="mb-5 flex items-end justify-between"><div><h1 className="text-2xl font-bold">{cfg.title}</h1><p className="text-sm text-slate-500">Create, search, edit and remove records.</p></div><Button onClick={()=>{setForm({});setOpen(true)}}>Add New</Button></div>
    <div className="card"><div className="border-b p-4"><input className="field max-w-sm" placeholder="Search…" value={search} onChange={e=>{setSearch(e.target.value);load(e.target.value)}}/></div><DataTable columns={columns} data={data} onRowActivate={row=>{setForm(row);setOpen(true)}}/></div>
    <Modal title={`${form.id?"Edit":"New"} ${cfg.title}`} open={open} onClose={()=>setOpen(false)}><form onSubmit={save} className="grid gap-4 md:grid-cols-2">{cfg.fields.map(([key,label,type,options],index)=>type==="select"?<Select autoFocus={index===0} key={key} label={label} value={form[key]||""} onChange={e=>setForm({...form,[key]:e.target.value})} required><option value="">Select</option>{options.map(x=><option key={x}>{x}</option>)}</Select>:<Input autoFocus={index===0} key={key} label={label} type={type||"text"} step="0.01" value={form[key]??""} onChange={e=>setForm({...form,[key]:e.target.value})} required={["name","sku","symbol","ledger_type"].includes(key)}/>)}{error&&<p className="text-red-600 md:col-span-2">{error}</p>}<Button className="md:col-span-2">Save</Button></form></Modal>
  </>
}
