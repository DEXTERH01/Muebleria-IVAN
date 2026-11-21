export type OrderStatus = 'material-pendiente' | 'corte' | 'armado' | 'listo' | 'instalado';
export type PaymentStatus = 'pendiente' | 'anticipo-pagado' | 'pagado';
export interface Customer { id:string; name:string; phone:string; address:string; totalPurchases:number; lastOrder:string }
export interface Order { id:string; customerId:string; customerName:string; productType:string; width:number; height:number; depth:number; material:string; finish:string; accessories:string[]; total:number; advancePaid:number; remainingBalance:number; status:OrderStatus; paymentStatus:PaymentStatus; createdAt:string; deliveryDate:string }
