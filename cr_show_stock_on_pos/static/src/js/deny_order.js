/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    setup(){
        super.setup();

        // Set disable_negative_qty_product to false if allow_negative_products_to_order is true
        if (this.pos.config.allow_negative_products_to_order) {
            this.pos.config.disable_negative_qty_product = false;
        }
    },

    getProductQuantityForLocation(product) {

        const stockType = this.pos.res_setting?.stock_type || 'on_hand';
        const stockFrom = this.pos.res_setting?.stock_from || 'all_warehouse';

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
        if (stockFrom === 'current_warehouse') {
            const configLocationId = this.pos.res_setting?.raw?.stock_location_id;

            if (!configLocationId) {
                return 0;
            }

            const stock_quant = this.pos.stock_quant || [];
            const product_product = this.pos.product_product || [];
            const move_line = this.pos.move_line || [];

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

    get productsToDisplay() {
        let list = [];

        if (this.searchWord !== "") {
            if (!this._searchTriggered) {
                this.pos.setSelectedCategory(0);
                this._searchTriggered = true;
            }
            list = this.addMainProductsToDisplay(this.getProductsBySearchWord(this.searchWord));
        } else {
            this._searchTriggered = false;
            if (this.pos.selectedCategory?.id) {
                list = this.getProductsByCategory(this.pos.selectedCategory);
            } else {
                list = this.products;
            }
        }

        if (!list || list.length === 0) {
            return [];
        }

        const excludedProductIds = [
            this.pos.config.tip_product_id?.id,
            ...this.pos.hiddenProductIds,
            ...this.pos.session._pos_special_products_ids,
        ];

        const filteredList = [];

        for (const product of list) {
            if (filteredList.length >= 100) {
                break;
            }
            if (!excludedProductIds.includes(product.id) && product.canBeDisplayed) {
                // Get the correct quantity based on location and stock_type
                const productQty = this.getProductQuantityForLocation(product);

                // Apply show_negative_qty_products filter
                if (this.pos.config.show_negative_qty_products || productQty > 0) {
                    filteredList.push(product);
                }
            }
        }

        return this.searchWord !== ""
            ? filteredList
            : filteredList.sort((a, b) => a.display_name.localeCompare(b.display_name));
    },

    /**
     * FIXED: Check threshold considering items already in cart
     */
    async addProductToOrder(event) {

        const current_product_id = event.id;
        const thresholdQty = this.pos.config?.threshold_qty;

        // Skip threshold check if not configured
        if (thresholdQty === undefined || thresholdQty === null) {
            super.addProductToOrder(event);
            return;
        }

        const thresholdMessage = this.pos.config?.threshold_message || _t("Stock is below the threshold limit.");

        // Get current stock based on location and stock type
        const currentStock = this.getProductQuantityForLocation(event);

        // Calculate quantity already in cart for this product
        const order = this.pos.get_order();
        let cartQty = 0;
        if (order) {
            order.get_orderlines().forEach(line => {
                if (line.product_id.id === current_product_id) {
                    cartQty += line.get_quantity();
                }
            });
        }

        // Calculate remaining stock after adding 1 more unit
        const remainingAfterAdd = currentStock - cartQty - 1;

        // Check if threshold would be breached
        if (remainingAfterAdd < thresholdQty) {
            const maxAllowedToAdd = Math.max(0, currentStock - thresholdQty - cartQty);

            if (maxAllowedToAdd <= 0) {
                // Cannot add any more items
                await this.dialog.add(AlertDialog, {
                    title: _t('Stock Below Threshold'),
                    body: _t(`${thresholdMessage}\n\nCurrent Stock: ${currentStock}\nAlready in Cart: ${cartQty}\nThreshold: ${thresholdQty}\n\n❌ Cannot add more items.`),
                });
                return; // Don't add the product
            } else {
                // Can add, but with warning
                await this.dialog.add(ConfirmationDialog, {
                    title: _t('Stock Below Threshold Warning'),
                    body: _t(`${thresholdMessage}\n\nCurrent Stock: ${currentStock}\nAlready in Cart: ${cartQty}\nThreshold: ${thresholdQty}\n\n⚠️ You can add maximum ${maxAllowedToAdd} more unit(s).\n\nDo you want to continue adding this item?`),
                    confirmLabel: _t("Add to Cart"),
                    confirm: () => {
                        super.addProductToOrder(event);
                    },
                    cancel: () => {},
                    cancelLabel: _t("Cancel"),
                });
                return;
            }
        }

        // No threshold breach, add normally
        super.addProductToOrder(event);
    },
});