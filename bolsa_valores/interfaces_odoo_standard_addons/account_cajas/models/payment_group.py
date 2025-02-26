from odoo import fields, api, models, exceptions


class PaymentGroup(models.Model):
    _inherit = 'grupo_account_payment.payment.group'

    caja_session_id = fields.Many2one(
        'account.caja.session', string="Sesión de caja")

    def get_sesion(self):
        if self and self.caja_session_id:
            sesion = self.caja_session_id
        else:
            sesion = self.env['account.caja.session'].search(
                [('company_id', '=', self.company_id.id or self.env.user.company_id.id), ('user_id', '=', self.env.user.id), ('state', '=', 'proceso')])
        return sesion

    def button_confirmar(self):
        for i in self:
            if i.payment_type == 'inbound':
                for j in i.payment_ids:
                    caja = i.get_sesion().caja_id
                    if j.journal_id.id not in caja.journal_ids.ids:
                        raise exceptions.ValidationError(
                            'No se puede crear una linea de pago en el diario %s, el mismo no está habilitado para ésta caja.' % j.journal_id.name)

                super(PaymentGroup, i).button_confirmar()
                for j in i.payment_ids:
                    sesion = i.get_sesion()
                    for s in sesion.statement_ids.filtered(lambda x: x.journal_id == j.journal_id):
                        monto = j.amount
                        if i.payment_type == 'outbound':
                            monto = monto*-1
                        s.write(
                            {'line_ids': [(0, 0, {'journal_entry_ids': [(6, 0, j.move_line_ids.filtered(lambda z:z.debit > 0).ids)], 'date': fields.Date.today(), 'name': i.name, 'partner_id':i.partner_id.id, 'amount':monto, 'payment_id':j.id})]})
            else:
                super(PaymentGroup, i).button_confirmar()

    def button_cancelar(self):
        for i in self:
            if i.payment_type == 'inbound':
                #if i.caja_session_id and i.caja_session_id.state in ['proceso', 'cierre']:
                if 1==1:
                    super(PaymentGroup, i).button_cancelar()
                    for payment in i.payment_ids:
                        for st in i.caja_session_id.statement_ids:
                            lines = st.line_ids.filtered(
                                lambda l: l.payment_id == payment)
                            if lines:
                                lines.unlink()
                                if i.caja_session_id.state == 'cierre' and st.journal_id.type == 'bank':
                                    st.write(
                                        {'balance_end_real': st.balance_end_real-payment.amount})
                    return
                else:
                    raise exceptions.ValidationError(
                        'Sólo se puede cancelar un recibo si su sesión de caja está abierta o en proceso de cierre.')
            else:
                super(PaymentGroup, i).button_cancelar()
    @api.model
    def create(self, vals):
        if vals.get('payment_type') == 'inbound':
            session = self.get_sesion()
            if session:
                vals['caja_session_id'] = session.id
            else:
                raise exceptions.ValidationError(
                    'No existe ninguna sesión de caja abierta para el usuario %s. Antes debe abrir una.' % (self.env.user.name))
        return super(PaymentGroup, self).create(vals)
