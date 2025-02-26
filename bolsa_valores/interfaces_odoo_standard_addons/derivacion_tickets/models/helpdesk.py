import datetime
from datetime import date
from odoo import api, fields, models


class Help_desk(models.Model):
    _inherit = 'helpdesk.ticket'

    derivar = fields.Many2one('helpdesk.team', string="Derivar a")
    historial_id = fields.One2many("derivacion_tickets.historial_ticket", 'ticket_id', string="Historial")
    asunto = fields.Char("Asunto")
    comentario = fields.Char("Comentario")
    dias = fields.Integer(string="Cantidad de dias")
    user_parent = fields.Many2one("res.users", string="Usuario anterior", compute="usuario_anterior", readonly=True)
    padre=fields.Integer("Padre")
    parent_id = fields.Many2one("helpdesk.ticket", string="Ticket padre")
    entregado = fields.Boolean("Entregado", default=False)
    rating_selection = fields.Selection(string="Calificacion", selection=[('satisfecho','Satisfecho'),('no_satisfecho','No satisfecho'),('insatisfecho','Muy insatisfecho')], compute="rating_compute")
    rating_valor_pivot = fields.Selection(string="Calificacion", selection=[('satisfecho','Satisfecho'),('no_satisfecho','No satisfecho'),('insatisfecho','Muy insatisfecho')])
    bandera = fields.Boolean(default=False)

    @api.depends('rating_ids')
    def rating_compute(self):
        for r in self:
            if r.rating_ids:
                for i in r.rating_ids:
                    if i.rating == 5:
                        r.rating_selection = 'satisfecho'
                        r.rating_valor_pivot = 'satisfecho'

                    elif i.rating == 3:
                        r.rating_selection = 'no_satisfecho'
                        r.rating_valor_pivot ='no_satisfecho'

                    elif i.rating == 1:
                        r.rating_selection = 'insatisfecho'
                        r.rating_valor_pivot ='insatisfecho'

                    else:
                        r.rating_selection = False
                        r.rating_valor_pivot = False
            else:
                r.rating_selection = False
                r.rating_valor_pivot = False
            

    def usuario_anterior(self):
        for r in self:
            if r.parent_id != False:
                r.user_parent = r.parent_id.user_id.id

    #hace con Date no datetime, y ver como pasear de datetime a date
    def calcular_dias(self):
        for r in self:
            present = fields.Datetime.today()
            days = abs((present - r.create_date).days)
            if r.stage_id != self.env.ref("derivacion_tickets.resuelto3") and not r.bandera: 
                r.dias = days
            elif r.stage_id == self.env.ref("derivacion_tickets.resuelto3") and not r.bandera:
                r.dias = days
                r.bandera = True
            r.onchange_dias()
            

    

    def write(self, vals):
        for r in self:
            result = super(Help_desk,r).write(vals)

            if vals.get('derivar'):
                r.derivar_tickets()
            
            if vals.get('entregado') == True:
                state = self.env.ref('derivacion_tickets.resuelto3')
                r.write({'stage_id':state.id})
                r.onchange_stage()
            elif vals.get('entregado') == False:
                state = self.env.ref('derivacion_tickets.en_proceso2')
                r.write({'stage_id':state.id})
                r.onchange_stage()

            return result

    def derivar_tickets(self):
        ticket = self.env['helpdesk.ticket'].create({'team_id':self.derivar.id,'name':self.asunto,  'stage_id':self.env.ref('derivacion_tickets.nuevo1').id ,'priority':self.priority, 'tag_ids':self.tag_ids ,'description':self.description ,'partner_id':self.partner_id.id, 'ticket_type_id':self.ticket_type_id.id, 'padre':self.id, 'parent_id': self.id })
        ir_attachment_ids = self.env['ir.attachment'].search([( 'res_id','=', self.id),('res_model','=','helpdesk.ticket')])
        for r in ir_attachment_ids:
            attachment = r.copy()
            attachment.res_id = ticket.id
        historial = self.env['derivacion_tickets.historial_ticket'].create({'name':ticket.id, 'estado':ticket.stage_id.name, 'dias':ticket.dias ,'asunto':ticket.name, 'user_id':ticket.user_id.id, 'canal':self.derivar.id, 'ticket_id':self.id, 'ticket':ticket.id, 'comentario':self.comentario})
        self.actualizar_historial(historial)
        self.derivar = False

    def actualizar_historial(self,historial):
        parent_id = self.padre
        name = historial.name
        user_id = historial.user_id
        canal = historial.canal
        asunto = historial.asunto
        ticket = historial.ticket
        comentario = historial.comentario
        estado = historial.estado
        dias = historial.dias
        while parent_id != 0 :
            ticket_padre = self.env['helpdesk.ticket'].search([('id', '=', parent_id)])
            
            if ticket_padre:
                ticket_padre.env['derivacion_tickets.historial_ticket'].create({'name':name,  'estado':estado, 'dias':dias, 'comentario':comentario ,'asunto':asunto ,'user_id':user_id.id, 'canal':canal.id, 'ticket_id':ticket_padre.id, 'ticket':ticket.id})
                parent_id = ticket_padre.padre

    @api.depends('stage_id')
    @api.onchange('stage_id')
    def onchange_stage(self):
        parent_id = self.parent_id
        id = self.concatenar(self.id)
        while parent_id:
            historial = self.env['derivacion_tickets.historial_ticket'].search([('name','=',id)])
            for r in historial:
                r.write( { 'estado':self.stage_id.name } )
            parent_id = parent_id.parent_id
            

    @api.depends('dias')
    @api.onchange('dias')
    def onchange_dias(self):
        parent_id = self.parent_id
        id = self.concatenar(self.id)
        while parent_id:
            historial = self.env['derivacion_tickets.historial_ticket'].search([('name','=',id)])
            for r in historial:
                r.write( { 'dias':self.dias } )
            parent_id = parent_id.parent_id

    @api.depends('user_id')
    @api.onchange('user_id')
    def onchange_user_id(self):
        parent_id = self.parent_id
        id = self.concatenar(self.id)
        while parent_id:
            historial = self.env['derivacion_tickets.historial_ticket'].search([('name','=',id)])
            for r in historial:
                r.write( { 'user_id':self.user_id } )
            parent_id = parent_id.parent_id


    def concatenar(self,idd):
        name = str(idd)
        id=''
        for r in name:
            if r in ['0','1','2','3','4','5','6','7','8','9']:
               id=id+r 
        return int(id)
    
    def marcar_entregado(self):
        self.ensure_one()
        self.entregado = True
        if self.parent_id and self.parent_id.user_id:
            self.crear_actividad_ticket()
    
    def marcar_no_entregado(self):
        self.ensure_one()
        self.entregado = False 

    def crear_actividad_ticket(self):
        parent_id = self.env['helpdesk.ticket'].search([('id', '=', self.padre)])
        values = {
            'res_model_id':self.env.ref('helpdesk.model_helpdesk_ticket').id,
            'user_id':parent_id.user_id.id, 
            'res_id':parent_id.id,
            'date_deadline':fields.Date.today(),
            'summary':"Ticket Entregado"
        }
        actividad = self.env['mail.activity'].create(values)
        #self.enviar_email()

    def assign_ticket_to_self(self):
        self.ensure_one()
        self.user_id = self.env.user
        self.onchange_user_id()
    
    #def enviar_email(self):
    #    template_id = self.env.ref('crm_rural.email_ticket_entregado').id
    #    self.env['mail.template'].browse(template_id).send_mail(self.id,force_send=True)



    class Historial_ticket(models.Model):
        _name="derivacion_tickets.historial_ticket"
        _description = "Historial de ticket"
        
        asunto = fields.Char(string="Asunto")
        name = fields.Integer("Numero del ticket nuevo" )
        user_id = fields.Many2one("res.users", string="Oficial")
        canal = fields.Many2one('helpdesk.team', string="Derivado a")
        ticket_id = fields.Many2one("helpdesk.ticket")
        
        ticket = fields.Many2one('helpdesk.ticket', string="Ticket")
        comentario = fields.Char('Comentario')

        estado = fields.Char(string="Estado")
        dias = fields.Integer(string="Dias contados")