from odoo import fields, models, api, exceptions


class Wizard(models.TransientModel):
    _name = 'reporte_libro_diario.wizard'
    _description = 'New Description'

    fecha_inicio = fields.Date(string='Fecha de inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de fin', required=True)
    # compania = fields.Many2one('res.company', string='Compañía', required=True)

    def button_imprimir(self):
        data = {
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            # 'compania': self.compania.id,
        }
        return self.env.ref('reporte_libro_diario.reporte_diario_action').report_action(self, data=data)

    def button_imprimir_xlsx(self):
        data = {
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            # 'compania': self.compania.id,
        }
        return self.env.ref('reporte_libro_diario.reporte_diario_action_xlsx').report_action(self, data=data)


class ReporteLibroDiario(models.AbstractModel):
    _name = 'report.reporte_libro_diario.report_diario'

    @api.model
    def _get_report_values(self, docids, data=None):
        # company_obj = self.env['res.company'].browse(data.get('compania'))
        moves = self.env['account.move'].search(
            [
                ('date', '>=', data.get('fecha_inicio')),
                ('date', '<=', data.get('fecha_fin')),
                ('state', '=', 'posted'),
                # ('company_id', '=', data.get('compania'))
            ]
        )
        if moves:
            moves = moves.sorted(key=lambda x: (x.date, x.id))
        docargs = {
            'docs': moves,
            'fecha_inicio': data.get('fecha_inicio'),
            'fecha_fin': data.get('fecha_fin'),
            # 'company_name': company_obj.name

        }
        return docargs


class ReporteLibroDiarioXls(models.AbstractModel):
    _name = 'report.reporte_libro_diario.report_diario_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):

        # company_obj = self.env['res.company'].browse(data.get('compania'))
        moves = self.env['account.move'].search(
            [
                ('date', '>=', data.get('fecha_inicio')),
                ('date', '<=', data.get('fecha_fin')),
                ('state', '=', 'posted'),
                # ('company_id', '=', data.get('compania'))
            ]
        )
        if moves:
            moves = moves.sorted(key=lambda x: (x.date, x.id))

        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Hoja 1')
        bold = workbook.add_format({'bold': True})
        numerico = workbook.add_format({'num_format': True, 'align': 'right'})
        numerico.set_num_format('#,##0')
        num_float = workbook.add_format({'num_format': True, 'align': 'right'})
        num_float.set_num_format('#,##0.00')
        num_float_bold = workbook.add_format({'num_format': True, 'align': 'right', 'bold': True})
        num_float_bold.set_num_format('#,##0.00')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True})
        numerico_total.set_num_format('#,##0')
        wrapped_text = workbook.add_format()
        wrapped_text.set_text_wrap()
        wrapped_text_bold = workbook.add_format({'bold': True})
        wrapped_text_bold.set_text_wrap()

        position_x = 0
        position_y = 0

        def addSalto():
            global position_x
            global position_y
            position_x = 0
            position_y += 1

        def addRight():
            global position_x
            position_x += 1

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            sheet.write(position_y, position_x, to_write, format)

        def simpleWrite(to_write, format=None):
            global sheet
            sheet.write(position_y, position_x, to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            sheet.write(position_y, position_x, to_write, format)

        simpleWrite("Razon social:", bold)
        rightAndWrite(self.env.user.company_id.name)
        # rightAndWrite(company_obj.name)
        breakAndWrite("RUC:", bold)
        rightAndWrite(self.env.user.company_id.partner_id.vat)
        # rightAndWrite(company_obj.partner_id.vat)
        breakAndWrite("")
        breakAndWrite("Periodo:", bold)
        rightAndWrite("Del " + datas['fecha_inicio'].strftime("%d/%m/%Y") +
                      " al " + datas['fecha_fin'].strftime('%d/%m/%Y'))

        addSalto()
        rightAndWrite("Libro diario", bold)
        breakAndWrite("Cuenta", bold)
        rightAndWrite("Descripción", bold)
        rightAndWrite("Detalle", bold)
        rightAndWrite("Débito", bold)
        rightAndWrite("Crédito", bold)

        for move in moves:
            breakAndWrite("Asiento: %s" % move.id, bold)
            rightAndWrite("Fecha: %s" % move.date.strftime("%d/%m/%Y"), bold)
            for line in move.line_ids:
                breakAndWrite(line.account_id.display_name)
                rightAndWrite(line.name or "")
                rightAndWrite(line.ref or "")
                rightAndWrite(line.debit, numerico)
                rightAndWrite(line.credit, numerico)
