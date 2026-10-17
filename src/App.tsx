import { useEffect, useState } from 'react';
import { products } from './data/products';
import { customers } from './data/customers';
import { useOrders } from './hooks/useOrders';
import type { Quote } from './types';
import { Toast } from './components/ui';
import { HomePage } from './pages/HomePage';
import { CatalogPage } from './pages/CatalogPage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { QuotePage } from './pages/QuotePage';
import { QuoteSummaryPage } from './pages/QuoteSummaryPage';
import { useToast } from './components/ui';
import { Dashboard, KanbanPage, CustomersPage, OrderDetail, OrdersPage, PaymentsPage } from './pages/admin/AdminPages';
import { AnalyticsPage } from './pages/admin/AnalyticsPage';
import { AIAssistant } from './components/AIAssistant';
const defaultQuote:Quote={type:'Closet',width:180,height:220,depth:60,material:'Melamina 18 mm',finish:'Roble',accessories:['Correderas telescópicas'],materials:1250,accessoriesCost:95,labour:750,total:2400};
export default function App(){const [path,setPath]=useState(window.location.pathname);const [quote,setQuote]=useState<Quote>(defaultQuote);const {orders,updateOrder,registerPayment}=useOrders();const {toast,show}=useToast();useEffect(()=>{const listener=()=>setPath(window.location.pathname);window.addEventListener('popstate',listener);return()=>window.removeEventListener('popstate',listener)},[]);const detail=path.match(/^\/producto\/([^/]+)$/);const adminOrder=path.match(/^\/admin\/pedido\/([^/]+)$/);let page;if(path==='/')page=<HomePage/>;else if(path==='/catalogo')page=<CatalogPage/>;else if(detail)page=<ProductDetailPage id={detail[1]}/>;else if(path==='/cotizador')page=<QuotePage onComplete={setQuote} initialType={new URLSearchParams(window.location.search).get('producto')??undefined}/>;else if(path==='/cotizacion')page=<QuoteSummaryPage quote={quote}/>;else if(path==='/admin')page=<Dashboard orders={orders}/>;else if(path==='/admin/pedidos')page=<OrdersPage orders={orders}/>;else if(path==='/admin/kanban')page=<KanbanPage orders={orders} onMove={(id,status)=>updateOrder(id,{status})} showToast={show}/>;else if(path==='/admin/pagos')page=<PaymentsPage orders={orders} onPayment={registerPayment} showToast={show}/>;else if(path==='/admin/clientes')page=<CustomersPage customers={customers} orders={orders}/>;else if(path==='/admin/analitica')page=<AnalyticsPage orders={orders}/>;else if(adminOrder){const order=orders.find(o=>o.id===adminOrder[1])??orders[0];page=<OrderDetail order={order} customer={customers.find(c=>c.id===order.customerId)} onMove={(id,status)=>{updateOrder(id,{status});show('Pedido actualizado correctamente.')}} onPayment={(id,amount)=>{registerPayment(id,amount);show('Pago registrado correctamente.')}}/>}else page=<HomePage/>;return <>{page}{!path.startsWith('/admin')&&<AIAssistant/>}<Toast message={toast}/></>}
