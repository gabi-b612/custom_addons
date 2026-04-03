from odoo import models, fields, _
from odoo.exceptions import UserError


class ReportStockWarehouse(models.AbstractModel):
    _name = "report.rapport_stock_entrepot.stock_report_pdf"
    _description = "Rapport Stock Entrepôt - PDF"

    def _prepare_lines_for_warehouse(self, warehouse):
        """Retourne les lignes de stock pour l'entrepôt (produit, quantité, statut)."""
        if not warehouse or not warehouse.lot_stock_id:
            return []

        Quant = self.env["stock.quant"].sudo()
        quants = Quant.search([("location_id", "child_of", warehouse.lot_stock_id.id)])

        data = {}
        for q in quants:
            p = q.product_id
            if not p:
                continue

            qty = q.quantity or 0.0
            rec = data.get(p.id)
            if not rec:
                data[p.id] = {"product": p, "qty": qty}
            else:
                rec["qty"] += qty

        lines = list(data.values())

        # Tri par nom
        lines = sorted(lines, key=lambda x: (x["product"].display_name or "").lower())

        # Ajout statut
        for l in lines:
            qty = l["qty"]
            if qty < 0:
                status = _("Négatif")
            elif qty == 0:
                status = _("Rupture")
            else:
                status = _("Disponible")
            l["status"] = status

        return lines

    def _get_report_values(self, docids, data=None):
        reports = self.env["stock.warehouse.report"].browse(docids).exists()
        if not reports:
            raise UserError(_("Aucun rapport à imprimer."))

        report = reports[0]

        if not report.warehouse_id:
            raise UserError(_("Aucun entrepôt n'est défini sur ce rapport."))

        # Date du rapport (champ modèle)
        dt = report.date_report or fields.Datetime.now()
        dt_local = fields.Datetime.context_timestamp(self, dt)
        report_datetime_str = fields.Datetime.to_string(dt_local)

        # Date/heure impression
        print_dt = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        print_datetime_str = fields.Datetime.to_string(print_dt)

        lines = self._prepare_lines_for_warehouse(report.warehouse_id)
        if not lines:
            # On autorise un PDF vide, mais tu peux bloquer si tu veux
            # raise UserError(_("Aucun stock trouvé pour cet entrepôt."))
            lines = []

        return {
            "doc_ids": reports.ids,
            "doc_model": "stock.warehouse.report",
            "docs": reports,

            "report_title": _("Rapport de Stock par Entrepôt"),
            "warehouse_name": report.warehouse_id.display_name,

            "report_datetime": report_datetime_str,
            "print_datetime": print_datetime_str,
            "printed_by": self.env.user.name,

            "lines": lines,
        }