from odoo import models,fields,api,exceptions


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_iso=fields.Boolean(string="Es ticket de ISO")
    iso_from_user_id=fields.Many2one('res.users',string="De")
    iso_procedencia=fields.Selection(string="Procedencia",selection=[('auditoria','Auditoria de calidad'),('hallazgo','Hallazgo personal'),('cliente','Observación del cliente')])
    iso_clasificacion=fields.Selection(string="Clasificación del hallazgo",selection=[('conformidad','Conformidad'),('no_conf_mayor','No conformidad mayor'),('no_conf_menor','No conformidad menor'),('observacion','Observación'),('mejora','Oportunidad de mejora')])
    iso_team_id=fields.Many2one('helpdesk.team',string="Ubicación")
    iso_descripcion=fields.Char(string="Descripción")
    iso_evidencia=fields.Char(string="Evidencia")
    iso_referencia=fields.Char("Referencia")
    iso_accion_inmediata=fields.Char("Acción inmediata")
    iso_evaluacion_causa=fields.Char(string="Evaluación de las causas")
    iso_acciones_correctivas=fields.Char(string="Acciones correctivas")
    iso_implementacion_accion=fields.Selection(string="Implementación de la acción correctiva",selection=[('SI','SI'),('NO','NO')])
    iso_evaluacion_efectividad=fields.Selection(string="Evaluación de la efectividad de las acciones tomadas",selection=[('Efectivo','Efectivo'),('No efectivo','No efectivo')])
    iso_cierre=fields.Selection(string="Cierre",selection=[('SI','SI'),('NO','NO')])
