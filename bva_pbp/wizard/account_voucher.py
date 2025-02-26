from odoo import models, fields, api

class VoucherWizard(models.TransientModel):
    _name = "voucher.wizard"
    _description = "Wizard para generar voucher para los vencimientos de cartera"

    name = fields.Char()

    cuenta = fields.Many2one('account.account', string='Cuenta de devengamiento', required=True)
    vencimiento_id = fields.Many2one("pbp.vencimiento_capital_interes", string="Vencimiento")
    partner_id = fields.Many2one('res.partner', string='Emisor', required=True)

    fecha_vencimiento = fields.Date(related="vencimiento_id.fecha_vencimiento")

    total = fields.Float(string="Monto del Vencimiento")
    amount = fields.Float(string="Monto", required=True)
    saldo_actual = fields.Float(string="Saldo Vencimiento", readonly=True)
    saldo = fields.Float()

    @api.onchange("amount")
    def _onchange_amount(self):
        for record in self:
            record.saldo_actual = record.saldo - record.amount

    def action_create_voucher(self):
        self.ensure_one()
        voucher_vals = {
            'name': f"Voucher - {self.order_id.name}",
            'amount': self.amount,
            'order_id': self.order_id.id,
        }
        voucher = self.env['account.payment'].create(voucher_vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': voucher.id,
            'target': 'current',
        }

    def crear_voucher(self):


        lines = []
        lines.append((0, 0,
                      {
                          'name': self.name,
                          'quantity': 1,
                          'price_unit': self.amount,
                          'account_id': self.cuenta.id
                      }
                      )
        )
        print(lines)
        cabecera = {
            'partner_id': self.partner_id.id,
            'date': self.fecha_vencimiento,
            'account_id': self.cuenta.id,
            'line_ids': lines,
            'voucher_type': 'sale',
            'name': self.name,
            'vencimiento_id': self.vencimiento_id.id

        }
        print(cabecera)
        voucher = self.env["account.voucher"].create(cabecera)
        print("Se creo el voucher", voucher.id)
        # self.voucher_id = voucher
        # self.state = 'cobrado'
        # validar los voucher del vencimiento para cambiar su estado
        total_cobrado = 0
        vencimiento_monto = self.vencimiento_id.total
        for vouch in self.vencimiento_id.vouchers_ids:
            total_cobrado += vouch.amount

        if total_cobrado >= vencimiento_monto:
            print("Total:",total_cobrado,"Monto Vencimiento",vencimiento_monto)
            self.vencimiento_id.state = 'cobrado'
        return True
