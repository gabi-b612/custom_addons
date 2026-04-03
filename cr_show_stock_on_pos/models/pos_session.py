# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import api, models


class PosSession(models.Model):
    """inherit pos.session to add fields and modules in session."""
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """The list of models to be loaded for POS data."""
        data = super()._load_pos_data_models(config_id)
        data += ['res.config.settings','stock.quant','stock.move.line']
        return data

    #############################################

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        if self.config_id.show_product_stock:
            result["search_params"]["fields"].extend(
                ["qty_available", "virtual_available", "type", "total_sold", "total_added", "stock_trend"]
            )
        return result
    def _get_pos_ui_product_product(self, params):
        products = super()._get_pos_ui_product_product(params)
        if self.config_id.show_product_stock:
            picking_type = self.config_id.picking_type_id
            location_id = picking_type.default_location_src_id.id
            time_frame = datetime.now() - relativedelta(months=1)
            for product in products:
                if not product.get("id"):
                    continue
                pp = self.env["product.product"].browse([product.get("id")])
                product_qtys = pp.with_context(location=location_id)._compute_quantities_dict(None, None, None, None, None)
                for pos_product in product_qtys:
                    product["pos_qty_available"] = product_qtys.get(pos_product).get("qty_available", 0)
                    product["pos_forecasted_qty"] = product_qtys.get(pos_product).get("virtual_available", 0)
                total_sold = 0
                total_added = 0
                stock_trend = "neutral"
                if self.config_id.show_product_trend:
                    recent_orders = self.env["pos.order.line"].search([
                        ("product_id", "=", product["id"]),
                        ("order_id.date_order", ">=", time_frame),
                    ])
                    total_sold = sum(line.qty for line in recent_orders)
                    recent_stock_moves = self.env["stock.move"].search([
                        ("product_id", "=", product["id"]),
                        ("date", ">=", time_frame),
                        ("location_dest_id", "=", location_id),
                        ("state", "=", "done"),
                    ])
                    total_added = sum(move.quantity for move in recent_stock_moves)
                    if total_sold > total_added:
                        stock_trend = "increasing"
                    elif total_added > total_sold:
                        stock_trend = "decreasing"
                    else:
                        stock_trend = "neutral"
                product["total_sold"] = total_sold
                product["total_added"] = total_added
                product["stock_trend"] = stock_trend
        return products

    ##########################################################