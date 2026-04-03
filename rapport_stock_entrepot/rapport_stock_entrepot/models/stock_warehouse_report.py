# ./rapport_stock_entrepot/models/stock_warehouse_report.py
import base64
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StockWarehouseReport(models.Model):
    _name = "stock.warehouse.report"
    _description = "Rapport Stock par Entrepôt"
    _order = "date_report desc, id desc"

    name = fields.Char(string="Référence", required=True, default="Nouveau")
    warehouse_id = fields.Many2one("stock.warehouse", string="Entrepôt", required=True)

    # Date du rapport (affichée dans la liste + utilisée pour PDF)
    date_report = fields.Datetime(
        string="Date du rapport",
        default=lambda self: fields.Datetime.now(),
        required=True,
        readonly=True,
    )

    # ─────────────────────────────────────────────
    # PLANIFICATION EMAIL
    # ─────────────────────────────────────────────
    schedule_enabled = fields.Boolean(string="Envoi automatique activé", default=False)

    schedule_hour = fields.Integer(string="Heure", default=1)
    schedule_minute = fields.Integer(string="Minute", default=0)

    email_to = fields.Char(
        string="Destinataires (emails)",
        help="Sépare les emails par virgule. Exemple: a@x.com, b@y.com",
    )
    email_subject = fields.Char(string="Sujet email", default=False)
    email_body = fields.Html(string="Message", sanitize=True)

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "stock_wh_report_attachment_rel",
        "report_id",
        "attachment_id",
        string="Pièces jointes (optionnel)",
        help="Pièces jointes ajoutées en plus du PDF du rapport.",
    )

    last_sent_date = fields.Date(string="Dernière date d'envoi", readonly=True)

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────
    def action_print_pdf(self):
        """Bouton : imprime le PDF via ir.actions.report."""
        self.ensure_one()
        return self.env.ref("rapport_stock_entrepot.action_stock_report_pdf").report_action(self)

    def action_send_email_now(self):
        """Bouton : envoi immédiat (manuel)."""
        self.ensure_one()
        self._send_report_email(mark_sent_today=False)
        return True

    # ─────────────────────────────────────────────
    # OUTILS
    # ─────────────────────────────────────────────
    def _parse_recipients(self):
        self.ensure_one()
        if not self.email_to:
            raise UserError(_("Veuillez renseigner au moins une adresse email destinataire."))

        emails = [e.strip() for e in self.email_to.split(",") if e.strip()]
        if not emails:
            raise UserError(_("Veuillez renseigner au moins une adresse email destinataire."))

        invalid = [e for e in emails if not EMAIL_RE.match(e)]
        if invalid:
            raise UserError(_("Emails invalides: %s") % ", ".join(invalid))

        return ",".join(emails)

    def _render_report_pdf_attachment(self):
        """Génère le PDF actuel du rapport et retourne un ir.attachment."""
        self.ensure_one()

        report_action = self.env.ref("rapport_stock_entrepot.action_stock_report_pdf")

        # Odoo 18: rendu PDF
        pdf_content, _content_type = report_action._render_qweb_pdf([self.id])
        if not pdf_content:
            raise UserError(_("Impossible de générer le PDF du rapport."))

        filename = "%s_%s.pdf" % (
            (self.name or "Rapport_Stock"),
            fields.Date.to_string(fields.Date.context_today(self)),
        )

        att = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "mimetype": "application/pdf",
            "res_model": self._name,
            "res_id": self.id,
        })
        return att

    def _send_report_email(self, mark_sent_today=True):
        """Envoie le mail + PDF + pièces jointes optionnelles."""
        self.ensure_one()

        if not self.warehouse_id:
            raise UserError(_("Aucun entrepôt défini sur ce rapport."))

        email_to = self._parse_recipients()

        subject = self.email_subject or _("Rapport de stock — %s") % (self.warehouse_id.display_name,)
        body = self.email_body or _(
            "<p>Bonjour,</p><p>Veuillez trouver ci-joint le rapport de stock de l'entrepôt <strong>%s</strong>.</p>"
        ) % (self.warehouse_id.display_name,)

        pdf_att = self._render_report_pdf_attachment()

        extra_atts = self.attachment_ids
        all_atts = (pdf_att | extra_atts)

        # Utilisation de mail.mail (simple et fiable)
        mail = self.env["mail.mail"].create({
            "subject": subject,
            "body_html": body,
            "email_to": email_to,
            "attachment_ids": [(6, 0, all_atts.ids)],
        })
        mail.send()

        if mark_sent_today:
            self.last_sent_date = fields.Date.context_today(self)

    # ─────────────────────────────────────────────
    # CRON
    # ─────────────────────────────────────────────
    @api.model
    def _cron_send_scheduled_reports(self):
        """Cron: tourne toutes les minutes, envoie les rapports quand l'heure est atteinte."""
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)

        reports = self.search([("schedule_enabled", "=", True)])
        for r in reports:
            # éviter doublon dans la même journée
            if r.last_sent_date == today:
                continue

            # Validation simple
            if r.schedule_hour is None or r.schedule_minute is None:
                continue

            # Heure/minute atteinte (aujourd'hui)
            # On compare avec l'heure serveur Odoo.
            if now.hour > r.schedule_hour or (now.hour == r.schedule_hour and now.minute >= r.schedule_minute):
                try:
                    r._send_report_email(mark_sent_today=True)
                except Exception:
                    # On ne casse pas le cron: on log dans les logs Odoo
                    # (tu peux aussi créer un champ "last_error" si tu veux)
                    _logger = self.env["ir.logging"]
                    _logger.create({
                        "name": "rapport_stock_entrepot",
                        "type": "server",
                        "level": "ERROR",
                        "dbname": self.env.cr.dbname,
                        "message": "Erreur envoi auto rapport %s (ID %s)" % (r.display_name, r.id),
                        "path": "stock.warehouse.report",
                        "func": "_cron_send_scheduled_reports",
                        "line": "0",
                    })
