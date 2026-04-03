# -*- coding: utf-8 -*-
{
    "name": "POS — Bloquer la vente à découvert (Stock ≤ 0)",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Empêche la vente des produits dont le stock est à 0 ou négatif dans le POS.",
    "description": """
Bloque la vente à découvert dans le Point de Vente (Odoo 18).

Fonctionnement :
- Si le stock du produit est ≤ 0 : le produit est grisé et non cliquable.
- Si le stock est faible : le POS bloque l'ajout au panier au-delà du stock disponible.
- Le stock affiché se met à jour en live en tenant compte du panier.

Paramètres (simples) :
- Activer le blocage (oui/non)
- Message d’avertissement
- Emplacement de stock (optionnel). Si vide, on utilise l’emplacement source du picking POS.
""",
    "author": "Fabrice Sangwa",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "stock", "account"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "fs_pos_bloquer_vente_decouvert/static/src/js/pos_block_negative.js",
            "fs_pos_bloquer_vente_decouvert/static/src/xml/product_card_ext.xml",
            "fs_pos_bloquer_vente_decouvert/static/src/css/pos_block_negative.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
