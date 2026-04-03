# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fs_block_negative_sale = fields.Boolean(
        string="Bloquer la vente à découvert (stock ≤ 0)",
        related="pos_config_id.fs_block_negative_sale",
        readonly=False,
        store=False,
        help="Si activé : les produits dont le stock est à 0 ou négatif seront grisés dans le POS et "
             "l'ajout au panier sera bloqué au-delà du stock disponible.",
    )

    fs_block_negative_message = fields.Char(
        string="Message de blocage",
        related="pos_config_id.fs_block_negative_message",
        readonly=False,
        store=False,
        help="Message affiché dans le POS lorsqu'un produit ne peut pas être ajouté (stock insuffisant).",
    )

    fs_stock_location_id = fields.Many2one(
        "stock.location",
        string="Emplacement de stock (optionnel)",
        related="pos_config_id.fs_stock_location_id",
        readonly=False,
        store=False,
        domain="[('usage', '=', 'internal')]",
        help="Emplacement utilisé pour calculer le stock affiché dans le POS. "
             "Si vide, Odoo utilisera l'emplacement source par défaut du picking type du POS.",
    )