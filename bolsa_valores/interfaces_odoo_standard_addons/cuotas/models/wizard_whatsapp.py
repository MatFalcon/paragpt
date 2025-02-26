
from odoo import api, fields, models, exceptions


class WizardWhatsapp(models.TransientModel):
    _name = 'cuotas.wizard.whatsapp'
    _description = 'Mensaje de Whatsapp'

    cuota_id = fields.Many2one('cuotas.cuota', string="Cuota")
    text = fields.Text(string="Texto")

   
    def default_texto(self):
        texto = "%s, lo contactamos desde la Universidad Comunera para recordarle que su cuota correspondiente a %s tiene como fecha de vencimiento %s.<br/> Muchas gracias." % (
            self.cuota_id.partner_id.name, self.cuota_id.product_id.name, self.cuota_id.fecha_vencimiento.strftime('%d/%m/%Y'))

    def button_enviar_mensaje(self):
        record=self.env[self.cuota_id._name].browse(self.cuota_id.id)
        record.message_post(body='<strong>Mensaje de whatsapp enviado</strong> %s <strong>enviado por %s </strong>'%(self.text,self.env.user.name))
        
        return{
                    'type': 'ir.actions.act_url',
                    'url': "https://web.whatsapp.com/send?l=&phone=" + self.cuota_id.partner_id.mobile + "&text=%s"%self.text.replace('*', '').replace('_', '').replace('%0A', '<br/>').replace(
                        '%20', ' ').replace('%26', '&'),
                    'target': 'new',
                    'res_id': self.id,
                }