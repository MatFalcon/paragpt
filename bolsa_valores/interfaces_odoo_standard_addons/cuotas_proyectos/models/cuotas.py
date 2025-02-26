from email.policy import default
from odoo import models,fields,api,exceptions
from datetime import date,datetime

class Cuotas(models.Model):
    _inherit = 'cuotas.cuota'


    project_id=fields.Many2one('project.project',string="Proyecto")
    milestone_id=fields.Many2one('project.milestone',string="Hito")
    tipo_facturacion=fields.Selection(string="Tipo de facturación",selection=[('fecha','Por fecha de facturación'),('hito','Por hito')],default='fecha')
    facturable=fields.Boolean(string="Facturable",compute="compute_facturable",store=True)
    order_id=fields.Many2one('sale.order',string="Pedido de venta")

    @api.depends('milestone_id','tipo_facturacion','fecha_vencimiento')
    def compute_facturable(self):
        for i in self:
            facturable=False
            if i.tipo_facturacion=='hito':
                if i.milestone_id and i.milestone_id.is_reached:
                    facturable=True
            elif i.tipo_facturacion=='fecha':
                if i.fecha_facturacion and i.fecha_facturacion<=date.today():
                    facturable=True
            i.facturable=facturable

    def enviar_correo_facturable(self,cuota):
        users=self.env['ir.config_parameter'].get_param('facturable_recipients_param')
        if users:
            users=users.split(',')
        for user in users:
            if cuota:
                vals = {
                    'subject': 'Aviso de cuota facturable: %s - %s'%(cuota.name,cuota.partner_id.name),
                    'body_html': '<p>La cuota %s del cliente %s está lista para ser facturada :</p><p>https://www.interfaces.com.py/web#id=%s&cids=1&model=cuotas.cuota&view_type=form</p>'%(cuota.name,cuota.partner_id.name,cuota.id),
                    'email_to': user,
                    'auto_delete': False,
                    'email_from': 'info@interfaces.com.py',
                }

                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()
        return


    def write(self,vals):
        res=super(Cuotas,self).write(vals)
        for i in self:
            if vals.get('facturable') and vals.get('facturable')==True and not i.facturable:
                self.enviar_correo_facturable(i)
        return res

