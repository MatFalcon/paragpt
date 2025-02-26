from odoo import api, fields, models, exceptions


class PlanillaDescuentos(models.Model):
    _name = 'rrhh_novedades.planilla_descuentos'
    _description = 'Planilla'

    name = fields.Char(string="Número", required=True,
                       default=lambda self: self.default_name())
    fecha = fields.Date(string="Fecha", required=True)
    user_id = fields.Many2one(
        "res.users", string="Usuario", compute="compute_user_id", store=True)
    line_ids = fields.One2many(
        "rrhh_novedades.planilla_descuentos.line", "planilla_id", string="Lineas")
    tipo_id = fields.Many2one("hr.novedades.tipo", string="Tipo de novedad", required=True,
                              domain=[('name', 'ilike', 'despensa')])
    state = fields.Selection(string="Estado", selection=[(
        "draft", "Borrador"), ("done", "Confirmado"), ("cancel", "Cancelado")], default="draft")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def unlink(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            if i.state != "draft":
                raise exceptions.ValidationError(
                    "No se pueden eliminar planillas que no estén en estado Borrador")
        return super(PlanillaDescuentos, self).unlink()

    @api.onchange('name')
    def compute_user_id(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            i.user_id = self.env.user

    def button_confirmar(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            for j in i.line_ids:
                j.crear_novedad()
            i.button_calcular_saldos()
            i.write({'state': 'done'})

    def button_cancelar(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            for n in i.line_ids:
                n.novedad_id.button_cancelar()
            i.write({'state': 'cancel'})

    def button_draft(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            i.write({'state': 'draft'})

    def default_name(self):
        # rrhh_novedades/models/planilla_descuentos.py
        return self.env['ir.sequence'].sudo().next_by_code('seq_planilla_desc')

    @api.depends('name', 'line_ids')
    @api.onchange('name')
    def agregar_empleados(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            employees = self.env['hr.employee'].sudo().search([('company_id', '=', self.env.company.id)])
            new_lines = []
            if not i.line_ids:
                for e in employees:
                    new_line = {
                        'employee_id': e.id,
                    }
                    i.write({'line_ids': [(0, 0, new_line)]})

    def button_calcular_saldos(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for l in self.line_ids:
            l.compute_neto_cobrar()


class PlanillaDescuentosLine(models.Model):
    _name = 'rrhh_novedades.planilla_descuentos.line'
    _description = "Linea de planilla"

    planilla_id = fields.Many2one("rrhh_novedades.planilla_descuentos")
    fecha = fields.Date(string="Fecha", related="planilla_id.fecha")

    employee_id = fields.Many2one(
        "hr.employee", string="Empleado", required=True)
    job_id = fields.Many2one(
        "hr.job", related="employee_id.job_id", string="Cargo")
    doma = fields.Float(string="Doma", default=0)
    pollo = fields.Float(string="Pollo", default=0)
    lechuga = fields.Float(string="Lechuga", default=0)
    huevo = fields.Float(string="Huevo", default=0)
    despensa = fields.Float(string="Despensa", default=0)
    otros = fields.Float(string="Otros", default=0)
    comentarios = fields.Char(string="Comentarios")
    neto_cobrar = fields.Float(string="Saldo actual", readonly=True)
    saldo_calculado = fields.Float(string="Saldo calculado", readonly=True)
    novedad_id = fields.Many2many("hr.novedades", string="Novedad")
    total_egresos = fields.Float(
        string="Total egresos", compute="compute_egresos")

    @api.depends('pollo', 'lechuga', 'huevo', 'despensa', 'otros')
    def compute_egresos(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            i.total_egresos = i.pollo + i.lechuga + i.huevo + i.despensa + i.otros

    def compute_neto_cobrar(self):
        # rrhh_novedades/models/planilla_descuentos.py
        for i in self:
            if i.employee_id and i.fecha:
                nomina = self.env['hr.payslip'].search(
                    [('employee_id', '=', i.employee_id.id), ('state', '=', 'verify')])
                if nomina:
                    nomina = nomina.filtered(
                        lambda x: i.fecha >= x.date_from and i.fecha <= x.date_to)
                if nomina and len(nomina) == 1:
                    nomina.compute_sheet()
                    i.write({'neto_cobrar': nomina.net_wage, 'saldo_calculado': nomina.net_wage +
                                                                                i.doma - (
                                                                                            i.pollo + i.lechuga + i.huevo + i.despensa + i.otros)})

                else:
                    i.write({'neto_cobrar': 0, 'saldo_calculado': 0})
            else:
                i.write({'neto_cobrar': 0, 'saldo_calculado': 0})

    def crear_novedad(self):
        # rrhh_novedades/models/planilla_descuentos.py
        novedad = {
            'employee_id': self.employee_id.id,
            'fecha': self.fecha,
            'monto': self.pollo + self.lechuga + self.huevo + self.despensa + self.otros,
            'tipo_id': self.planilla_id.tipo_id.id,
            'comentarios': self.comentarios
        }
        if novedad.get('monto') > 0:
            novedad_id = self.env['hr.novedades'].create(novedad)
            self.write({'novedad_id': [(4, novedad_id.id, 0)]})
            if novedad_id:
                novedad_id.button_confirmar()

        if self.doma > 0:
            tipo_novedad_id = self.env['hr.novedades.tipo'].search(
                [('name', 'ilike', 'doma')])[0]
            if not tipo_novedad_id:
                raise exceptions.ValidationError(
                    "No existe un tipo de novedad para Doma. Favor contactar con el encargado de RRHH")
            novedad_doma = {
                'employee_id': self.employee_id.id,
                'fecha': self.fecha,
                'monto': self.doma,
                'tipo_id': tipo_novedad_id.id,
                'comentarios': self.comentarios
            }
            novedad_doma_id = self.env['hr.novedades'].create(novedad_doma)
            self.write({'novedad_id': [(4, novedad_doma_id.id, 0)]})
            if novedad_doma_id:
                novedad_doma_id.button_confirmar()


class ReporteVentasXlsx(models.AbstractModel):
    _name = 'report.rrhh_novedades.reporte_descuentos'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):
        # rrhh_novedades/models/planilla_descuentos.py
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
        breakAndWrite("Usuario:", bold)
        rightAndWrite(datas.user_id.name if datas.user_id else "")
        breakAndWrite("Tipo de novedad:", bold)
        rightAndWrite(datas.tipo_id.name if datas.tipo_id else "")
        addSalto()
        simpleWrite("Fecha", bold)
        rightAndWrite("Empleado", bold)
        rightAndWrite("Cargo", bold)
        rightAndWrite("Seccion", bold)
        rightAndWrite("Campo", bold)
        rightAndWrite("Doma", bold)
        rightAndWrite("Pollo", bold)
        rightAndWrite("Lechuga", bold)
        rightAndWrite("Huevo", bold)
        rightAndWrite("Otros", bold)
        rightAndWrite("Total Egresos", bold)
        rightAndWrite("Comentarios", bold)
        total_general = 0
        for linea in lineas:
            if linea.total_egresos > 0 or linea.doma > 0:
                addSalto()
                simpleWrite(linea.fecha.strftime("%d/%m/%Y") if linea.fecha else "")
                rightAndWrite(linea.employee_id.name if linea.employee_id else "")
                rightAndWrite(linea.job_id.name if linea.job_id else "")
                rightAndWrite(linea.doma if linea.doma else 0)
                rightAndWrite(linea.pollo if linea.pollo else 0)
                rightAndWrite(linea.lechuga if linea.lechuga else 0)
                rightAndWrite(linea.huevo if linea.huevo else 0)
                rightAndWrite(linea.otros if linea.otros else 0)
                rightAndWrite(linea.total_egresos if linea.total_egresos else 0)
                rightAndWrite(linea.comentarios if linea.comentarios else "")
