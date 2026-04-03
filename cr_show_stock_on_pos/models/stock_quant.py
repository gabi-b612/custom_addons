# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import  api, models


class StockQuant(models.Model):
    """Inherits model "stock.quant to load pos data"""
    _name = 'stock.quant'
    _inherit = ['stock.quant','pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the list of fields to be loaded for POS data."""
        return [
            'product_id', 'available_quantity', 'quantity', 'location_id','reserved_quantity'
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        """Constructs the domain for loading POS data based on the POS configuration."""
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        if config_id.location_from == 'all_warehouse':
            location_ids = self.env['stock.location'].search([])
            domain = [('location_id', 'in', location_ids.ids)]
        else:
            location_id = config_id.pos_stock_location_id
            domain = ['|', ('location_id', '=', location_id.id), ('location_id', 'in', location_id.child_ids.ids)]
        return domain
