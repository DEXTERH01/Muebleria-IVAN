import type { OrderStatus, PaymentStatus } from '../types';
export const money = (value:number) => `S/ ${value.toLocaleString('es-PE', {minimumFractionDigits:0, maximumFractionDigits:0})}`;
export const date = (value:string) => new Intl.DateTimeFormat('es-PE',{day:'2-digit',month:'short',year:'numeric'}).format(new Date(`${value}T12:00:00`));
export const orderStatusLabel:Record<OrderStatus,string> = {'material-pendiente':'Material pendiente',corte:'En corte',armado:'En armado',listo:'Listo para entrega',instalado:'Instalado'};
export const paymentStatusLabel:Record<PaymentStatus,string> = {pendiente:'Anticipo pendiente','anticipo-pagado':'50% pagado',pagado:'Pagado'};
export const statusSteps:OrderStatus[] = ['material-pendiente','corte','armado','listo','instalado'];
