# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherit the base settings to add field. """
    _name = 'res.config.settings'
    _inherit = ['res.config.settings', 'pos.load.mixin']

    ######################################
    show_product_stock = fields.Boolean(
        string="Show Product Stock",
        config_parameter="point_of_sale.show_product_stock",
        help="Enable to display product stock information in the POS interface.",
    )
    stock_display_type = fields.Selection(
        selection=[
            ("on_hand", "On-Hand Quantity"),
            ("forecasted", "Forecasted Quantity"),
        ],
        string="Stock Display Type",
        default="on_hand",
        config_parameter="cr_show_stock_on_pos.stock_display_type",
        help="Choose whether to display On-Hand Quantity or Forecasted Quantity in the POS.",
    )
    show_negative_qty_products = fields.Boolean(
        string="Show Negative Quantity Products",
        # config_parameter="cr_show_stock_on_pos.show_negative_qty_products",
        help="Enable to display products with negative quantities in the POS interface.",
        related='pos_config_id.show_negative_qty_products',
        store=True,
        readonly=False,
    )
    disable_negative_qty_product = fields.Boolean(
        string="Disable Negative Quantity Products",
        # config_parameter="cr_show_stock_on_pos.disable_negative_qty_product",
        help="Enable to disable products with negative quantities from being selected in the POS.",
        related='pos_config_id.disable_negative_qty_product',
        store=True,
        readonly=False,
    )
    allow_negative_products_to_order = fields.Boolean(
        string="Allow Negative Products to Order",
        # config_parameter="cr_show_stock_on_pos.allow_negative_products_to_order",
        help="Enable to allow adding products with negative quantities to the order in the POS.",
        related='pos_config_id.allow_negative_products_to_order',
        store=True,
        readonly=False,
    )

    threshold_qty = fields.Integer(
        string="Threshold Quantity",
        # config_parameter="cr_show_stock_on_pos.threshold_qty",
        related='pos_config_id.threshold_qty',
        store=True,
        readonly=False,
        help="Set the minimum stock quantity below which a warning will be shown in the POS.",
    )
    threshold_message = fields.Char(
        string="Threshold Warning Message",
        # config_parameter="cr_show_stock_on_pos.threshold_message",
        related='pos_config_id.threshold_message',
        store=True,
        readonly=False,
        help="Custom message to display when a product's stock is below the threshold quantity.",
    )

    ########################
    display_stock = fields.Boolean(string="Display Stock",
                                   readonly=False, help="By enabling you can "
                                                        "view quantity in Point Of Sale",
                                   default=False, config_parameter='cr_show_stock_on_pos.display_stock')
    stock_type = fields.Selection(related='pos_config_id.stock_product',
                                  string="Stock Type", readonly=False,
                                  required=True, help="Help you to choose "
                                                      "the quantity you want to visible in pos")
    stock_from = fields.Selection(related='pos_config_id.location_from',
                                  string="Show Stock Of", readonly=False,
                                  required=True, help="can choose the location "
                                                      "where you want to display the stock ")
    stock_location_id = fields.Many2one(related='pos_config_id.pos_stock_location_id',
                                        string="Stock Location", readonly=False,
                                        help="This field helps to hold the location")
    show_product_trend = fields.Boolean(
        string="Show Product Trend",
        # config_parameter="point_of_sale.show_product_trend",
        related='pos_config_id.show_product_trend',
        readonly=False,
        store=True,
        help="Enable to display a trend indicator for product stock based on sales and stock movements from the last month.",
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the list of fields to be loaded for POS data."""
        result = super()._load_pos_data_fields(config_id)
        result.append('display_stock')
        result.append('stock_type')
        result.append('stock_from')
        result.append('stock_location_id')
        result.append('show_product_trend')
        result.append('show_product_stock')
        result.append('stock_display_type')
        result.append('show_negative_qty_products')
        result.append('disable_negative_qty_product')
        result.append('allow_negative_products_to_order')
        result.append('threshold_qty')
        result.append('threshold_message')
        return result
