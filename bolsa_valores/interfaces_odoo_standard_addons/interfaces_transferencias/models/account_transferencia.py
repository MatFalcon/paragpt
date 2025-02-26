from odoo import fields, api, models, exceptions


class Transferencias(models.Model):
    _name = 'account.transferencia'
    _description = 'Transferencia'
    _order = 'id desc'
    _sql_constraints = [('unique_deposito', 'unique(nro_boleta_deposito,journal_id)',
                         'Ya existe una boleta de depósito con éste número para éste diario')]

    name = fields.Char(string="Name", default="Borrador",
                       readonly=True, copy=False)
    fecha = fields.Date(
        string="Fecha", default=fields.Date.today(), required=True, copy=False)
    journal_id = fields.Many2one('account.journal', string="Diario de destino", required=True, domain=[
        ('type', 'in', ['bank', 'cash'])])
    journal_source_id = fields.Many2one('account.journal', string="Diario de origen", domain=[
        ('type', 'in', ['bank', 'cash']), ('es_diario_tesoreria', '=', True)], required=True)
    memo = fields.Char(string="Memo")
    nro_boleta_deposito = fields.Char(string="Nro. de boleta")
    state = fields.Selection(string="Estado", selection=[(
        'draft', 'Borrador'), ('done', 'Confirmado'), ('cancel', 'Cancelado')], default="draft")
    move_id = fields.Many2one('account.move', string="Asiento contable")
    user_id = fields.Many2one(
        'res.users', string='Usuario', default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Compañia', default=lambda self: self.env.user.company_id)
    payment_ids = fields.One2many(
        'account.payment', 'transferencia_id', string="Cheques")
    temp_payment_ids = fields.Many2many('account.payment', string="Pagos a transferir", domain=[
        ('payment_type', '=', 'inbound')])
    total_transferencia = fields.Float(
        string="Total", compute="compute_totales")
    transfer_ids = fields.Many2many('account.payment', 'parent_transfer_id', string="Transferencias internas")

    def borrar_lineas(self):
        for transferencia in self:
            transferencia.update({'temp_payment_ids': [(5, 0, 0)]})

    @api.depends('temp_payment_ids')
    def compute_totales(self):
        for i in self:
            i.total_transferencia = 0
            for payment in i.temp_payment_ids:
                i.total_transferencia += payment.amount

    def validaciones(self):
        if not self.payment_ids:
            raise exceptions.ValidationError(
                'No se puede confirmar una transferencia si no hay elegido valores a transferir')

    def reprocesar_transferencia(self):
        for transferencia in self:
            transferencia.action_cancel(True)
            transferencia.action_confirmar(True)

    @api.depends('temp_payment_ids')
    def action_confirmar(self, actualizacion=False):
        for transferencia in self:
            if transferencia.name == 'Borrador':
                transferencia.write({'name': transferencia.genera_secuencia()})
            if not actualizacion:
                if not transferencia.journal_source_id:
                    raise exceptions.ValidationError('Debe elegir un Diario de origen')
                transferencia.write({'payment_ids': [(5, 0, 0)]})
                for i in transferencia.temp_payment_ids:
                    transferencia.write({'payment_ids': [(4, i.id, 0)]})

            transferencia.write({'state': 'done'})
            transferencia.genera_transferencia()
            transferencia.actualiza_estado_payments('confirmar')
        return

    @api.onchange('journal_source_id')
    @api.depends('journal_source_id')
    def onchange_journal_source(self):
        for transferencia in self:
            transferencia.update({'temp_payment_ids': [(5, 0, 0)]})

    def button_confirmar(self):
        for transferencia in self:
            transferencia.action_confirmar()

    def button_cancel(self):
        for transferencia in self:
            transferencia.action_cancel()

    def actualiza_estado_payments(self, operacion):
        for transferencia in self:
            for payment in transferencia.payment_ids:
                if operacion == 'confirmar':
                    payment.write({'journal_actual_id': transferencia.journal_id.id})
                elif operacion == 'cancelar':
                    if transferencia.journal_source_id:
                        payment.write({'journal_actual_id': transferencia.journal_source_id.id})
                    else:
                        payment.write({'journal_actual_id': payment.journal_id.id})
        return

    def action_cancel(self, actualizacion=False):
        for transferencia in self:
            transferencia.actualiza_estado_payments('cancelar')
            if not actualizacion:
                for i in transferencia.payment_ids:
                    transferencia.write({'payment_ids': [(3, i.id, 0)]})
            transferencia.write({'state': 'cancel'})
            transferencia.cancela_transferencia()

            if actualizacion:
                transferencia.move_id.button_cancel()
                transferencia.move_id.unlink()
        return True

    def genera_transferencia(self):
        for transferencia in self:
            print('Name', transferencia.name)
            print('Boleta', transferencia.nro_boleta_deposito)
            transfer = {
                # 'journal_actual_id': diario.id,
                'payment_type': 'outbound',
                'journal_id': transferencia.journal_source_id.id,
                'destination_journal_id': transferencia.journal_id.id,
                'date': transferencia.fecha,
                'ref': '%s - Nro. de depósito %s' % (transferencia.name, str(transferencia.nro_boleta_deposito)),
                'amount': transferencia.total_transferencia,
                'is_internal_transfer': True,
                'payment_method_id': self.env['account.payment.method'].search([])[0].id
            }
            res = self.env['account.payment'].create(transfer)
            res.action_post()
            transferencia.write({'transfer_ids': [(4, res.id, 0)]})

    def cancela_transferencia(self):
        for transferencia in self:
            for i in transferencia.transfer_ids:
                i.action_cancel()
                i.paired_internal_transfer_payment_id.action_cancel()

    def button_draft(self):
        self.write({'state': 'draft'})

    def genera_secuencia(self):
        seq = self.sudo().env['ir.sequence'].next_by_code('seq_transferencia')
        return seq
