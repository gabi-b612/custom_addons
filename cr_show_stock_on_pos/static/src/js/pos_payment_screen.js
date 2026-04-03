/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
    },
    async validateOrder(isForceValidate) {
        const order = this.pos.get_order();
        const lines = order.get_orderlines();
        if (this.pos.res_setting['stock_from'] === 'all_warehouse') {
            if (this.pos.res_setting['stock_type'] === 'on_hand') {
                lines.forEach((line) => {
                    const order_quantity = line.qty;
                    const new_qty = line.product_id.qty_available - order_quantity;
                    line.product_id.qty_available = new_qty;
                });
            } else if (this.pos.res_setting['stock_type'] === 'outgoing_qty') {
                lines.forEach((line) => {
                    const order_quantity = line.qty;
                    // Add logic if needed for outgoing_qty
                });
            } else if (this.pos.res_setting['stock_type'] === 'incoming_qty') {
                lines.forEach((line) => {
                    const order_quantity = line.qty;
                    // Add logic if needed for incoming_qty
                });
            }
        } else if (this.pos.res_setting['stock_from'] === 'current_warehouse') {
            if (this.pos.res_setting['stock_type'] === 'on_hand') {
                lines.forEach((line) => {
                    const item_quantity = line.qty;
                    const on_hand_qty = line.product_id.qty_available;
                    const new_qty = on_hand_qty - item_quantity;
                    line.product_id.qty_available = new_qty;
                });
            } else if (this.pos.res_setting['stock_type'] === 'outgoing_qty') {
                lines.forEach((line) => {
                    const item_quantity = line.qty;
                    const out_going = line.product_id.outgoing;
                    // Add logic if needed for outgoing_qty
                });
            } else if (this.pos.res_setting['stock_type'] === 'incoming_qty') {
                lines.forEach((line) => {
                    const item_quantity = line.qty;
                    const incoming = line.product_id.incoming;
                    // Add logic if needed for incoming_qty
                });
            }
        }
        return super.validateOrder(isForceValidate);
    },
});
