from odoo import models, fields, api , _
from odoo.exceptions import ValidationError
class InvoiceTermsConditionsWizard(models.TransientModel):
    _name = 'invoice.terms.conditions.wizard'
    _description = 'Assign conditions wizard'

    sale_invoice_term_id = fields.Many2one('sale.invoice.terms', string="Invoice Term")
    name = fields.Char(string='Name')
    user_id = fields.Many2one('res.users', string="Responsible",tracking=True)
    date_deadline = fields.Date(string='Date deadline',tracking=True)
    condition_activity_type_id = fields.Many2one('mail.activity.type',string="Activity type",tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade', index=True)

    def action_save(self):
        self.ensure_one()
        # Aquí crearías el nuevo término de condiciones de la factura
        condition = self.env['sale.invoice.terms.conditions'].create({
            'sale_invoice_term_id': self.sale_invoice_term_id.id,
            'condition_activity_type_id': self.condition_activity_type_id.id,
            'date_deadline': self.date_deadline,
            'user_id': self.user_id.id,
            'name': self.name,
            'sale_order_id': self.sale_invoice_term_id.sale_order_id.id
        })

        # Aquí crearías la actividad asociada a la condición de factura
        self.env['mail.activity'].create({
            'res_id': condition.id,
            'res_model_id': self.env['ir.model']._get('sale.invoice.terms.conditions').id,
            'activity_type_id': self.condition_activity_type_id.id,
            'summary': f"Actividad de {self.name}",
            'date_deadline': self.date_deadline,
            'user_id': self.user_id.id,
        })

        # Enviar un correo electrónico al usuario notificándole sobre la nueva actividad
        mail_content = f"<p>Hola, {self.user_id.name}.</p><p>Se te ha asignado una nueva actividad con el nombre {self.name}.</p>"
        mail = self.env['mail.mail'].create({
            'subject': 'Nueva actividad asignada',
            'body_html': mail_content,
            'email_to': self.user_id.email,
            'auto_delete': True,
        })
        mail.send()

        # Registrar el mensaje en el chatter
        condition.message_post(body=mail_content, message_type='notification')

        return {'type': 'ir.actions.act_window_close'}
