from odoo import api, exceptions, fields, models


class WizardFacturas(models.TransientModel):
    _name = 'pbp.wizard.facturas'
    _description = 'Wizard facturas'

    fecha_inicio = fields.Date(string="Fecha Inicial", default=fields.Date.today(), required=True)
    fecha_fin = fields.Date(string="Fecha Final", default=fields.Date.today(), required=True)
    fecha_factura = fields.Date(string="Fecha de factura/s",
                                help="Si no se elige una fecha, todas las facturas serán creadas al día de hoy")
    partner_ids = fields.Many2many('res.partner', string='Partner/s', required=True)
    modelos = fields.Selection(
        selection=[
            ('novedades', 'Novedades'),
            ('sistema_tradicional', 'Sistema Tradicional'),
            ('gastos_administrativos', 'Gastos Administrativos'),
            ('transferencia_cartera','Transferencia de Carteras')
        ], help="Si no se elige una opción, serán facturadas todas las opciones", required=False, string="Opciones"
    )

    def button_generar_factura(self):
        facturas = self.action_facturar()

        return {
            'name': 'Facturas generadas',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', facturas)],
        }

    def action_facturar(self):
        # Obtener las monedas PYG y USD
        PYG = self.env['res.currency'].search([('name', '=', 'PYG')])
        USD = self.env['res.currency'].search([('name', '=', 'USD-Venta')])

        facturas = []  # Lista para almacenar las facturas creadas

        # Iterar sobre los clientes seleccionados en el asistente
        if self.partner_ids:
            for partner in self.partner_ids:
                # Inicializar listas para cada tipo de facturación
                novedades = []
                sistema_tradicional = []
                gastos_administrativos = []
                transferencia_cartera = []
                lineas_facturas_gs = []  # Facturas en Guaraníes
                lineas_facturas_usd = []  # Facturas en Dólares

                # Filtro base para buscar registros por cliente
                search_domain_partners = [('partner_id', '=', partner.id)]

                # 🔹 Facturación de Sistema Tradicional
                if not self.modelos or self.modelos == 'sistema_tradicional':
                    search_domain = search_domain_partners + [
                        ('invoice_id', '=', False),
                        ('product_id', '!=', False),
                        ('total', '!=', False),
                        ('fecha', '<=', self.fecha_fin),
                        ('fecha', '>=', self.fecha_inicio)
                    ]
                    sistema_tradicional = self.env['pbp.novedades_series'].search(search_domain)

                    if sistema_tradicional:
                        # Agrupar por producto
                        productos_st = set(sistema_tradicional.mapped('product_id'))
                        for p in productos_st:
                            # Sumar montos por moneda
                            sum_product_gs = sum(sistema_tradicional.filtered(
                                lambda x: x.product_id == p and x.currency_id == PYG).mapped('total'))
                            sum_product_usd = sum(sistema_tradicional.filtered(
                                lambda x: x.product_id == p and x.currency_id == USD).mapped('total'))

                            # Agregar líneas a la factura en PYG
                            if sum_product_gs:
                                lineas_facturas_gs.append((0, 0, {
                                    'partner_id': partner.id,
                                    'product_id': p.id,
                                    'currency_id': PYG.id,
                                    'price_unit': sum_product_gs,
                                    'tax_ids': [(6, 0, p.taxes_id.ids)]
                                }))
                            # Agregar líneas a la factura en USD
                            if sum_product_usd:
                                lineas_facturas_usd.append((0, 0, {
                                    'partner_id': partner.id,
                                    'product_id': p.id,
                                    'currency_id': USD.id,
                                    'price_unit': sum_product_usd,
                                    'tax_ids': [(6, 0, p.taxes_id.ids)]
                                }))

                # 🔹 Facturación de Novedades
                if not self.modelos or self.modelos == 'novedades':
                    search_domain = search_domain_partners + [
                        ('invoice_id', '=', False),
                        ('product_id', '!=', False),
                        ('subtotal', '!=', False),
                        ('fecha_operacion', '<=', self.fecha_fin),
                        ('fecha_operacion', '>=', self.fecha_inicio)
                    ]
                    novedades = self.env['pbp.novedades'].search(search_domain)

                    if novedades:
                        productos_nv = set(novedades.mapped('product_id'))
                        for p in productos_nv:
                            sum_product_gs = sum(
                                novedades.filtered(lambda x: x.product_id == p and x.currency_id == PYG).mapped(
                                    'subtotal'))
                            sum_product_usd = sum(
                                novedades.filtered(lambda x: x.product_id == p and x.currency_id == USD).mapped(
                                    'subtotal'))

                            if sum_product_gs:
                                lineas_facturas_gs.append((0, 0, {
                                    'partner_id': partner.id,
                                    'product_id': p.id,
                                    'currency_id': PYG.id,
                                    'price_unit': sum_product_gs,
                                    'tax_ids': [(6, 0, p.taxes_id.ids)]
                                }))
                            if sum_product_usd:
                                lineas_facturas_usd.append((0, 0, {
                                    'partner_id': partner.id,
                                    'product_id': p.id,
                                    'currency_id': USD.id,
                                    'price_unit': sum_product_usd,
                                    'tax_ids': [(6, 0, p.taxes_id.ids)]
                                }))

                # 🔹 Facturación de Gastos Administrativos
                if not self.modelos or self.modelos == 'gastos_administrativos':
                    product_gastos_administrativos = self.env['ir.config_parameter'].sudo().get_param(
                        'product_gastos_administrativos_id')
                    if not product_gastos_administrativos:
                        raise exceptions.UserError("Debe definir un producto para facturar gastos administrativos")

                    p = self.env['product.product'].browse(int(product_gastos_administrativos))
                    search_domain = search_domain_partners + [
                        ('invoice_id', '=', False),
                        ('monto', '!=', False),
                        ('fecha_operacion', '<=', self.fecha_fin),
                        ('fecha_operacion', '>=', self.fecha_inicio),
                        ('state', '=', 'verificado')
                    ]
                    gastos_administrativos = self.env['pbp.gastos_administrativos'].search(search_domain)

                    if gastos_administrativos:
                        sum_product_gs = sum(
                            gastos_administrativos.filtered(lambda x: x.currency_id == PYG).mapped('monto'))
                        sum_product_usd = sum(
                            gastos_administrativos.filtered(lambda x: x.currency_id == USD).mapped('monto'))

                        if sum_product_gs:
                            lineas_facturas_gs.append((0, 0, {
                                'partner_id': partner.id,
                                'product_id': p.id,
                                'currency_id': PYG.id,
                                'price_unit': sum_product_gs,
                                'tax_ids': [(6, 0, p.taxes_id.ids)]
                            }))
                        if sum_product_usd:
                            lineas_facturas_usd.append((0, 0, {
                                'partner_id': partner.id,
                                'product_id': p.id,
                                'currency_id': USD.id,
                                'price_unit': sum_product_usd,
                                'tax_ids': [(6, 0, p.taxes_id.ids)]
                            }))

                # 🔹 Creación de Facturas en USD
                if lineas_facturas_usd:
                    vals_usd = {
                        'partner_id': partner.id,
                        'currency_id': USD.id,
                        'move_type': 'out_invoice',
                        'date': self.fecha_factura if self.fecha_factura else fields.Date.today()
                    }
                    factura_usd = self.env['account.move'].create(vals_usd)
                    factura_usd.write({'invoice_line_ids': lineas_facturas_usd})
                    facturas.append(factura_usd.id)

                # 🔹 Creación de Facturas en PYG
                if lineas_facturas_gs:
                    vals_gs = {
                        'partner_id': partner.id,
                        'currency_id': PYG.id,
                        'move_type': 'out_invoice',
                        'date': self.fecha_factura if self.fecha_factura else fields.Date.today()
                    }
                    factura_gs = self.env['account.move'].create(vals_gs)
                    factura_gs.write({'invoice_line_ids': lineas_facturas_gs})
                    facturas.append(factura_gs.id)

            return facturas  # Retorna la lista de facturas creadas

