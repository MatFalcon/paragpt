from odoo import fields, api, models, exceptions
import re, math


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fake_number = fields.Char(compute="set_nro_factura", store=True, readonly=True, copy=False, string="Número")
    timbrado_proveedor=fields.Char(string="Timbrado del Proveedor")
    @api.depends('move_name', 'number', 'journal_id')
    def set_nro_factura(self):
        for i in self:
            numero = i.move_name or i.number or False
            if not numero:
                secuencia = i.journal_id.sequence_id
                if secuencia:
                    numero = secuencia.prefix + (str(secuencia.number_next_actual).zfill(secuencia.padding))
                else:
                    raise exceptions.ValidationError('No hay ningún diario configurado para ésta operación')
            i.fake_number = numero

    
    def action_cancel(self):

        for i in self:
            if not i.move_name:
                next_number = i.journal_id.sequence_id.next_by_id()
                i.move_name = next_number
                i.fake_number = next_number
            super(AccountInvoice, i).action_cancel()
        return True

    def button_actualizar_nro_factura(self):

        if self.fake_number:
            prefijo = self.fake_number.split('-')[0] + "-" + self.fake_number.split('-')[1]
        elif self.move_name:
            prefijo = self.move_name.split('-')[0] + "-" + self.move_name.split('-')[1]
        elif self.number:
            prefijo = self.number.split('-')[0] + "-" + self.number.split('-')[1]
        else:
            raise exceptions.ValidationError('El nro. de ésta factura no es editable')

        return {
            'name': 'Actualizar nro. de factura',
            'type': 'ir.actions.act_window',
            'res_model': 'interfaces_timbrado.actualizar_nro_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_invoice_id': self.id, 'default_prefijo': prefijo}
        }

    def validar_timbrado(self):
        if self.type=='out_invoice':
            print("Invoice : ", self.name, " Read : ", self.read())
            timbrado= self.journal_id.timbrados_ids.filtered(lambda x:x.active)
            if len(timbrado)>1:
                raise exceptions.ValidationError('Tiene más de 1 timbrado activo para éste Diario. Favor verificar')
            if timbrado:
                numero=self.journal_id.sequence_id.number_next_actual
                if numero>timbrado.rango_final:
                    raise exceptions.ValidationError('El timbrado activo ha llegado a su número final')
                fecha=self.date_invoice or fields.Date.today()
                if fecha>timbrado.fin_vigencia:
                    raise exceptions.ValidationError('La fecha de la factura no puede ser mayor a la fecha de fin de vigencia del timbrado')
                if fecha<timbrado.inicio_vigencia:
                    raise exceptions.ValidationError('La fecha de la factura no puede ser menor a la fecha de inicio de vigencia del timbrado')
                return
            else:
                raise exceptions.ValidationError('No existe un timbrado activo')
        else:
            return

    
    def action_invoice_open(self):
        for i in self:
            self.validar_timbrado()
            if i.type == 'out_invoice':
                if not i._context.get('opciones') or i._context.get('opciones') == 'dividir':
                    maximo_lineas = i.journal_id.max_lineas
                    if maximo_lineas > 0 and i.journal_id.type == 'sale':
                        lineas_factura = len(i.invoice_line_ids)
                        if lineas_factura > maximo_lineas:
                            return {
                                'name': "Opciones de factura",
                                'view_mode': 'form',
                                'view_type': 'form',
                                'res_model': 'interfaces_timbrado.split_factura',
                                'type': 'ir.actions.act_window',
                                'target': 'new',
                                'context': {'default_invoice_id': i.id}
                            }
                        else:
                            super(AccountInvoice, i).action_invoice_open()
                    else:
                        super(AccountInvoice, i).action_invoice_open()
                elif i._context.get('opciones') == 'mantener':
                    super(AccountInvoice, i).action_invoice_open()
            else:
                super(AccountInvoice, i).action_invoice_open()


