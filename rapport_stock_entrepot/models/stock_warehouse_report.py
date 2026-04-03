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

    email_subject = fields.Char(string="Sujet email")
    email_body = fields.Html(string="Message", sanitize=True)

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "stock_wh_report_attachment_rel",
        "report_id",
        "attachment_id",
        string="Pièces jointes (optionnel)",
    )

    last_sent_date = fields.Date(string="Dernière date d'envoi", readonly=True)

    # ─────────────────────────────────────────────
    # ACTION PDF
    # ─────────────────────────────────────────────
    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref("rapport_stock_entrepot.action_stock_report_pdf").report_action(self)

    # ─────────────────────────────────────────────
    # ACTION ENVOI MANUEL
    # ─────────────────────────────────────────────
    def action_send_email_now(self):
        self.ensure_one()

        try:
            self._send_report_email(mark_sent_today=False, source="MANUEL")

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Envoi email"),
                    "message": _("Email envoyé avec succès à : %s") % (self.email_to or ""),
                    "type": "success",
                    "sticky": False,
                },
            }

        except Exception as e:
            self._log_send("ERROR", "MANUEL", str(e))
            raise UserError(_("Échec d'envoi email : %s") % str(e))

    # ─────────────────────────────────────────────
    # OUTILS EMAIL
    # ─────────────────────────────────────────────
    def _parse_recipients(self):
        self.ensure_one()

        if not self.email_to:
            raise UserError(_("Veuillez renseigner au moins une adresse email."))

        emails = [e.strip() for e in self.email_to.split(",") if e.strip()]
        if not emails:
            raise UserError(_("Veuillez renseigner au moins une adresse email."))

        invalid = [e for e in emails if not EMAIL_RE.match(e)]
        if invalid:
            raise UserError(_("Emails invalides: %s") % ", ".join(invalid))

        return ",".join(emails)

    def _render_report_pdf_attachment(self):
        """Odoo 18 compatible"""
        self.ensure_one()

        report_action = self.env.ref("rapport_stock_entrepot.action_stock_report_pdf")
        report_ref = report_action.report_name

        pdf_content, _ = report_action._render_qweb_pdf(report_ref, res_ids=[self.id])

        if not pdf_content:
            raise UserError(_("Impossible de générer le PDF."))

        filename = "%s_%s.pdf" % (
            self.name or "Rapport_Stock",
            fields.Date.to_string(fields.Date.context_today(self)),
        )

        return self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "mimetype": "application/pdf",
            "res_model": self._name,
            "res_id": self.id,
        })

    # ─────────────────────────────────────────────
    # LOGGING CENTRALISÉ
    # ─────────────────────────────────────────────
    def _log_send(self, level, source, message):
        self.ensure_one()

        # chatter visible
        try:
            self.message_post(
                body=_("<b>[%s]</b> %s") % (source, message),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
        except Exception:
            pass

        # log serveur
        try:
            self.env["ir.logging"].create({
                "name": "rapport_stock_entrepot",
                "type": "server",
                "level": level,
                "dbname": self.env.cr.dbname,
                "message": "[%s] %s (report_id=%s)" % (source, message, self.id),
                "path": "stock.warehouse.report",
                "func": "_send_report_email",
                "line": "0",
            })
        except Exception:
            pass

    # ─────────────────────────────────────────────
    # ENVOI EMAIL
    # ─────────────────────────────────────────────
    def _send_report_email(self, mark_sent_today=True, source="CRON"):
        self.ensure_one()

        if not self.warehouse_id:
            raise UserError(_("Aucun entrepôt défini."))

        email_to = self._parse_recipients()

        subject = self.email_subject or _("Rapport de stock — %s") % self.warehouse_id.display_name

        body = self.email_body or _(
            "<p>Bonjour,</p>"
            "<p>Veuillez trouver ci-joint le rapport de stock de l'entrepôt "
            "<strong>%s</strong>.</p>"
        ) % self.warehouse_id.display_name

        pdf_att = self._render_report_pdf_attachment()
        all_atts = pdf_att | self.attachment_ids

        mail = self.env["mail.mail"].create({
            "subject": subject,
            "body_html": body,
            "email_to": email_to,
            "attachment_ids": [(6, 0, all_atts.ids)],
        })

        mail.send()

        if mark_sent_today:
            self.last_sent_date = fields.Date.context_today(self)

        self._log_send("INFO", source, "Email envoyé à : %s" % email_to)

    # ─────────────────────────────────────────────
    # CRON
    # ─────────────────────────────────────────────
    @api.model
    def _cron_send_scheduled_reports(self):
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)

        reports = self.search([("schedule_enabled", "=", True)])

        for r in reports:

            if r.last_sent_date == today:
                continue

            if now.hour > r.schedule_hour or (
                now.hour == r.schedule_hour and now.minute >= r.schedule_minute
            ):
                try:
                    r._send_report_email(mark_sent_today=True, source="CRON")
                except Exception as e:
                    r._log_send("ERROR", "CRON", str(e))
