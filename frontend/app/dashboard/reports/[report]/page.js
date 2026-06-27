"use client";
import {use,useEffect,useMemo,useState} from "react";
import DataTable from "../../../../components/DataTable";
import {Button} from "../../../../components/ui";
import {api} from "../../../../lib/api";
export default function Report({params}){
 const {report}=use(params),[items,setItems]=useState([]);
 useEffect(()=>{api(`/reports/${report}`).then(x=>setItems(x.items))},[report]);
 const columns=useMemo(()=>items.length?Object.keys(items[0]).filter(x=>x!=="id").map(k=>({accessorKey:k,header:k.replaceAll("_"," ")})):[],[items]);
 async function excel(){const blob=await api(`/reports/${report}/excel`);const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=`${report}.xlsx`;a.click();URL.revokeObjectURL(url)}
 return <><div className="mb-5 flex items-end justify-between"><div><h1 className="text-2xl font-bold capitalize">{report.replaceAll("-"," ")}</h1><p className="text-sm text-slate-500">Generated from posted transactions.</p></div><Button onClick={excel}>Export Excel</Button></div><div className="card"><DataTable columns={columns} data={items}/></div></>
}
