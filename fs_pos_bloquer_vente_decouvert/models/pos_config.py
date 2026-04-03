# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    fs_block_negative_sale = fields.Boolean(
        string="Bloquer la vente à découvert (stock ≤ 0)",
        help="Si activé : les produits dont le stock est à 0 ou négatif seront grisés dans le POS et "
             "l'ajout au panier sera bloqué au-delà du stock disponible.",
        default=True,
    )

    fs_block_negative_message = fields.Char(
        string="Message de blocage",
        help="Message affiché dans le POS lorsqu'un produit ne peut pas être ajouté (stock insuffisant).",
        default="Stock insuffisant : vente à découvert interdite.",
    )

    fs_stock_location_id = fields.Many2one(
        "stock.location",
        string="Emplacement de stock (optionnel)",
        help="Emplacement utilisé pour calculer le stock affiché dans le POS. "
             "Si vide, Odoo utilisera l'emplacement source par défaut du picking type du POS.",
        domain="[('usage', '=', 'internal')]",
    )

    def _loader_params_pos_config(self):
        """
        Assure que nos champs sont envoyés au POS UI (Odoo 18).
        """
        result = super()._loader_params_pos_config()
        fields_list = result.get("search_params", {}).get("fields", [])
        for f in ["fs_block_negative_sale", "fs_block_negative_message", "fs_stock_location_id"]:
            if f not in fields_list:
                fields_list.append(f)
        result["search_params"]["fields"] = fields_list
        return result