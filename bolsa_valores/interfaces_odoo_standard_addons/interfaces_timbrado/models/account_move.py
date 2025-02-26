from odoo import api, fields, models, exceptions, _

import re
import math


class AccountMove(models.Model):
    _inherit = 'account.move'

    timbrado = fields.Char(string="Timbrado")
    timbrado_proveedor = fields.Char(string="Timbrado del proveedor")

    def button_anular(self):
        for i in self:
            i.validar_timbrado()
            if i.state != 'draft':
                i.button_draft()
            i.button_cancel()
            return

    # @api.onchange('name')
    # def onchName(self):
    #     if self.move_type in ['out_invoice','out_refund']:
    #         if self.name and self.name != '/':
    #             self.validarnrofactura(self.name)

    def validar_timbrado(self):
        if self.move_type in ['out_invoice', 'out_refund'] and self.name and self.name != '/':
            timbrado = self.journal_id.timbrados_ids.filtered(
                lambda x: x.active and x.tipo_documento == self.move_type)
            if len(timbrado) > 1:
                raise exceptions.ValidationError(
                    'Tiene más de 1 timbrado activo para éste Diario. Favor verificar')
            if timbrado:
                print('Timbrado : ', timbrado.name)
                print('Rango final : ', timbrado.rango_final)
                ###### Para primera numeracion de factura de un diario nuevo ############
                if len(self.name.split('-')) == 1:
                    nro = (7 - len(str(timbrado.proximo_numero))) * '0'
                    nro += str(timbrado.proximo_numero)
                    self.name = timbrado.nro_establecimiento + '-' + timbrado.nro_punto_expedicion + '-' + nro
                #######################################################
                self.validarnrofactura(self.name)
                numero = int(self.name.split('-')[-1])
                nro_establecimiento = self.name.split('-')[0]
                nro_pto_expedicion = self.name.split('-')[1]
                if nro_pto_expedicion != timbrado.nro_punto_expedicion:
                    raise exceptions.ValidationError(
                        'El numero de punto de expedicion no coincide con el del timbrado activo')
                if nro_establecimiento != timbrado.nro_establecimiento:
                    raise exceptions.ValidationError(
                        'El numero de establecimiento no coincide con el del timbrado activo')
                if numero > timbrado.rango_final:
                    raise exceptions.ValidationError(
                        'El timbrado activo ha llegado a su número final')
                fecha = self.invoice_date or fields.Date.today()
                if fecha > timbrado.fin_vigencia:
                    raise exceptions.ValidationError(
                        'La fecha de la factura no puede ser mayor a la fecha de fin de vigencia del timbrado')
                if fecha < timbrado.inicio_vigencia:
                    raise exceptions.ValidationError(
                        'La fecha de la factura no puede ser menor a la fecha de fin de vigencia del timbrado')
                return
            else:
                raise exceptions.ValidationError(
                    'No existe un timbrado activo')
        else:
            return

    def validarnrofactura(self, seq):
        # validar formato (xxx-xxx-xxxxxxx)
        patron = re.compile(r'((^\d{3})[-](\d{3})[-](\d{7}$)){1}')
        # if not self.es_autofactura:
        if seq:
            m = patron.match(seq)
            if m is None:
                raise exceptions.ValidationError('El nro de factura no tiene el formato adecuado (xxx-xxx-xxxxxxx)')

    def validar_ruc_vacio(self):
        for i in self:
            if not i.partner_id.vat and not i.partner_id.obviar_validacion:
                raise exceptions.ValidationError("El cliente no tiene asignado un RUC. Favor agregarlo")
            return

    def _post(self, soft):
        res = super(AccountMove, self)._post(soft)
        for i in self:
            if i.move_type in ['out_invoice', 'out_refund']:

                i.validar_ruc_vacio()
                i.validar_timbrado()
                i.validar_cantidad_lineas()
                timbrado = i.journal_id.timbrados_ids.filtered(lambda x: x.tipo_documento == i.move_type)
                if timbrado and len(timbrado) == 1:
                    timbrado = timbrado[0].name
                i.write({'timbrado': timbrado or None})
        return res

    @api.onchange('invoice_line_ids')
    @api.depends('invoice_line_ids', 'journal_id')
    def validar_cantidad_lineas(self):
        for i in self:
            if i.journal_id.max_lineas != 0:
                if len(i.invoice_line_ids) > i.journal_id.max_lineas:
                    raise exceptions.ValidationError(
                        "Se ha llegado a la cantidad máxima de lineas soportadas en la factura")
            return

    def button_actualizar_nro_factura(self):

        # if self.name:
        #    prefijo = self.name.split('-')[0] + "-" + self.name.split('-')[1]
        if not self.name:
            raise exceptions.ValidationError(
                'El nro. de ésta factura no es editable')

        return {
            'name': 'Actualizar nro. de factura',
            'type': 'ir.actions.act_window',
            'res_model': 'interfaces_timbrado.actualizar_nro_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_move_id': self.id}
        }

    # para tener en cuenta rectificativas solo si se escribe en la secuencia
    def write(self, vals):
        print(vals)
        res = super(AccountMove, self).write(vals)
        if vals.get("sequence_number"):
            for i in self:
                i.validar_timbrado()
        return res

    # def create(self, vals):
    #     res = super(AccountMove, self).create(vals)
    #     for i in self:
    #         i.validar_timbrado()
    #     return res

    def action_switch_invoice_into_refund_credit_note(self):
        # interfaces_timbrado/models/account_move.py
        # fix para evitar cambiar facturas ya canceladas
        if any(move.state == 'cancel' for move in self):
            raise exceptions.ValidationError(_("This action isn't available for this document."))

        return super(AccountMove, self).action_switch_invoice_into_refund_credit_note()


class ActualizaNroFacturaWizard(models.TransientModel):
    _name = 'interfaces_timbrado.actualizar_nro_wizard'

    move_id = fields.Many2one('account.move', string='Factura', required=True)
    nuevo_nro = fields.Char(string='Nuevo nro.', required=True)

    # prefijo = fields.Char(string="Prefijo", required=True)

    @api.onchange('move_id')
    @api.depends('move_id', 'nuevo_nro')
    def preparar_nuevo_nro(self):
        if self.move_id:
            if self.move_id.name:
                nuevo = self.move_id.name
            if nuevo:
                self.nuevo_nro = nuevo

    def actualizar(self):
        nuevo = self.nuevo_nro
        # self.validar_nuevo(self.nuevo_nro)
        if '*' in nuevo:
            nuevo = nuevo + " - A modificar"
        self.move_id.write({'name': nuevo})
        return

    # def validar_nuevo(self, nuevo):
    #    if not re.match('^[0-9]+[*]?$', nuevo):
    #        raise exceptions.ValidationError(
    #            'Sólo se admiten números y un "*"')
