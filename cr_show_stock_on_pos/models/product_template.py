# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ProductTemplate(models.Model):
    """inherit product.template to add field."""
    _inherit = "product.template"

    deny = fields.Integer(string="Deny POS Order", default=0,
                          help="Set a limit so that you can deny POS Order")


class ProductProduct(models.Model):
    """inherit product.product to load field in pos."""
    _name = 'product.product'
    _inherit = ['product.product','pos.load.mixin']

    stock_trend = fields.Char(string='Stock Trend', compute='_compute_trend_fields', store=False)
    total_sold = fields.Integer(string='Total Sold', compute='_compute_trend_fields', store=False)
    total_added = fields.Integer(string='Total Added', compute='_compute_trend_fields', store=False)

    @api.depends()
    def _compute_trend_fields(self):
        time_frame = datetime.now() - relativedelta(months=1)
        for product in self:
            total_sold = 0
            total_added = 0
            stock_trend = "neutral"
            recent_orders = self.env["pos.order.line"].search([
                ("product_id", "=", product.id),
                ("order_id.date_order", ">=", time_frame),
            ])
            total_sold = sum(line.qty for line in recent_orders)
            recent_stock_moves = self.env["stock.move"].search([
                ("product_id", "=", product.id),
                ("date", ">=", time_frame),
                ("state", "=", "done"),
            ])
            total_added = sum(move.quantity for move in recent_stock_moves)
            if total_sold > total_added:
                stock_trend = "increasing"
            elif total_added > total_sold:
                stock_trend = "decreasing"
            product.total_sold = total_sold
            product.total_added = total_added
            product.stock_trend = stock_trend

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the fields to be loaded for POS data."""
        result = super()._load_pos_data_fields(config_id)
        result.append('qty_available')
        result.append('incoming_qty')
        result.append('outgoing_qty')
        result.append('deny')
        result.append('stock_trend')
        result.append('total_sold')
        result.append('total_added')
        result.append('virtual_available')
        return result
