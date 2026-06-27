"use client";
import {useEffect,useState} from "react";import {api} from "../../../lib/api";import DataTable from "../../../components/DataTable";
export default function Invoices(){
 const [x,setX]=useState([]);useEffect(()=>{api("/invoices").then(d=>setX(d.items))},[]);
 async function pdf(id){const blob=await api(`/invoices/${id}/pdf`),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=`invoice-${id}.pdf`;a.click();URL.revokeObjectURL(url)}
 return <><h1 className="mb-1 text-2xl font-bold">Invoices</h1><p className="mb-5 text-sm text-slate-500">Tax invoices generated from sales.</p><div className="card"><DataTable data={x} columns={[{accessorKey:"invoice_number",header:"Invoice"},{accessorKey:"invoice_date",header:"Date"},{accessorKey:"subtotal",header:"Taxable"},{accessorKey:"gst_amount",header:"GST"},{accessorKey:"total",header:"Total"},{id:"actions",header:"Actions",cell:({row})=><div className="flex gap-3"><a className="text-blue-600" href={`/dashboard/invoices/${row.original.id}`}>Print View</a><button className="text-blue-600" onClick={()=>pdf(row.original.id)}>PDF</button></div>}]}/></div></>
}
