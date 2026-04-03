from odoo import fields, models


class StockWarehouseReportLine(models.Model):
    _name = "stock.warehouse.report.line"
    _description = "Ligne Rapport Stock Entrepôt"
    _order = "product_id asc, id asc"

    report_id = fields.Many2one(
        "stock.warehouse.report",
        string="Rapport",
        required=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        "product.product",
        string="Produit",
        required=True,
        ondelete="restrict",
    )

    qty_available = fields.Float(string="Quantité disponible", digits="Product Unit of Measure")

    status = fields.Selection(
        [
            ("available", "Disponible"),
            ("out", "Rupture"),
            ("negative", "Épuisé"),
        ],
        string="État",
        required=True,
        default="available",
    )