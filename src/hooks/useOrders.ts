import { useEffect, useState } from 'react';
import { seedOrders } from '../data/orders';
import type { Order } from '../types';
const KEY='muebleflow-orders';
const load=():Order[]=>{ try { const raw=localStorage.getItem(KEY); return raw ? JSON.parse(raw) as Order[] : seedOrders; } catch { return seedOrders; } };
export function useOrders(){
 const [orders,setOrders]=useState<Order[]>(load);
 useEffect(()=>localStorage.setItem(KEY,JSON.stringify(orders)),[orders]);
 const updateOrder=(id:string, patch:Partial<Order>)=>setOrders(current=>current.map(order=>order.id===id?{...order,...patch}:order));
 const registerPayment=(id:string, amount:number)=>setOrders(current=>current.map(order=>{
   if(order.id!==id)return order; const advancePaid=order.advancePaid+amount; const remainingBalance=Math.max(0,order.total-advancePaid); return {...order,advancePaid,remainingBalance,paymentStatus:remainingBalance===0?'pagado':advancePaid>0?'anticipo-pagado':'pendiente'};
 }));
 const reset=()=>setOrders(seedOrders);
 return {orders,updateOrder,registerPayment,reset};
}
