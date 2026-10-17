export type OrderStatus = 'material-pendiente' | 'corte' | 'armado' | 'listo' | 'instalado';
export type PaymentStatus = 'pendiente' | 'anticipo-pagado' | 'pagado';
export interface Product { id:string; name:string; category:'Cocina'|'Dormitorio'|'Sala'|'Oficina'; description:string; priceReference:number; material:string; finish:string; featured:boolean; visual:string; features:string[] }
export interface Customer { id:string; name:string; phone:string; address:string; totalPurchases:number; lastOrder:string }
export interface Order { id:string; customerId:string; customerName:string; productType:string; width:number; height:number; depth:number; material:string; finish:string; accessories:string[]; total:number; advancePaid:number; remainingBalance:number; status:OrderStatus; paymentStatus:PaymentStatus; createdAt:string; deliveryDate:string }
export interface Quote { type:string; width:number; height:number; depth:number; material:string; finish:string; accessories:string[]; materials:number; accessoriesCost:number; labour:number; total:number }
