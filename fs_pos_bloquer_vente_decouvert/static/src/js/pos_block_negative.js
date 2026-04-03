/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { Order } from "@point_of_sale/app/store/models";

/**
 * =========================
 * Utils stock
 * =========================
 */

function getBackendStockQty(product) {
    return Number(product?.qty_available || 0);
}

function getCartQtyForProduct(pos, product) {
    const order = pos.get_order();
    if (!order) return 0;

    let qty = 0;
    for (const line of order.get_orderlines()) {
        if (line.product_id?.id === product.id) {
            qty += Number(line.get_quantity() || 0);
        }
    }
    return qty;
}

function getAvailableQty(pos, product) {
    return getBackendStockQty(product) - getCartQtyForProduct(pos, product);
}

function isBlockingEnabled(pos) {
    return Boolean(pos.config?.fs_block_negative_sale);
}

function getBlockMessage(pos) {
    return pos.config?.fs_block_negative_message || _t("Stock insuffisant : vente à découvert interdite.");
}

function shouldIgnoreProduct(product) {
    // On laisse vendre les services
    return product?.type === "service";
}

/**
 * Met à jour les champs runtime sur un produit (utilisés dans le XML)
 */
function refreshProductRuntimeFields(pos, product) {
    if (!product) return;

    const enabled = isBlockingEnabled(pos);
    const available = enabled && !shouldIgnoreProduct(product) ? getAvailableQty(pos, product) : null;

    product.fs_show_stock_badge = enabled && !shouldIgnoreProduct(product);
    product.fs_available_qty = enabled && !shouldIgnoreProduct(product) ? available : null;
    product.fs_blocked = enabled && !shouldIgnoreProduct(product) ? (available <= 0) : false;
}

/**
 * Rafraîchir tous les produits visibles dans le POS (DB)
 */
function refreshAllProductsRuntimeFields(pos) {
    if (!pos?.db?.product_by_id) return;

    for (const idStr of Object.keys(pos.db.product_by_id)) {
        const product = pos.db.product_by_id[idStr];
        refreshProductRuntimeFields(pos, product);
    }
}

/**
 * =========================
 * 1) Patch ProductScreen : blocage ajout au panier
 * =========================
 */
patch(ProductScreen.prototype, {
    async addProductToOrder(product, options = {}) {
        if (!isBlockingEnabled(this.pos) || shouldIgnoreProduct(product)) {
            const res = await super.addProductToOrder(product, options);
            refreshProductRuntimeFields(this.pos, product);
            return res;
        }

        const available = getAvailableQty(this.pos, product);
        const message = getBlockMessage(this.pos);

        if (available <= 0) {
            await this.dialog.add(AlertDialog, {
                title: _t("Vente bloquée"),
                body: _t(`${message}\n\nProduit : ${product.display_name}\nStock disponible : ${available}`),
            });
            // Rafraîchir visuel
            refreshProductRuntimeFields(this.pos, product);
            return;
        }

        const requestedQty = Number(options?.quantity || 1);
        if (requestedQty > available) {
            await this.dialog.add(AlertDialog, {
                title: _t("Stock insuffisant"),
                body: _t(
                    `${message}\n\nProduit : ${product.display_name}\n` +
                    `Stock disponible : ${available}\n` +
                    `Quantité demandée : ${requestedQty}`
                ),
            });
            refreshProductRuntimeFields(this.pos, product);
            return;
        }

        const res = await super.addProductToOrder(product, options);

        // Après ajout → recalcul live pour que la grille se mette à jour
        refreshAllProductsRuntimeFields(this.pos);
        return res;
    },
});

/**
 * =========================
 * 2) Patch Order : dès que le panier change, on recalcule
 * =========================
 * Ça règle ton problème principal : stock affiché qui reste figé.
 */
patch(Order.prototype, {
    add_product(product, options) {
        const res = super.add_product(product, options);
        refreshAllProductsRuntimeFields(this.pos);
        return res;
    },
    removeOrderline(line) {
        const res = super.removeOrderline(line);
        refreshAllProductsRuntimeFields(this.pos);
        return res;
    },
});

/**
 * =========================
 * 3) Patch ProductCard : avant rendu, on injecte le runtime
 * =========================
 * Permet au XML d’utiliser props.product.fs_blocked, fs_available_qty...
 */
patch(ProductCard.prototype, {
    setup() {
        super.setup();
        // Le product est accessible via props.product dans Odoo 18
        const product = this.props?.product;
        refreshProductRuntimeFields(this.pos, product);
    },
});

/**
 * Export au besoin
 */
export const FsPosStockUtils = {
    getBackendStockQty,
    getCartQtyForProduct,
    getAvailableQty,
    refreshProductRuntimeFields,
    refreshAllProductsRuntimeFields,
};