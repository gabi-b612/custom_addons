/** @odoo-module */
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.state = useState({
            qty_available: null,
            incoming_qty: null,
            virtual_available: null,
            outgoing_qty: null,
            display_stock: false,
            show_product_trend: false,
        });

        this.product = this.props?.product || this.pos?.db?.product_by_id[this.props.productId] || {};
        this.product.total_sold = this.product.total_sold || 0;
        this.product.total_added = this.product.total_added || 0;
        this.stockTrend = this.product.stock_trend || 'neutral';
        this.showStock = this.pos?.res_setting?.display_stock || false;

        this.showProductTrend = this.pos?.config?.show_product_trend || false;
        this.thresholdQty = this.pos?.config?.threshold_qty || -1000;
        this.thresholdMessage = this.pos?.res_setting?.threshold_message || _t("Stock is below the threshold limit.");
        this.stockDisplayType = this.pos?.res_setting?.stock_type || 'on_hand';
        this.stockFrom = this.pos?.res_setting?.stock_from || 'all_warehouse';

        if (this.showStock && this.product) {
            // Calculate quantity based on location and stock type
            this.qty = this.getProductQuantity();

            this.isVisible = this.pos?.config?.show_negative_qty_products || this.qty > 0;
            this.isDisabled = this.pos?.config?.disable_negative_qty_product && this.qty <= 0;
            this.stockTrend = this.product.stock_trend || 'neutral';
        } else {
            this.qty = 0;
            this.isVisible = true;
            this.isDisabled = false;
            this.stockTrend = 'neutral';
        }

        this.onClick = this.onClick.bind(this);

        // Initialize state with product data directly from loaded data
        this.initializeStateFromProduct();
    },

    initializeStateFromProduct() {
        // Use already loaded product data instead of fetching again
        if (this.product) {
            this.state.qty_available = this.product.qty_available || 0;
            this.state.incoming_qty = this.product.incoming_qty || 0;
            this.state.outgoing_qty = this.product.outgoing_qty || 0;
            this.state.virtual_available = this.product.virtual_available || 0;
        }
    },

    getProductQuantity() {
        const product = this.props.product || this.product;
        const productId = this.props.productId;

        // For 'all_warehouse' - use product fields directly
        if (this.stockFrom === 'all_warehouse') {
            if (this.stockDisplayType === 'on_hand') {
                return product.qty_available || 0;
            } else if (this.stockDisplayType === 'outgoing_qty') {
                return product.outgoing_qty || 0;
            } else if (this.stockDisplayType === 'forecasted') {
                return product.virtual_available || 0;
            } else if (this.stockDisplayType === 'incoming_qty') {
                return product.incoming_qty || 0;
            }
        }

        // For 'current_warehouse' - calculate from stock_quant for the specific location
        if (this.stockFrom === 'current_warehouse') {
            const configLocationId = this.pos.res_setting?.raw?.stock_location_id;

            if (!configLocationId) {
                return 0;
            }

            const stock_quant = this.pos.stock_quant || [];
            const product_product = this.pos.product_product || [];
            const move_line = this.pos.move_line || [];

            // Get all variants of this product template
            const main_product = product_product.find(p => p.id === productId);
            if (!main_product) return 0;

            const product_tmpl_id = main_product.raw.product_tmpl_id;
            const product_variants = product_product.filter(p => p.raw.product_tmpl_id === product_tmpl_id);
            const variant_ids = product_variants.map(v => v.id);

            if (this.stockDisplayType === 'on_hand') {
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
            } else if (this.stockDisplayType === 'outgoing_qty') {
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
            } else if (this.stockDisplayType === 'incoming_qty') {
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
            } else if (this.stockDisplayType === 'forecasted') {
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

    getCartQuantity() {
        if (!this.pos) return 0;
        const order = this.pos.get_order();
        return order ? order.get_quantity_by_product_id(this.product.id) || 0 : 0;
    },

    async onClick(requestedQty = 1) {
        if (!this.pos || !this.dialog) {
            return;
        }

        const currentQty = this.getProductQuantity();
        const cartQty = this.getCartQuantity();
        const effectiveStock = currentQty - cartQty;
        const newStockQty = effectiveStock - requestedQty;

        if (this.showStock && newStockQty < this.thresholdQty) {
            const availableQty = Math.max(0, effectiveStock - this.thresholdQty);
            const adjustedQty = Math.min(requestedQty, availableQty);

            this.dialog.add(ConfirmationDialog, {
                title: _t("Stock Below Threshold"),
                body: adjustedQty <= 0
                    ? _t(this.thresholdMessage)
                    : _t(`${this.thresholdMessage} Only ${adjustedQty} can be added to keep ${this.thresholdQty} in stock.`),
                confirmLabel: adjustedQty > 0 ? _t("Add Adjusted Quantity") : _t("OK"),
                confirm: () => {
                    if (adjustedQty > 0) {
                        this.pos.addProductToCurrentOrder(this.product, { quantity: adjustedQty });
                        this.updateQty();
                    }
                },
                cancel: () => {},
            });
            return;
        }

        this.pos.addProductToCurrentOrder(this.product, { quantity: requestedQty });
        this.updateQty();
    },

    updateQty() {
        if (!this.pos) return;
        this.qty = this.getProductQuantity();
        this.stockTrend = this.product.stock_trend || 'neutral';

        // Update state with current product values (no ORM call needed)
        this.state.qty_available = this.product.qty_available || 0;
        this.state.incoming_qty = this.product.incoming_qty || 0;
        this.state.outgoing_qty = this.product.outgoing_qty || 0;
        this.state.virtual_available = this.product.virtual_available || 0;
    },

    get value() {
        if (this.pos.res_setting.display_stock == true) {
            const current_product = this.props.productId;
            const move_line = this.pos.move_line;
            const stock_product = this.pos.stock_quant;
            const product_product = this.pos.product_product;

            const configLocationId = this.pos.res_setting?.raw?.stock_location_id?.[0];

            let qty = 0;
            let on_hand = 0;
            let outgoing = 0;
            let incoming = 0;

            const main_product = product_product.find(product => product.id === current_product);
            const product_tmpl_id = main_product?.raw.product_tmpl_id;
            const product_variants = product_product.filter(product => product.raw.product_tmpl_id === product_tmpl_id);

            if (this.stockFrom === 'current_warehouse' && configLocationId) {
                stock_product.forEach((quant) => {
                    if (quant && quant.product_id) {
                        const product_id = quant.product_id.id;
                        const is_variant = product_variants.some(variant => variant.id === product_id);
                        const quant_location_id = quant.raw.location_id?.[0];

                        if ((product_id === current_product || is_variant) && quant_location_id === configLocationId) {
                            qty += quant.available_quantity || 0;
                            on_hand += quant.quantity || 0;
                        }
                    }
                });

                move_line.forEach((line) => {
                    if (line && line.product_id) {
                        const is_variant = product_variants.some(variant => variant.id === line.product_id.id);

                        if (line.product_id.id == current_product || is_variant) {
                            const line_dest_location_id = line.raw.location_dest_id?.[0];
                            const line_location_id = line.raw.location_id?.[0];

                            if (line_dest_location_id === configLocationId) {
                                incoming += line.product_id.incoming_qty || 0;
                            }
                            if (line_location_id === configLocationId) {
                                outgoing += line.product_id.outgoing_qty || 0;
                            }
                        }
                    }
                });
            } else {
                stock_product.forEach((product) => {
                    if (product && product.product_id) {
                        const product_id = product.product_id.id;
                        const is_variant = product_variants.some(variant => variant.id === product_id);

                        if (product_id === current_product || is_variant) {
                            qty += product.available_quantity || 0;
                            on_hand += product.quantity || 0;
                        }
                    }
                });

                move_line.forEach((line) => {
                    if (line && line.product_id && (line.product_id.id == current_product)) {
                        incoming += line.product_id.incoming_qty || 0;
                        outgoing += line.product_id.outgoing_qty || 0;
                    }
                });
            }

            this.props.available = qty;
            this.props.on_hand = on_hand;
            this.props.outgoing = outgoing;
            this.props.incoming_loc = incoming;

            // CRITICAL FIX: Remove the ORM call - use already loaded data
            this.state.display_stock = true;
            // Update state from product instead of fetching
            this.state.qty_available = this.product.qty_available || 0;
            this.state.incoming_qty = this.product.incoming_qty || 0;
            this.state.outgoing_qty = this.product.outgoing_qty || 0;
            this.state.virtual_available = this.product.virtual_available || 0;

            return {
                display_stock: this.pos.res_setting.display_stock,
                show_product_trend: this.showProductTrend,
                stock_trend: this.stockTrend,
                total_sold: this.product.total_sold,
                total_added: this.product.total_added,
            };
        } else {
            return {
                display_stock: false,
                show_product_trend: false,
                stock_trend: 'neutral',
                total_sold: 0,
                total_added: 0,
            };
        }
    },
});