"use client";
import {useEffect,useState} from "react";import {api} from "../../../lib/api";import DataTable from "../../../components/DataTable";
export default function Banking(){const [x,setX]=useState([]);useEffect(()=>{api("/banking").then(d=>setX(d.items))},[]);return <><h1 className="mb-1 text-2xl font-bold">Banking</h1><p className="mb-5 text-sm text-slate-500">Cash and bank ledger balances.</p><div className="card"><DataTable data={x} columns={[{accessorKey:"name",header:"Ledger"},{accessorKey:"balance",header:"Current Balance"}]}/></div></>}
