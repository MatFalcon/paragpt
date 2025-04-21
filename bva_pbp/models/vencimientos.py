from ast import literal_eval
from datetime import timedelta
import logging
from odoo import fields, models, api, exceptions
_logger = logging.getLogger(__name__)

class Vencimientos(models.Model):
    _name = "pbp.vencimiento_capital_interes"
    _description = "Vencimiento de Capital e Intereses"

    name = fields.Char(related="registros.serie")
    state = fields.Selection([('vencido', 'Vencido'), ('cobrado', 'Cobrado'), ('pendiente', 'Por Cobrar')],
                             default='pendiente')
    color = fields.Integer(compute="_compute_color", store=True)

    @api.depends('state')
    def _compute_color(self):
        for record in self:
            if record.state == 'cobrado':
                record.color = 10  # Verde
            elif record.state == 'vencido':
                record.color = 1  # Rojo
            elif record.state == 'pendiente':
                record.color = 3  # Amarillo
            else:
                record.color = 0

    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    dias = fields.Integer(string="Dias")
    interes = fields.Float(string="InteresxTitulo")
    total = fields.Float(string="Total a Cobrar")
    valor_actual_pyg = fields.Float(compute="_calculo_valor_actual_pyg_usd")
    valor_actual_usd = fields.Float(compute="_calculo_valor_actual_pyg_usd")



    saldo = fields.Float(string="Saldo Vencimiento", compute="_compute_saldo_vencimiento")
    amortizacion = fields.Selection(
        selection=[
            ('inicio', 'Inicio'),
            ('vtoInt', 'Vto.Interes'),
            ('pagocap', 'Pago de Capital'),
        ]
    )
    serie = fields.Char(related="registros.serie",store=True)
    registros = fields.Many2one('pbp.cartera_inversion', string="Capital e Intereses")
    destinatarios = fields.Many2many('res.users', string="Destinatarios")
    texto = fields.Html(string="Texto")
    email_to = fields.Char(string="Destinatarios")
    user_id = fields.Many2one(
        'res.users', string="Usuario", required=True, default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    voucher_id = fields.Many2one("account.voucher")
    # para la vista tree
    vouchers_ids = fields.One2many("account.voucher", "vencimiento_id", string="Vouchers Generados")
    partner_id = fields.Many2one('res.partner', string='Emisor', required=True, related="registros.partner_id",compute='_compute_casa_bolsa')
    casa_bolsa = fields.Many2one('res.partner', string='Casa de Bolsa', required=True,compute='_compute_casa_bolsa')
    currency_id = fields.Many2one('res.currency',string="Moneda", related="registros.currency_id",store=True)
    cuenta = fields.Many2one('account.account', string='Cuenta de devengamiento',
                             tracking=True, compute='_compute_cuenta'   )
    instrumento = fields.Selection(string="Instrumento", related="registros.instrumento",store=True)


    ##### Cuentas #########
    ########### CAMPOS PARA ASIENTO DE PAGO INICIAL ##################
    inversion_account_id = fields.Many2one('account.account', string="Cuenta de Inversión",
                                           tracking=True, related="registros.inversion_account_id", store=True)
    banco_account_id = fields.Many2one('account.account', string="Cuenta de Banco",
                                       tracking=True, related="registros.banco_account_id", store=True)
    inversion_journal_id = fields.Many2one('account.journal', string="Diario de inversión",
                                           tracking=True, related="registros.inversion_journal_id", store=True)
    ########### CAMPOS PARA ASIENTO INICIAL A DEVENGAR ################
    initial_credit_account_id = fields.Many2one('account.account', string='Cuenta acreedora inicial a devengar CP',
                                                tracking=True, related="registros.initial_credit_account_id", store=True)
    initial_credit_largo_plazo_account_id = fields.Many2one('account.account',
                                                            string='Cuenta acreedora inicial a devengar LP',
                                                            tracking=True, related="registros.initial_credit_largo_plazo_account_id", store=True)
    initial_debit_account_id = fields.Many2one('account.account', string='Cuenta deudora inicial a devengar CP',
                                               tracking=True, related="registros.initial_debit_account_id", store=True)
    initial_debit_account_id_lp = fields.Many2one('account.account', string='Cuenta deudora inicial a devengar LP',
                                                  tracking=True, related="registros.initial_debit_account_id_lp", store=True)
    initial_journal_id = fields.Many2one('account.journal', string="Diario de asiento a devengar",
                                         tracking=True, related="registros.initial_journal_id", store=True)
    # initial_move_ids = fields.One2many(
    #     'account.move',
    #     'initial_cartera_id',  # Campo inverso en `account.move`
    #     string="Asientos Iniciales",
    #     copy=False
    # )

    ########### CAMPOS PARA DEVENGAMIENTO ############################
    credit_account_id = fields.Many2one('account.account', string='Cuenta de ingresos',
                                        tracking=True, related="registros.credit_account_id")
    debit_account_id = fields.Many2one('account.account', string='Cuenta de devengamiento',
                                       tracking=True, related="registros.debit_account_id")
    # move_ids = fields.Many2one(
    #     'account.move',
    #     related="registros.move_ids",  # Campo inverso en `account.move`
    #     string="Asientos contables de devengamiento"
    # )
    move_count = fields.Integer(
        string="Cantidad de Asientos Contables",
        store=True
    )

    @api.depends("casa_bolsa", "partner_id")
    def _compute_casa_bolsa(self):
        #cuando el registro de cartera no tiene casa de bolsa
        #debe tomar como casa de bolsa el emisor
        for record in self:
            record.casa_bolsa = False
            if record.registros.casa_bolsa:
                record.casa_bolsa = record.registros.casa_bolsa
            else:
                record.casa_bolsa = record.registros.partner_id

            if record.registros.partner_id:
                record.partner_id = record.registros.partner_id



    @api.depends("cuenta")
    def _compute_cuenta(self):
        for record in self:
            record.cuenta = False
            if record.amortizacion == 'vtoInt':
                record.cuenta = record.registros.initial_debit_account_id.id
            else:# cuando es cobro de capital
                record.cuenta = record.registros.inversion_account_id



    @api.depends("saldo")
    def _compute_saldo_vencimiento(self):
        for record in self:
            total_vouchers = 0
            for voucher in record.vouchers_ids:
                total_vouchers += voucher.amount
            record.saldo = record.total - total_vouchers


    @api.depends("valor_actual_pyg", "valor_actual_usd")
    def _calculo_valor_actual_pyg_usd(self):
        _logger.info(f"_calculo_valor_actual_pyg_usd")
        for record in self:
            record.valor_actual_pyg = 0
            record.valor_actual_usd = 0
            if record.registros.cambio_utilizado and record.registros.cambio_utilizado > 0:
                if record.currency_id.id !=  155:# si es dolar
                    record.valor_actual_pyg = record.total * record.registros.cambio_utilizado
                    record.valor_actual_usd = record.total
                else:# si es guarani
                    record.valor_actual_usd = record.total / record.registros.cambio_utilizado
                    record.valor_actual_pyg = record.total
            else:
                record.valor_actual_pyg = record.total
                record.valor_actual_usd = 0

            #_logger.info(f"ID: {record.id}   PYG: {record.valor_actual_pyg } - USD: {record.valor_actual_usd}")

    def unlink(self):
        _logger.warning('self user %s', self.env.user.id)
        if self.env.user.id == 1:
            _logger.warning('self env user %s', self.env.user.id)
            raise exceptions.UserError("El usuario con ID 1 no puede eliminar registros.")
        return super(Vencimientos, self).unlink()

    def crear_voucher_parcial(self):
        nombre = f"{self.serie} - {self.fecha_vencimiento} - "
        if self.amortizacion == 'vtoInt':
            nombre += "Vencimiento Interes"
        else:
            nombre += "Vencimiento Capital"
        return {
            'type': 'ir.actions.act_window',
            'name': 'Abrir Wizard de Vouchers',
            'res_model': 'voucher.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_name': nombre,
                        'default_saldo': self.saldo,
                        'default_amount': self.saldo,
                        'default_vencimiento_id': self.id,
                        'default_cuenta':self.cuenta.id,
                        'default_partner_id': self.partner_id.id
                        },
        }

    def cambiar_estados_vencimientos(self):
        #cambiar tambien en el script para que actualice
        vencimientos = self.env["pbp.vencimiento_capital_interes"].search([('state', '=', 'pendiente')])
        _logger.warning(f"Accion planificada")

        for vencimiento in vencimientos:
            # validar si supero la fecha del vencimiento
            if vencimiento.fecha_vencimiento < fields.date.today():
                _logger.warning(f"Se cambio el vencimiento: {vencimiento.serie} - {vencimiento.fecha_vencimiento}")

                vencimiento.state = 'vencido'



