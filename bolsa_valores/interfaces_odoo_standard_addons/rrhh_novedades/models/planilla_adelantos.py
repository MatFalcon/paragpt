
from odoo import api, fields, models,exceptions


class PlanillaAdelantos(models.Model):
    _name = 'rrhh_novedades.planilla_adelantos'
    _description = 'Planilla'

    name=fields.Char(string="Número",required=True,default=lambda self:self.default_name())
    fecha=fields.Date(string="Fecha",required=True)
    user_id=fields.Many2one("res.users",string="Usuario",compute="compute_user_id",store=True)
    line_ids=fields.One2many("rrhh_novedades.planilla_adelantos.line","planilla_id",string="Lineas")
    tipo_id=fields.Many2one("hr.novedades.tipo",string="Tipo de novedad",domain=[('name','ilike','giro')])
    state=fields.Selection(string="Estado",selection=[("draft","Borrador"),("done","Confirmado"),("cancel","Cancelado")],default="draft")
    company_id=fields.Many2one('res.company',default=lambda self:self.env.company)

    def button_calcular_saldos(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for l in self.line_ids:
            l.compute_neto_cobrar()
            
    def unlink(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            if i.state != "draft":
                raise exceptions.ValidationError("No se pueden eliminar planillas que no estén en estado Borrador")
        return super(PlanillaAdelantos,self).unlink()


    @api.onchange('name')
    def compute_user_id(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            i.user_id=self.env.user

    def button_confirmar(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            for j in i.line_ids:
                j.crear_novedad()
            i.write({'state':'done'})

    def button_cancelar(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            for n in i.line_ids:
                n.novedad_id.button_cancelar()
            i.write({'state':'cancel'})

    def button_draft(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            i.write({'state':'draft'})

    def default_name(self):
        # rrhh_novedades/models/planilla_adelantos.py
        return self.env['ir.sequence'].sudo().next_by_code('seq_planilla_adelanto')

    @api.depends('name','line_ids')
    @api.onchange('name')
    def agregar_empleados(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            employees=self.env['hr.employee'].sudo().search([('company_id','=',self.env.company.id)])
            new_lines=[]
            if not i.line_ids:
                for e in employees:
                    new_line={
                        'employee_id':e.id,
                    }
                    i.write({'line_ids':[(0,0,new_line)]})


class PlanillaAdelantosLine(models.Model):
    _name='rrhh_novedades.planilla_adelantos.line'
    _description="Linea de planilla"

    planilla_id=fields.Many2one("rrhh_novedades.planilla_adelantos")
    fecha=fields.Date(string="Fecha",related="planilla_id.fecha")
    
    
    employee_id=fields.Many2one("hr.employee",string="Empleado",required=True)
    monto=fields.Float(string="Monto telefono 1")
    monto2=fields.Float(string="Monto telefono 2")
    telefono1=fields.Char(string="Teléfono 1")
    telefono2=fields.Char(string="Teléfono 2")
    comentarios=fields.Char(string="Observaciones")
    neto_cobrar=fields.Float(string="Saldo actual",readonly=True)
    saldo_calculado=fields.Float(string="Saldo calculado",readonly=True)
    novedad_id=fields.Many2many("hr.novedades",string="Novedad")
    comision=fields.Float(string="Comision",compute="compute_comision")
    total_adelanto=fields.Float(string="Total",compute="compute_total")


    @api.depends('monto','monto2','comision')
    def compute_total(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            i.total_adelanto=i.monto+i.monto2+i.comision

    @api.depends('monto','monto2','planilla_id.tipo_id')
    def compute_comision(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            i.comision=(i.monto+i.monto2)*i.planilla_id.tipo_id.interes/100

    def compute_neto_cobrar(self):
        # rrhh_novedades/models/planilla_adelantos.py
        for i in self:
            if i.employee_id and i.fecha:
                nomina=self.env['hr.payslip'].search([('employee_id','=',i.employee_id.id),('state','=','verify')])
                if nomina:
                    nomina=nomina.filtered(lambda x:i.fecha>=x.date_from and i.fecha<=x.date_to)
                if nomina and len(nomina)==1:
                    nomina.compute_sheet()
                    i.write({'neto_cobrar':nomina.net_wage,'saldo_calculado':nomina.net_wage-(i.monto+i.monto2+i.comision)})
                    
                else:
                    i.write({'neto_cobrar':0,'saldo_calculado':0})
            else:
                    i.write({'neto_cobrar':0,'saldo_calculado':0})

    def crear_novedad(self):
        # rrhh_novedades/models/planilla_adelantos.py
        novedad={
            'employee_id':self.employee_id.id,
            'fecha':self.fecha,
            'monto':self.monto+self.monto2,
            'tipo_id':self.planilla_id.tipo_id.id,
            'comentarios':'%s - Telefonos: %s %s'%(self.comentarios or '',self.telefono1 or '',self.telefono2 or '')
        }
        if novedad.get('monto')>0:
            novedad_id=self.env['hr.novedades'].create(novedad)
            self.write({'novedad_id':[(4,novedad_id.id,0)]})
            if novedad_id:
                novedad_id.button_confirmar()

class ReporteVentasXlsx(models.AbstractModel):
    _name = 'report.rrhh_novedades.reporte_aqui_pago'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):
        # rrhh_novedades/models/planilla_adelantos.py
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
        
        lineas=datas.line_ids


        simpleWrite("Empleado",bold)
        rightAndWrite("Telefono 1",bold)
        rightAndWrite("Monto Telefono 1",bold)
        rightAndWrite("Telefono 2",bold)
        rightAndWrite("Monto Telefono 2",bold)
        rightAndWrite("Comisión",bold)
        rightAndWrite("Total",bold)
        total_general=0
        for linea in lineas:
            if (linea.monto + linea.monto2) >0:
                addSalto()
                simpleWrite(linea.employee_id.name if linea.employee_id else "")
                rightAndWrite(str(linea.telefono1)  if linea.telefono1 else "")
                rightAndWrite(linea.monto  if linea.monto else "",numerico)
                rightAndWrite(str(linea.telefono2)  if linea.telefono2 else "")
                rightAndWrite(linea.monto2  if linea.monto2 else "",numerico)
                monto1=linea.monto or 0
                monto2=linea.monto2 or 0
                comision=linea.comision or 0
                if comision==0:
                    comision=(monto1+monto2)*0.05
                rightAndWrite(comision,numerico)
                total=monto1+monto2+comision
                rightAndWrite(total,numerico)
                total_general=total_general+total
        breakAndWrite("Total general",bold)
        rightAndWrite("")
        rightAndWrite("")
        rightAndWrite("")
        rightAndWrite("")
        rightAndWrite("")
        rightAndWrite(total_general,numerico_total)

