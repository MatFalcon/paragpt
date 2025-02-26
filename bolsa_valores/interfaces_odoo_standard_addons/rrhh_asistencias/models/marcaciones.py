from odoo import fields, api, models, exceptions, _
import datetime, pytz, logging

_logger = logging.getLogger(__name__)


class Marcaciones(models.Model):
    _name = 'rrhh_asistencias.marcaciones'

    id_unico_marcacion = fields.Char()
    id_marcador = fields.Many2one('rrhh_asistencias.marcadores', string='Marcador')
    company_id = fields.Many2one('res.company', string='Compañía', compute='_set_company_id', store=True)
    id_marcacion = fields.Char(string='ID marcación')
    raw_fecha_hora = fields.Datetime(string="Raw fecha hora")
    fecha_hora = fields.Datetime(string="Raw fecha hora")
    fecha = fields.Date('Fecha')
    hora = fields.Float('Hora')
    asistencia_creada = fields.Boolean(string='Asistencia Creada', default=False)
    marcacion_procesada = fields.Boolean(string='Asistencia Procesada', default=False)
    comentario = fields.Char('Comentario', default='Marcación sin procesar')
    employee_id = fields.Many2one('hr.employee', string='Empleado', compute='_compute_employee_id', search='_search_employee_id')

    def _search_employee_id(self, operator, value):
        employees_id_marcacion = self.employee_id.search([('name', operator, value)]).mapped('id_marcacion')
        recs = self.search([('id_marcacion', 'in', employees_id_marcacion)])
        if recs:
            return [('id', 'in', recs.ids)]

    @api.depends('id_marcador.company_id')
    def _set_company_id(self):
        for this in self:
            this.company_id = this.id_marcador.company_id

    def _compute_employee_id(self):
        # rrhh_asistencias/models/marcaciones.py
        for this in self:
            employee_id = False
            try:
                if this.id_marcacion:
                    employee_id = self.env['hr.employee'].sudo().search([('id_marcacion', '=', int(this.id_marcacion))], limit=1)
                    if not employee_id:
                        employee_id = False
            except:
                employee_id = False
            finally:
                this.employee_id = employee_id

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        # rrhh_asistencias/models/marcaciones.py
        r = super(Marcaciones, self).create(vals_list)
        r.process_dates()
        return r

    def process_date(self, raw_fecha_hora=False):
        # rrhh_asistencias/models/marcaciones.py
        if self:
            raw_fecha_hora = self.raw_fecha_hora
        elif not raw_fecha_hora:
            return
            # raise exceptions.ValueError('Datos insuficientes para procesar la Marcación')
        fecha_hora_utc = pytz.timezone('UTC').localize(raw_fecha_hora)
        fecha_hora_real = fecha_hora_utc.astimezone(pytz.timezone('America/Asuncion'))

        fecha = fecha_hora_real.date()
        hora = fecha_hora_real.hour + fecha_hora_real.minute / 60
        if self:
            self.write({
                'fecha': fecha,
                'hora': hora,
                'fecha_hora': datetime.datetime.strptime(
                    datetime.datetime.strftime(raw_fecha_hora, '%Y-%m-%d %H:%M:%S'),
                    '%Y-%m-%d %H:%M:%S'
                )
            })
        return fecha, hora

    def process_dates(self):
        # rrhh_asistencias/models/marcaciones.py
        for this in self:
            this.process_date()

    def create_attendance(self, employee_id=False, fecha=False, hora=False):
        # rrhh_asistencias/models/marcaciones.py
        if self:
            employee_id = self.employee_id
            fecha = self.fecha
            hora = self.hora
            # _logger.info('Procesando marcación ' + self.id_unico_marcacion)

        if not (employee_id and fecha and hora):
            if self:
                self.write({
                    'comentario': 'No existe un empleado con el id de marcación',
                    'marcacion_procesada': True,
                })
            return
            # raise exceptions.ValueError('Datos insuficientes para procesar la Asistencia')

        asistencias = self.env['hr.attendance'].search([
            ('employee_id', '=', employee_id.id),
            ('date', '=', fecha)
        ])
        asistencias_modificadas = self.env['hr.attendance']
        open_contracts = employee_id.contract_ids.filtered(lambda x: x.state in ['open'])
        if not open_contracts:
            return
            # raise exceptions.ValidationError('El empleado no tiene definido un contrato activo')
        for contract in open_contracts:
            asistencia_fecha = asistencias.filtered(lambda x:
                                                    x.date == fecha and
                                                    x.contract_id == contract and
                                                    x.salida_marcada == False
                                                    )

            if not asistencia_fecha:
                asistencias_modificadas |= asistencia_fecha.create({
                    'employee_id': employee_id.id,
                    'contract_id': contract.id,
                    'date': fecha,
                    'entrada_marcada': hora,
                })
            else:
                asistencias_modificadas |= asistencia_fecha
                if asistencia_fecha.entrada_marcada < hora:
                    asistencia_fecha.write({
                        'salida_marcada': hora,
                    })
                else:
                    asistencia_fecha.write({
                        'salida_marcada': asistencia_fecha.entrada_marcada,
                        'entrada_marcada': hora,
                    })
            if self:
                self.write({
                    'comentario': 'Marcación procesada',
                    'marcacion_procesada': True,
                    'asistencia_creada': True
                })
        return asistencias_modificadas

    def create_attendances(self):
        # rrhh_asistencias/models/marcaciones.py
        for marcacion in self:
            marcacion.create_attendance()
            self._cr.commit()

    def reset_marcaciones(self):
        wizard_id = self.env['rrhh_asistencias.wizard_reset_marcaciones'].create({
            'marcaciones_ids': [(4, marcacion.id) for marcacion in self]
        })

        return {
            'name': _("Reprocesar Marcaciónes"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard_id._name,
            'res_id': wizard_id.id,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class WizardResetMarcaciones(models.TransientModel):
    _name = 'rrhh_asistencias.wizard_reset_marcaciones'

    marcaciones_ids = fields.Many2many('rrhh_asistencias.marcaciones', relation='wizard_reset_marcaciones_marcaciones_rel')
    marcaciones_ids_count = fields.Integer(string='Marcaciones a reprocesar', compute='_get_marcaciones_ids_count')

    def _get_marcaciones_ids_count(self):
        for this in self:
            this.marcaciones_ids_count = len(this.marcaciones_ids)

    def reset_marcaciones(self):
        self.marcaciones_ids.write({
            'marcacion_procesada': False,
            'asistencia_creada': False,
            'comentario': 'Marcación a reprocesar',
        })
