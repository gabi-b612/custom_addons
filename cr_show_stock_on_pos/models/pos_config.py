# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import  api, fields, models


class PosConfig(models.Model):
    """inherit pos.config to add fields."""
    _inherit = 'pos.config'

    pos_stock_location_id = fields.Many2one('stock.location', string='Stock Location',
                                         help="This field helps to hold the location")
    location_from = fields.Selection([('all_warehouse', 'All Location'),
                                      ('current_warehouse', 'Current Location')],
                                     string="Show Stock Of",
                                     help="can choose the location where you want to display the stock ")
    display_stock_setting = fields.Boolean(string="Display Stock",
                                           help="By enabling you can view quantity in Point Of Sale",
                                           store=True,)
    stock_product = fields.Selection([('on_hand', 'On Hand Quantity'),
                                      ('incoming_qty', 'Incoming Quantity'),
                                      ('outgoing_qty', 'Outgoing Quantity'),("forecasted", "Forecasted Quantity"),],
                                     string="Stock Type",
                                     help="Help you to choose the quantity you want to visible in pos")

    @api.onchange('location_from')
    def _onchange_location_from(self):
        """ Adjust the stock_location_id when stock_from is changed. """
        if self.location_from == 'all_warehouse':
            self.stock_location_id = False
        elif self.location_from == 'current_warehouse':
            self.stock_location_id = self.pos_config_id.pos_stock_location_id


    ###############################################################

    show_product_stock = fields.Boolean(
        string="Show Product Stock",
        default=False,
        store=True,
    )

    stock_display_type = fields.Selection(
        selection=[
            ("on_hand", "On-Hand Quantity"),
            ("forecasted", "Forecasted Quantity"),
        ],
        string="Stock Display Type",
        default="on_hand",
        store=True,
    )

    show_negative_qty_products = fields.Boolean(
        string="Show Negative Quantity Products",
        store=True,
    )

    disable_negative_qty_product = fields.Boolean(
        string="Disable Negative Quantity Products",
    )

    allow_negative_products_to_order = fields.Boolean(
        string="Allow Negative Products to Order",
        store=True,
    )

    show_product_trend = fields.Boolean(
        string="Show Product Trend",
        store=True,
    )

    threshold_qty = fields.Integer(
        string="Threshold Quantity",
        default=-1000,
        store=True,
    )
    threshold_message = fields.Char(
        string="Threshold Warning Message",
        store=True,
    )


    def _loader_params_pos_config(self):
        result = super()._loader_params_pos_config()
        result["search_params"]["fields"].extend(
            [
                "show_product_stock",
                "stock_display_type",
                "show_negative_qty_products",
                "disable_negative_qty_product",
                "allow_negative_products_to_order",
                "show_product_trend",
                "threshold_qty",
                "threshold_message",
            ]
        )
        return result

    ####################################################