"""@api.model
def getEmailData(self):
    texto = ""
    destinatarios = []

    fecha_vencimiento = fields.Date.today() + timedelta(days=1)
    group = self.env['res.groups'].search([('name', '=', 'Grupo PBP')])
    #Si el grupo existe, busca los usuarios que pertenecen a él
    if group:
        users = self.env['res.users'].search([('groups_id', 'in', group.ids)])
    #    for u in users:
    #        email_to = email_to + u.email + ','

    destinatarios.append(self.env.user.company_id.partner_id.id)

    registros = self.env['pbp.cartera_inversion'].search([('fecha_vencimiento','=',fecha_vencimiento)])

    if registros:
        partners = set(registros.mapped('partner_id'))
        for p in partners:
            texto = texto + '<b>' + p.name + '</b><br/>'
            texto = texto + '<table><tr><td style="border:1px solid black;padding:5px">Emisor</td><td style="border:1px solid black;padding:5px">Fecha de vencimiento</td><td style="border:1px solid black;padding:5px">Instrumento</td><td style="border:1px solid black;padding:5px">Monto Intereses</td><td style="border:1px solid black;padding:5px">Serie</td><td style="border:1px solid black;padding:5px">Moneda</td></tr>'
            for r in registros.filtered(lambda x: x.partner_id == p):
                texto = texto + '<tr><td style="border:1px solid black;padding:5px">' + r.partner_id.name +\
                        '</td><td style="border:1px solid black;padding:5px">'+ r.fecha_vencimiento.strftime("%d/%m/%Y") +\
                        '</td><td style="border:1px solid black;padding:5px">'+r.instrumento+\
                        '</td><td style="border:1px solid black;padding:5px">'+ str('{0:,.0f}'.format(r.intereses)).replace(",",".")+\
                        '</td><td style="border:1px solid black;padding:5px">'+r.serie + \
                        '</td><td style="border:1px solid black;padding:5px">'+r.currency_id.name + \
                        '</td></tr>'
            texto = texto + '</table>'

        registro_values = {
            'fecha_vencimiento':fecha_vencimiento,
            'destinatarios':[(6, 0, users.ids)],
            'registros': [(6, 0, registros.ids)],
            'texto':texto
        }

        vencimiento_capital_interes = self.env['pbp.vencimiento_capital_interes'].create(registro_values)

        template = self.env.ref('pbp.mail_template_vencimientos_capital_interes')

        vals = {
            'email_from': 'tesoreria@bolsadevalores.com.py',
            'author_id': self.user_id.id,
            'subject': 'Re: Vencimiento de Capital e Interes a fecha %s' % fecha_vencimiento,
            'auto_delete': False,
            'recipient_ids': destinatarios
        }
        mail_id = template.send_mail(vencimiento_capital_interes.id, email_values=vals, force_send=True)
        for r in registros:
            r.write({'correo_enviado': True, 'mail_id': mail_id})"""