class ActualizaNroFacturaWizard(models.TransientModel):
    _name = 'interfaces_timbrado.actualizar_nro_wizard'

    invoice_id = fields.Many2one('account.invoice', string='Factura', required=True)
    nuevo_nro = fields.Char(string='Nuevo nro.', required=True)
    prefijo = fields.Char(string="Prefijo", required=True)

    @api.onchange('invoice_id')
    @api.depends('invoice_id', 'nuevo_nro', 'prefijo')
    def preparar_nuevo_nro(self):
        if self.invoice_id:
            if self.invoice_id.fake_number:
                nuevo = self.invoice_id.fake_number.split('-')[2]
            elif self.invoice_id.move_name:
                nuevo = self.invoice_id.move_name.split('-')[2]
            elif self.invoice_id.number:
                nuevo = self.invoice_id.number.split('-')[2]

            if nuevo:
                self.nuevo_nro = nuevo

    def actualizar(self):
        nuevo = self.prefijo + "-" + self.nuevo_nro
        self.validar_nuevo(self.nuevo_nro)
        self.invoice_id.write({'number': nuevo, 'fake_number': nuevo, 'move_name': nuevo})
        self.invoice_id.move_id.write({'name': nuevo})
        return

    def validar_nuevo(self, nuevo):
        if not re.match('^[0-9]+[*]?$', nuevo):
            raise exceptions.ValidationError('Sólo se admiten números y "*"')


class SplitFacturas(models.TransientModel):
    _name = 'interfaces_timbrado.split_factura'

    dividir_facturas = fields.Selection(string="Opciones de factura", selection=[
        ('dividir', 'Dividir en 2 o más facturas'), ('mantener', 'Mantener en 1 factura')], default='dividir')
    invoice_id = fields.Many2one('account.invoice', string='Factura asociada')

    def button_confirmar(self):
        a = 1
        if self.invoice_id:
            if self.dividir_facturas == 'mantener':
                self.invoice_id.with_context({'opciones': 'mantener'}).action_invoice_open()
            elif self.dividir_facturas == 'dividir':
                facturas = self.partir_facturas()
                facturas_ids = []
                for i in facturas:
                    i.with_context({'opciones': 'mantener'}).action_invoice_open()
                    facturas_ids.append(i.id)
                tree_view_id = self.env.ref('account.invoice_tree')
                form_view_id = self.env.ref('account.invoice_form')
                return {
                    'name': 'Facturas creadas',
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_id.id, 'tree'), (form_view_id.id, 'form')],
                    'res_model': 'account.invoice',
                    'domain': [('id', 'in', facturas_ids)]
                }

    def partir_facturas(self):
        factura_orig = self.invoice_id
        lineas_maximas = factura_orig.journal_id.max_lineas
        cantidad_facturas = math.ceil(len(factura_orig.invoice_line_ids) / lineas_maximas)
        # lineas_orig = factura_orig.invoice_line_ids
        new_invoices_arr = []
        lineas_sobrantes = []
        # factura_orig.update({'tax_line_ids':False})
        for i in range(0, cantidad_facturas):
            a = 1
            if i == 0:
                cont = 0
                for j in factura_orig.invoice_line_ids:
                    if cont > lineas_maximas - 1:
                        j.update({'invoice_id': None})
                        lineas_sobrantes.append(j)
                    cont += 1

                for line in factura_orig.invoice_line_ids:
                    line._compute_price()
                factura_orig.compute_taxes()
                factura_orig._compute_amount()
                new_invoices_arr.append(factura_orig)
            else:
                new_invoice = factura_orig.copy()

                for j in new_invoice.invoice_line_ids:
                    j.unlink()
                cont = 0
                for x in filter(lambda x: not x.invoice_id, lineas_sobrantes):
                    if cont <= lineas_maximas - 1:
                        x.update({'invoice_id': new_invoice.id})
                        # lineas_sobrantes.remove(x)
                        cont += 1
                    else:
                        break
                for line in new_invoice.invoice_line_ids:
                    line._compute_price()
                new_invoice.compute_taxes()
                new_invoice._compute_amount()
                new_invoices_arr.append(new_invoice)

        return new_invoices_arr
