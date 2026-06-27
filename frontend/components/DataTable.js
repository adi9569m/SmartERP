"use client";

import { useRef } from "react";
import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";

export default function DataTable({ columns, data, empty = "No records found", onRowActivate }) {
  const table = useReactTable({ columns, data, getCoreRowModel: getCoreRowModel() });
  const bodyRef = useRef(null);
  function move(event, index) {
    if (!["ArrowDown", "ArrowUp", "Home", "End", "Enter"].includes(event.key)) return;
    if (event.key === "Enter" && onRowActivate) {
      event.preventDefault();
      onRowActivate(data[index]);
      return;
    }
    if (event.key === "Enter") return;
    event.preventDefault();
    const rows = bodyRef.current?.querySelectorAll("[data-erp-row]") || [];
    const next = event.key === "Home" ? 0 : event.key === "End" ? rows.length - 1 :
      Math.max(0, Math.min(rows.length - 1, index + (event.key === "ArrowDown" ? 1 : -1)));
    rows[next]?.focus();
  }
  return <div className="overflow-x-auto">
    <table className="w-full text-left text-sm">
      <thead className="border-b bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
        {table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) =>
          <th className="px-4 py-3" key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>
        )}</tr>)}
      </thead>
      <tbody className="divide-y" ref={bodyRef}>
        {table.getRowModel().rows.map((row, index) => <tr data-erp-row tabIndex="0" onKeyDown={(e) => move(e, index)} onDoubleClick={() => onRowActivate?.(row.original)} className="outline-none hover:bg-slate-50 focus:bg-blue-50 focus:ring-2 focus:ring-inset focus:ring-blue-500" key={row.id}>{row.getVisibleCells().map((cell) =>
          <td className="whitespace-nowrap px-4 py-3" key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
        )}</tr>)}
        {!data.length && <tr><td className="px-4 py-12 text-center text-slate-400" colSpan={columns.length}>{empty}</td></tr>}
      </tbody>
    </table>
  </div>;
}
