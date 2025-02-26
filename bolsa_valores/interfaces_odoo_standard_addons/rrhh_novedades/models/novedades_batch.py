from odoo import api, fields, models, exceptions


class NovedadesBatch(models.Model):
    _name = 'rrhh_novedades.novedades_batch'
    _description = 'Planilla'

    name = fields.Char(string="Número", required=True, default="Nuevo")
    fecha = fields.Date(string="Fecha", required=True)
    line_ids = fields.One2many("rrhh_novedades.novedades_batch.line", "batch_id", string="Lineas")
    novedad_tipo_id = fields.Many2one("hr.novedades.tipo", string="Tipo de novedad", domain=[('periodicidad', '=', 'puntual')], required=True)
    state = fields.Selection(string="Estado", selection=[
        ("draft", "Borrador"),
        ("done", "Confirmado"),
        ("cancel", "Cancelado"),
    ], default="draft")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    periodicidad = fields.Selection(
        string="Periodicidad",
        selection=[("puntual", "Puntual"), ("periodico", "Periodico")],
        related="novedad_tipo_id.periodicidad"
    )

    def unlink(self):
        # rrhh_novedades/models/novedades_batch.py
        for i in self:
            if i.state != "draft":
                raise exceptions.ValidationError("No se pueden eliminar planillas que no estén en estado Borrador")
        return super(NovedadesBatch, self).unlink()

    def button_confirmar(self):
        # rrhh_novedades/models/novedades_batch.py
        for i in self:
            for j in i.line_ids:
                j.crear_novedad()
            i.write({'state': 'done'})

    def button_cancelar(self):
        # rrhh_novedades/models/novedades_batch.py
        for i in self:
            for n in i.line_ids:
                n.novedad_id.button_cancelar()
            i.write({'state': 'cancel'})

    def button_draft(self):
        # rrhh_novedades/models/novedades_batch.py
        for i in self:
            i.write({'state': 'draft'})

    def default_name(self):
        # rrhh_novedades/models/novedades_batch.py
        return self.env['ir.sequence'].sudo().next_by_code('seq_nov_batch')

    @api.model
    def create(self, vals):
        # rrhh_novedades/models/novedades_batch.py
        if vals.get('name') == "Nuevo" or not vals.get("name"):
            vals['name'] = self.default_name()
        return super(NovedadesBatch, self).create(vals)

    # @api.depends('name', 'line_ids')
    # @api.onchange('name')
    # def agregar_empleados(self):
    #     # rrhh_novedades/models/novedades_batch.py
    #     for this in self:
    #         contracts = this.env['hr.contract'].sudo().search([('company_id', '=', this.env.company.id)])
    #         for contract in contracts:
    #             if contract not in this.line_ids.contract_id:
    #                 i.write({'line_ids': [(0, 0, {
    #                     'employee_id': contract.employee_id.id,
    #                     'contract_id': contract.id,
    #                 })]})

    def button_agregar_empleados(self):
        # rrhh_novedades/models/novedades_batch.py
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agregar Empleados',
            'view_mode': 'form',
            'res_model': 'rrhh_novedades.novedades_batch.add_employees',
            'context': {'default_batch_id': self.id},
            'target': 'new',
        }


class NovedadesBatchAddEmployees(models.TransientModel):
    _name = 'rrhh_novedades.novedades_batch.add_employees'
    _description = "Agregar Empleados a las Novedades por Lote"

    batch_id = fields.Many2one('rrhh_novedades.novedades_batch', string='Lote de Novedades')
    contract_ids = fields.Many2many('hr.contract', string='Contratos')

    def add_employees(self):
        # rrhh_novedades/models/novedades_batch.py
        if not self.batch_id.state in ['draft']:
            raise exceptions.ValidationError('El lote de novedades debe de estar en estado borrador para agregar empleados')
        self.batch_id.write({'line_ids': [(0, 0, {
            'employee_id': contract.employee_id.id,
            'contract_id': contract.id,
        }) for contract in self.contract_ids if contract not in self.batch_id.line_ids.contract_id]})


class NovedadesBatchLine(models.Model):
    _name = 'rrhh_novedades.novedades_batch.line'
    _description = "Linea de planilla"

    batch_id = fields.Many2one("rrhh_novedades.novedades_batch")
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    contract_id = fields.Many2one("hr.contract", string='Contrato', required=True)
    job_id = fields.Many2one("hr.job", related="employee_id.job_id", string="Cargo")
    fecha = fields.Date(string="Fecha", related="batch_id.fecha")
    monto = fields.Float(string="Monto", default=0)
    novedad_id = fields.Many2one("hr.novedades", string="Novedad")

    def crear_novedad(self):
        # rrhh_novedades/models/novedades_batch.py
        if self.monto > 0:
            novedad = self.env['hr.novedades'].create({
                'tipo_id': self.batch_id.novedad_tipo_id.id,
                'employee_id': self.employee_id.id,
                'contract_id': self.contract_id.id,
                'fecha': self.fecha,
                'monto': self.monto,
                'company_id': self.batch_id.company_id.id,
            })
            novedad.button_confirmar()
            self.write({'novedad_id': novedad.id})


class ReporteVentasXlsx(models.AbstractModel):
    _name = 'report.rrhh_novedades.reporte_lote_novedades'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):
        # rrhh_novedades/models/novedades_batch.py
        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Hoja 1')
        bold = workbook.add_format({'bold': True})
        numerico = workbook.add_format({'num_format': True, 'align': 'right'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format({'num_format': True, 'align': 'right', 'bold': True})
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

        lineas = datas.line_ids

        simpleWrite("Planilla:", bold)
        rightAndWrite(datas.name if datas.name else "")
        breakAndWrite("Fecha:", bold)
        rightAndWrite(datas.fecha.strftime("%d/%m/%Y") if datas.fecha else "")
        breakAndWrite("Tipo de novedad:", bold)
        rightAndWrite(datas.novedad_tipo_id.name if datas.novedad_tipo_id else "")
        addSalto()
        simpleWrite("Sección", bold)
        rightAndWrite("Campo", bold)
        rightAndWrite("Empleado", bold)
        rightAndWrite("Cargo", bold)
        rightAndWrite("Concepto", bold)
        rightAndWrite("Monto", bold)
        rightAndWrite("Comentarios", bold)
        total_general = 0
        for linea in lineas:
            addSalto()
            rightAndWrite(linea.employee_id.name if linea.employee_id else "")
            rightAndWrite(linea.job_id.name if linea.job_id else "")
            rightAndWrite(linea.concepto if linea.concepto else "")
            rightAndWrite(linea.monto if linea.monto else 0, numerico)
            rightAndWrite(linea.comentarios if linea.comentarios else "")
            total_general = total_general + linea.monto
