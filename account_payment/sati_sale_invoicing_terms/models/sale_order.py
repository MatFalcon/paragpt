from odoo import models, fields, api , _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_term_ids = fields.One2many('sale.invoice.terms', 'sale_order_id', string='Invoice Terms')
    invoice_term_conditions_ids = fields.One2many('sale.invoice.terms.conditions', 'sale_order_id', string='Invoice Terms Conditions')
    invoice_term_conditions_qty = fields.Integer(compute='get_invoicing_terms_conditions_qtys')
    invoice_term_qty = fields.Integer(compute='get_invoicing_terms_conditions_qtys')
    allow_invoice_terms = fields.Boolean(string="Allow invoice terms?", default=True,tracking=True)
    generate_account_move = fields.Boolean(string="Genereate account move?",default=False,help="Tildar este campo en caso de que esta NP contenga un contrato",tracking=True)
    contract_file = fields.Binary(string='Contract file', attachment=True,tracking=True)
    contract_file_name = fields.Char(string='File name')
    bill_installments = fields.Boolean(string="Bill in installments",default=False,tracking=True)
    installment_qty = fields.Integer(string="Number of installments",tracking=True)
    installment_amount = fields.Float(string="Installment amount",tracking=True)

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = "Presupuesto-" + vals['name']

        return super(SaleOrder, self).create(vals_list)

    def generate_invoice_term_installments(self):
        invoice_term_model = self.env['sale.invoice.terms']
        next_invoice_date = fields.Date.today()

        for i in range(self.installment_qty):
            if i > 0:
                next_invoice_date += timedelta(days=30)  # Incrementar la fecha para las siguientes facturas

            vals = {
                'invoice_date': next_invoice_date,
                'invoice_amount': self.installment_amount,
                'sale_order_id': self.id
            }

            invoice_term_model.create(vals)

    @api.constrains('invoice_term_ids','allow_invoice_terms')
    def check_invoice_terms(self):
        check = True
        if not self._context.get('check_invoice_term'):
            check = False
        if check:
            if self.allow_invoice_terms and not self.bill_installments:
                if not self.invoice_term_ids:
                    raise ValidationError(_('Please specify the invoicing terms for this sale order'))
                # Verify if sum of totals for invoice_terms equals to sale order total
                sum_invoice_terms = sum(term.invoice_amount for term in self.invoice_term_ids)
                if sum_invoice_terms != self.amount_total:
                    raise ValidationError(_('The total amount of invoicing terms must be equal to sale order total'))

    def _create_invoices(self, grouped=False, final=False, date=None):
        # Llama al método original y almacena las facturas creadas
        created_invoices = super(SaleOrder, self)._create_invoices(grouped, final, date)

        # Obtener las líneas facturables
        invoiceable_lines = self._get_invoiceable_lines(final)

        # Verificar si el monto personalizado de la factura está en el contexto
        custom_invoice_amount = self._context.get('custom_invoice_amount')

        if custom_invoice_amount and invoiceable_lines:
            # Calcular el total de las líneas facturables
            total_amount = sum(line.price_subtotal for line in invoiceable_lines)
            if total_amount != custom_invoice_amount:
                # Ajustar el precio unitario o la cantidad de la última línea
                # para que el total de la factura coincida con custom_invoice_amount
                last_line = invoiceable_lines[-1]
                last_line.price_unit = custom_invoice_amount - (total_amount - last_line.price_subtotal)

        # Almacenamos las facturas creadas en el contexto para acceder a ellas más tarde
        self.env['sale.order'].env.context = self.env['sale.order'].env.context.copy()
        self.env['sale.order'].env.context['created_invoices'] = created_invoices.ids

        return created_invoices

    @api.depends('invoice_term_conditions_ids','invoice_term_ids')
    def get_invoicing_terms_conditions_qtys(self):
        for rec in self:
            rec.invoice_term_qty = len(rec.invoice_term_ids)
            rec.invoice_term_conditions_qty = len(rec.invoice_term_conditions_ids)
    def write(self, vals):
        # Verificar si el campo 'allow_invoice_term_ids' está presente en los valores actualizados
        if 'allow_invoice_terms' in vals:
            # Obtener el valor actual del campo 'allow_invoice_term_ids'
            allow_invoice_term_ids = vals.get('allow_invoice_terms')
            # Si el campo 'allow_invoice_term_ids' se desmarca
            if not allow_invoice_term_ids:
                # Eliminar los datos relacionados
                self.invoice_term_ids.unlink()
                self.invoice_term_conditions_ids.unlink()
        # Llamar al método write original
        return super(SaleOrder, self).write(vals)

    def create_account_provition_move(self):
        AccountMove = self.env['account.move']
        for order in self:
            if not order.company_id.contract_account_id or not order.company_id.provition_account_id or not order.company_id.provition_journal_id:
                raise UserError(_("Please set both contract and provision accounts in the settings."))
            for invoice_term in order.invoice_term_ids:  # Assuming invoice_term_ids field is present in sale.order
                if not invoice_term.provition_move_id:
                    analytic_account_id = order.analytic_account_id.id if order.analytic_account_id else False

                    # Calculate debit and credit based on exchange rate
                    currency = order.currency_id
                    date = fields.Date.today()
                    company_currency = order.company_id.currency_id
                    if currency and currency != company_currency:
                        amount_currency = invoice_term.invoice_amount
                        debit = credit = currency._convert(invoice_term.invoice_amount, company_currency,
                                                           order.company_id, date)
                    else:
                        amount_currency = 0
                        debit = credit = invoice_term.invoice_amount

                    move_vals = {
                        'ref': order.name + '/' + invoice_term.name,
                        'date': date,
                        'journal_id': order.company_id.provition_journal_id.id,
                        'line_ids': [(0, 0, {
                            'name': order.name + '/' + invoice_term.name,
                            'account_id': order.company_id.contract_account_id.id,
                            'debit': debit,
                            'credit': 0,
                            'amount_currency': amount_currency,
                            'currency_id': currency.id if currency and currency != company_currency else False,
                            'analytic_account_id': analytic_account_id,
                        }), (0, 0, {
                            'name': order.name + '/' + invoice_term.name,
                            'account_id': order.company_id.provition_account_id.id,
                            'debit': 0,
                            'credit': credit,
                            'amount_currency': -amount_currency,
                            'currency_id': currency.id if currency and currency != company_currency else False,
                            'analytic_account_id': analytic_account_id,
                        })],
                    }
                    move = AccountMove.create(move_vals)
                    move.post()
                    invoice_term.provition_move_id = move.id


    def action_confirm(self):
        # Iterate through invoice terms
        self.check_invoice_terms()
        for term in self.invoice_term_ids:
            if not term.invoice_term_condition_ids:
                raise ValidationError(_('The term %s has no conditions, please add at least one' % (term.name)))
            invoicing_term_users = self.env.ref('sati_sale_invoicing_terms.group_invoicing_term_notify_activity').users
            # Crea una actividad para cada usuario en invoicing_term_users
            for user in invoicing_term_users:
                self.env['mail.activity'].create({
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model']._get('sale.order').id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': f"Factura de {term.invoice_amount} programada",
                    'date_deadline': term.invoice_date,
                    'user_id': user.id,
                })
        if self.generate_account_move:
            self.create_account_provition_move()
        res = super(SaleOrder, self).action_confirm()
        return res
