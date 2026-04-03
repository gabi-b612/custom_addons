/** @odoo-module **/
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Patch OrderSummary to enhance threshold checking in _setValue method
 * This ensures threshold is checked when quantity is changed via numpad
 */
patch(OrderSummary.prototype, {

    /**
     * Get product stock quantity based on location and stock type
     */
    getProductStockQuantity(product, selectedLine) {
        const pos = this.pos;
        const stockType = pos.res_setting?.stock_type || 'on_hand';
        const stockFrom = pos.res_setting?.stock_from || 'all_warehouse';
        const configLocationId = pos.res_setting?.raw?.stock_location_id;

        // For 'all_warehouse' - use product fields directly
        if (stockFrom === 'all_warehouse') {
            if (stockType === 'on_hand') {
                return product.qty_available || 0;
            } else if (stockType === 'outgoing_qty') {
                return product.outgoing_qty || 0;
            } else if (stockType === 'forecasted') {
                return product.virtual_available || 0;
            } else if (stockType === 'incoming_qty') {
                return product.incoming_qty || 0;
            }
        }

        // For 'current_warehouse' - calculate from stock_quant
        if (stockFrom === 'current_warehouse' && configLocationId) {
            const stock_quant = pos.stock_quant || [];
            const product_product = pos.product_product || [];
            const move_line = pos.move_line || [];

            // Get all variants of this product template
            const main_product = product_product.find(p => p.id === product.id);
            if (!main_product) return 0;

            const product_tmpl_id = main_product.raw.product_tmpl_id;
            const product_variants = product_product.filter(p => p.raw.product_tmpl_id === product_tmpl_id);
            const variant_ids = product_variants.map(v => v.id);

            if (stockType === 'on_hand') {
                let total_qty = 0;
                stock_quant.forEach((quant) => {
                    if (quant?.product_id && variant_ids.includes(quant.product_id.id)) {
                        const quant_location_id = quant.raw.location_id;
                        if (quant_location_id === configLocationId) {
                            total_qty += quant.available_quantity || 0;
                        }
                    }
                });
                return total_qty;
            } else if (stockType === 'outgoing_qty') {
                let total_outgoing = 0;
                move_line.forEach((line) => {
                    if (line?.product_id && variant_ids.includes(line.product_id.id)) {
                        const line_location_id = line.raw.location_id;
                        if (line_location_id === configLocationId) {
                            total_outgoing += line.product_id.outgoing_qty || 0;
                        }
                    }
                });
                return total_outgoing;
            } else if (stockType === 'incoming_qty') {
                let total_incoming = 0;
                move_line.forEach((line) => {
                    if (line?.product_id && variant_ids.includes(line.product_id.id)) {
                        const line_dest_location_id = line.raw.location_dest_id;
                        if (line_dest_location_id === configLocationId) {
                            total_incoming += line.product_id.incoming_qty || 0;
                        }
                    }
                });
                return total_incoming;
            } else if (stockType === 'forecasted') {
                let on_hand = 0;
                let outgoing = 0;
                let incoming = 0;

                stock_quant.forEach((quant) => {
                    if (quant?.product_id && variant_ids.includes(quant.product_id.id)) {
                        const quant_location_id = quant.raw.location_id;
                        if (quant_location_id === configLocationId) {
                            on_hand += quant.available_quantity || 0;
                        }
                    }
                });

                move_line.forEach((line) => {
                    if (line?.product_id && variant_ids.includes(line.product_id.id)) {
                        const line_location_id = line.raw.location_id;
                        const line_dest_location_id = line.raw.location_dest_id;

                        if (line_location_id === configLocationId) {
                            outgoing += line.product_id.outgoing_qty || 0;
                        }
                        if (line_dest_location_id === configLocationId) {
                            incoming += line.product_id.incoming_qty || 0;
                        }
                    }
                });

                return on_hand - outgoing + incoming;
            }
        }

        return 0;
    },

    /**
     * Check if setting quantity would breach threshold
     */
    checkThresholdBreach(selectedLine, newQuantity) {
        const pos = this.pos;
        const product = selectedLine.product_id;

        // Only check if threshold is enabled
        const thresholdQty = pos.config?.threshold_qty;
        if (thresholdQty === undefined || thresholdQty === null) {
            return { breached: false, availableQty: newQuantity, message: '' };
        }

        const thresholdMessage = pos.config?.threshold_message || _t("Stock is below the threshold limit.");

        // Get current stock quantity
        const currentStock = this.getProductStockQuantity(product, selectedLine);

        // Calculate total quantity in cart for this product (excluding current line)
        const order = this.currentOrder;
        let totalCartQty = 0;
        if (order) {
            order.get_orderlines().forEach(line => {
                if (line.product_id.id === product.id && line.uuid !== selectedLine.uuid) {
                    totalCartQty += line.get_quantity();
                }
            });
        }

        // Calculate remaining stock after this order
        const remainingStock = currentStock - totalCartQty - newQuantity;

        // Check if threshold is breached
        if (remainingStock < thresholdQty) {
            const maxAllowedQty = Math.max(0, currentStock - thresholdQty - totalCartQty);

            return {
                breached: true,
                availableQty: maxAllowedQty,
                currentStock: currentStock,
                thresholdQty: thresholdQty,
                totalCartQty: totalCartQty,
                message: maxAllowedQty > 0
                    ? _t(`${thresholdMessage}\n\nCurrent Stock: ${currentStock}\nThreshold: ${thresholdQty}\n\nMaximum you can add: ${maxAllowedQty} units`)
                    : _t(`${thresholdMessage}\n\nCurrent Stock: ${currentStock}\nThreshold: ${thresholdQty}\n\nCannot add more items.`)
            };
        }

        return { breached: false, availableQty: newQuantity, message: '' };
    },

    _setValue(val) {
        const { numpadMode } = this.pos;
        let selectedLine = this.currentOrder.get_selected_orderline();

        if (selectedLine) {
            if (numpadMode === "quantity") {
                if (selectedLine.combo_parent_id) {
                    selectedLine = selectedLine.combo_parent_id;
                }

                if (val === "remove") {
                    this.currentOrder.removeOrderline(selectedLine);
                } else {
                    // THRESHOLD CHECK BEFORE SETTING QUANTITY
                    const pos = this.pos;
                    const newQty = parseFloat(val);

                    // Check threshold for products
                    if (pos.config?.threshold_qty !== undefined) {

                        const thresholdCheck = this.checkThresholdBreach(selectedLine, newQty);

                        if (thresholdCheck.breached) {
                            if (thresholdCheck.availableQty <= 0) {
                                // No stock available
                                this.dialog.add(AlertDialog, {
                                    title: _t('Stock Below Threshold'),
                                    body: thresholdCheck.message,
                                });
                                this.numberBuffer.reset();
                                return; // Don't allow quantity change
                            } else {
                                // Some stock available - show warning and set to max
                                this.dialog.add(AlertDialog, {
                                    title: _t('Stock Below Threshold'),
                                    body: thresholdCheck.message + _t('\n\nQuantity will be adjusted to maximum allowed: %s', thresholdCheck.availableQty),
                                });

                                // Set to maximum allowed quantity
                                const result = selectedLine.set_quantity(
                                    thresholdCheck.availableQty,
                                    Boolean(selectedLine.combo_line_ids?.length)
                                );

                                for (const line of selectedLine.combo_line_ids || []) {
                                    line.set_quantity(thresholdCheck.availableQty, true);
                                }

                                if (result !== true && result !== undefined) {
                                    this.dialog.add(AlertDialog, result);
                                }

                                this.numberBuffer.reset();
                                return;
                            }
                        }
                    }

                    // No threshold issue - proceed normally
                    const result = selectedLine.set_quantity(
                        val,
                        Boolean(selectedLine.combo_line_ids?.length)
                    );

                    for (const line of selectedLine.combo_line_ids || []) {
                        line.set_quantity(val, true);
                    }

                    if (result !== true && result !== undefined) {
                        this.dialog.add(AlertDialog, result);
                        this.numberBuffer.reset();
                    }
                }
            } else if (numpadMode === "discount" && val !== "remove") {
                this.pos.setDiscountFromUI(selectedLine, val);
            } else if (numpadMode === "price" && val !== "remove") {
                this.setLinePrice(selectedLine, val);
            }
        }
    }
});