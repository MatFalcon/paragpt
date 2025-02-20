# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from odoo.exceptions import ValidationError
from odoo.tools import email_split
from datetime import datetime, timedelta
from smtplib import SMTPException
from requests.exceptions import RequestException, ConnectionError
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from lxml import etree
import smtplib
import logging
import pytz

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    presale_order_item_id = fields.Many2one('presale.order.item', string="Item de preventa")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    es_preventa = fields.Boolean()
    ocultar_lineas_productos = fields.Boolean()
    product_temporal_line = fields.One2many("sale.order.line.temporal", "sale_order_id")
    presale_id = fields.Many2one('presale.order', string="Preventa Asociada")
    purchase_request_ids = fields.One2many('purchase.request', 'sale_order_id')

    def generate_analytic_account(self):
        analytic_account_vals = {
            'name': self.name + "-" + self.opportunity_id.name + "-" + self.opportunity_id.code,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'company_id': self.company_id.id,
            'plan_id': 1 # PLan analitica de proyectos, por el momento lo especificamos de manera manual por ID
        }
        analytic_account = self.env['account.analytic.account'].create(analytic_account_vals)
        self.analytic_account_id = analytic_account.id

    def action_confirm(self):
        # Recorremos las líneas de la orden de venta
        if self.opportunity_id:
            for line in self.order_line:
                presale_item = line.presale_order_item_id
                if presale_item and presale_item.detail_ids:
                    # Generar las solicitudes de compra para el producto relacionado
                    self._generate_purchase_from_presale_item(presale_item, line)
            stage_ganado = self.env['crm.stage'].search([('name', '=', 'Ganado')])[0]
            self.opportunity_id.stage_id = stage_ganado
            self.generate_analytic_account()
        super(SaleOrder, self).action_confirm()

    def _generate_purchase_from_presale_item(self, presale_item, line):
        """
        Generar una lista de materiales (BOM) basada en los detalles del presale.order.item
        """
        purchase_request_obj = self.env['purchase.request']
        purchase_request_line_obj = self.env['purchase.request.line']

        # Crear la cabecera de la solicitud de compra
        purchase = purchase_request_obj.sudo().create({
            'requested_by': presale_item.presale_order_id.commercials_ids[0].id,
            'sale_order_id': self.id
        })

        if presale_item.imprevisto == 'fabricacion':
            # Crear las líneas de la lista de materiales
            for detail in presale_item.detail_ids:
                purchase_request_line_obj.create({
                    'request_id': purchase.id,
                    'product_id': detail.product_id.id,
                    'product_qty': detail.qty,
                    'product_uom_id': detail.uom_id.id,
                })
        else:
            purchase_request_line_obj.create({
                'request_id': purchase.id,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
            })


# lineas de la orden de venta con los items
class SaleOrderLineTemporal(models.Model):
    _name = "sale.order.line.temporal"

    sale_order_id = fields.Many2one("sale.order", string="Orden de Venta", ondelete="cascade")
    product_temp_id = fields.Many2one("preventa.producto.temporal")

    qty = fields.Float()
    precio_unitario = fields.Float(string='Precio Unitario')


# lista de materiales
class MrpBom(models.Model):
    _inherit = "mrp.bom"

    producto_temporal_id = fields.Many2one("preventa.producto.temporal")


# producto temporal
class PreventaProductoTemporal(models.Model):
    _name = 'preventa.producto.temporal'
    _description = 'Producto Temporal para Preventas'

    name = fields.Char(string='Nombre del Producto', required=True)
    descripcion = fields.Text(string='Descripción')
    precio_unitario = fields.Float(string='Precio Unitario')
    # producto de la preventa
    product_preventa_id = fields.Many2one('presale.order.item', string='Preventa', required=True)
    # para ficha de producto
    detailed_type = fields.Selection(
        [('consu', 'Consumible'),
         ('servicio', 'Servicio'),
         ('product', 'Producto Almacenable')]
    )
    categ_id = fields.Many2one("product_category")
    uom_id = fields.Many2one('uom.uom', string="Uom", tracking=True, copy=True)


# preventa principal
class PreSaleOrder(models.Model):
    _name = 'presale.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True, copy=True)

    # ----- Item Detalle -----
    item_presale_ids = fields.One2many("presale.order.item", "presale_order_id", string="Item Preventa")
    aplicar_descuento = fields.Boolean(string="Aplicar descuento")
    valor_descuento = fields.Float(string="% descuento")

    def aprobar_preventa(self):
        presupuesto_lineas = []
        for item in self.item_presale_ids:
            if item.imprevisto == "fabricacion":
                if self.aplicar_descuento:
                    precio_unitario = item.precio_unit_dcto
                else:
                    precio_unitario = item.precio_venta_margen_unit
                # Crear producto temporal
                producto_temporal = self.env['product.product'].create({
                    'name': item.name,
                    'list_price': precio_unitario,
                    'categ_id': item.categ_id.id,
                    'uom_id': item.uom_id.id,
                    'detailed_type': item.detailed_type,
                })
                item.product_id = producto_temporal
            else:
                producto_temporal = item.product_id
                if self.aplicar_descuento:
                    precio_unitario = item.precio_unit_dcto
                else:
                    precio_unitario = item.precio_venta_margen_unit
            # Agrega línea al presupuesto como sale.order.line
            presupuesto_lineas.append((0, 0, {
                'product_id': producto_temporal.id,  # Relacionado con product.product
                'product_uom_qty': item.qty,  # Cantidad
                'price_unit': precio_unitario,  # Precio unitario
                'name': item.name,  # Descripción del producto
                'presale_order_item_id': item.id,  # Relacion entre linea de pedido de venta e item de preventa
                'image_128': item.image_128 if item.image_128 else False
            }))

        if presupuesto_lineas:
            orden_venta_vals = {
                'partner_id': self.partner_id.id,
                'date_order': fields.Datetime.now(),
                'origin': self.name,
                'es_preventa': True,
                'presale_id': self.id,
                'order_line': presupuesto_lineas,  # Se cambió a 'order_line'
            }
            _logger.info("Valores de orden de venta: %s", orden_venta_vals)
            orden_venta = self.env["sale.order"].create(orden_venta_vals)
            self.sales_order_id = orden_venta
            return orden_venta
        else:
            raise ValidationError('Ocurrio un error al generar el presupuesto')

    # currency_id = fields.Many2one('res.currency',string=226"Team currency",related='team_id.presale_currency_id')
    currency_id = fields.Many2one('res.currency', string="Team currency", copy=True)
    rate = fields.Float(name="Project rate", tracking=True, copy=True)
    heading_ids = fields.One2many('presale.order.heading', 'order_id', string="Items", copy=True)
    order_ids = fields.One2many('sale.order', 'presale_id', copy=True)

    state = fields.Selection([('Borrador', 'Borrador'), ('Aprobado', 'Aprobado')], string="State", default="Borrador",
                             tracking=True, copy=True)
    partner_id = fields.Many2one('res.partner', 'Partner', tracking=True, copy=True)
    date = fields.Date(string="End date", tracking=True, copy=True)
    income_date = fields.Date(string="Income date", tracking=True, copy=True)
    commercials_ids = fields.Many2many('res.users', string='Commercial', tracking=True, copy=True,
                                       relation='presale_order_designer_rel')
    designers_ids = fields.Many2many('res.users', string='Designer', tracking=True, copy=True,
                                     relation='presale_order_user_rel')
    team_id = fields.Many2one('crm.team', 'Sale team', tracking=True, copy=True)

    sales_order_id = fields.Many2one('sale.order', string="Sales orders", tracking=True, copy=True)
    create_or_update = fields.Boolean(string="Create Sale Order (No/Yes)",
                                      help="One tip: if the 'Create Sales Order' check button is gray it means 'No', if it is blue it means 'yes'",
                                      tracking=True, copy=True)
    lead_id = fields.Many2one('crm.lead', string="Associate Opportunity", tracking=True, copy=True)
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist", tracking=True, copy=True)

    require_discount = fields.Boolean(string="Requires Discount", tracking=True, copy=True)
    discount_over_total = fields.Float(string="Discount O/ Total", tracking=True, copy=True)
    company_currency = fields.Boolean(string="Quote with Sales Team Currency", default=False, tracking=True, copy=True)
    rate_date = fields.Date(string="Rate date", tracking=True, copy=True)
    convert_currency = fields.Boolean(string="Convert Currency No/Yes", tracking=True, copy=True)

    aux_labor_table_ids = fields.One2many('presale.auxiliary_labor_table', 'order_id_aux', string="Personnel",
                                          tracking=True, copy=True)

    labor_qty_daily = fields.Float(string="qty", compute="calculate_daily_monthly", store=True, copy=True)
    labor_cost_daily = fields.Float(string="total cost", compute="calculate_daily_monthly", store=True, copy=True)
    overtime_sub_daily_one = fields.Float(string="subtotal", compute="  calculate_daily_monthly", store=True, copy=True)
    overtime_sub_daily_two = fields.Float(string="subtotal", compute="calculate_daily_monthly", store=True, copy=True)

    labor_cost_monthly = fields.Float(string="total cost", compute="calculate_daily_monthly", store=True, copy=True)
    overtime_sub_monthly_one = fields.Float(string="subtotal", compute="calculate_daily_monthly", store=True, copy=True)
    overtime_sub_monthly_two = fields.Float(string="subtotal", compute="calculate_daily_monthly", store=True, copy=True)

    logistic_summary_id = fields.One2many('presale.logistic_summary', 'order_id_log', string="Logistic", tracking=True,
                                          copy=True)

    fuel_type = fields.Many2one('presale.fuel_type', string="Fuel Type", tracking=True, copy=True)
    transfers = fields.Float(string="Transfers", tracking=True, copy=True)
    consumption_till_work = fields.Float(strig="Consumption to WORK (round trip)", compute="calculate_transfer",
                                         store=True)
    price_per_liter = fields.Float(string="Price per Liter", tracking=True, copy=True)
    price_per_tour = fields.Float(string="Price per Tour", compute="calculate_transfer", store=True, copy=True)
    total_price_per_tour = fields.Float(string="Total Price per Tour", compute="calculate_transfer", store=True,
                                        copy=True)
    toll = fields.Float(string="Toll", tracking=True, copy=True)
    total_transfer_amount = fields.Float(string="Total Transfer Amount", compute="calculate_transfer", store=True,
                                         copy=True)

    summary_estimated_time = fields.Float(string="Estimated Time (P/ Month", compute="calculate_total_summary",
                                          store=True, copy=True)  # compute
    summary_logistic = fields.Float(string="Logistic", compute="calculate_total_summary", copy=True)
    total_summary_amount = fields.Float(string="Total Amount", compute="calculate_total_summary", copy=True)

    net_total_cost = fields.Float(string="Net Total Costs", compute="calculate_net_total_costs", store=True, copy=True)
    total_labour = fields.Float(string="Labour", compute="calculate_net_total_costs", store=True, tracking=True,
                                copy=True)
    total_materials = fields.Float(string="Materials", compute="calculate_net_total_costs", store=True, tracking=True,
                                   copy=True)
    vat_credit_materials = fields.Float(string="VAT Credit Materials", compute="calculate_net_total_costs", store=True,
                                        copy=True)

    others_costs = fields.Float(string="Others Costs", compute="calculate_net_total_costs", store=True, copy=True)
    gen_grand_total_costs = fields.Float(string="Costos Generales", compute="calculate_net_total_costs", store=True,
                                         copy=True)
    financial_interest_costs = fields.Float("Financial Interest", placeholder="%", tracking=True, copy=True)

    hundred_perc_unforseen = fields.Float(string="Unforeseen (100% of the cost)", compute="calculate_net_total_costs",
                                          store=True, copy=True)
    hundred_perc_unforseen_perc = fields.Float(string="%", tracking=True, copy=True)
    financial_interest = fields.Float(string="Financial Interest", compute="calculate_net_total_costs", store=True,
                                      copy=True)
    financial_interest_perc = fields.Float(string="Financial I  nterest", tracking=True, copy=True)
    financial_interest_perc_default = fields.Float(string="%", tracking=True, copy=True)
    tools_fixed_expenses = fields.Float(string="Tools/Fixed Expenses", compute="calculate_net_total_costs", store=True,
                                        copy=True)
    tools_fixed_expenses_perc = fields.Float(string="Tools/Fixed Expenses %", tracking=True, copy=True)
    minor_materials = fields.Float(string="Minor Materials (from 100% of material cost)",
                                   compute="calculate_net_total_costs", store=True, copy=True)
    minor_materials_perc = fields.Float(string="%", compute="get_minor_material_perc_average", store=True, copy=True)

    price_vat_included = fields.Float(string="Price VAT Included", compute="calculate_price_vat_included", store=True,
                                      copy=True)
    vat_ten_percent = fields.Float(string="VAT 10%", compute="calculate_commisions", store=True, copy=True)
    price_without_vat = fields.Float(string="Price w/o VAT", compute="calculate_commisions", store=True, copy=True)
    commission_sf_av = fields.Float(string="Commission SF/AV", compute="calculate_commisions", store=True, copy=True)
    commission_sf_av_perc = fields.Float(string="Commission SF/AV %", tracking=True, copy=True)
    comm_sf_av_whithout_vat = fields.Float(string="Commision SF/AV w/o VAT", compute="calculate_commisions", store=True,
                                           copy=True)
    external_commission = fields.Float(string="External Commision", compute="calculate_commisions", store=True,
                                       copy=True)
    external_commission_per = fields.Float(string="External Commision %", tracking=True, copy=True)
    external_comm_without_vat = fields.Float(string="External Commission w/o VAT", compute="calculate_commisions",
                                             store=True, copy=True)
    gross_contribution = fields.Float(string="Gross Contribution", compute="calculate_commisions", store=True,
                                      copy=True)
    business_income_tax = fields.Float(string="BIT", compute="calculate_commisions", store=True, copy=True)  # IRE
    business_income_tax_per = fields.Float(string="BIT %", tracking=True, copy=True)  # IRE
    total_expenses = fields.Float(string="Total Expenses", compute="calculate_commisions", store=True, copy=True)
    contributions = fields.Float(string="Contribution", compute="calculate_commisions", store=True, copy=True)

    material_mv_trans_perc = fields.Float(
        string="Materials for = Medium Voltage, Generator Group and Transformer (MT-GG)", tracking=True, copy=True)
    material_installation_perc = fields.Float(string="Materials for low voltage electrical installations",
                                              tracking=True, copy=True)
    labor_bt = fields.Float(string="Labor in BT", tracking=True, copy=True)
    labor_mt = fields.Float(string="Labor in MT", tracking=True, copy=True)
    cabling_perc = fields.Float(string="Artifacts", tracking=True, copy=True)
    transformers_generator_perc = fields.Float(string="Transformers and Generators", tracking=True, copy=True)

    payment_term_ids = fields.Many2one('account.payment.term', string="Payment Term", tracking=True, copy=True)
    project_manager = fields.Many2many('res.users', string="Project Manager", tracking=True, copy=True,
                                       relation='presale_order_projectmanager_rel')
    distance_to_work = fields.Float(string="Distance to Work (km)", tracking=True, copy=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Mobile", tracking=True, copy=True)
    consumption_per_liter = fields.Float(string="Consumption per Km", compute="set_consumption_value", store=True,
                                         copy=True)

    qty_month = fields.Float(string="Qty. Months", compute="get_expected_months", store=True, copy=True)
    expected_month = fields.Float(string="Expected Months", compute="get_expected_months", store=True, copy=True)
    journeys = fields.Float(string="Journeys", compute="get_expected_months", store=True, copy=True)
    total_estimated_time = fields.Float(string="Total Estimated Time", compute="get_expected_months", store=True,
                                        copy=True)

    employer_contribution = fields.Float(string="Employer Contribution", tracking=True, copy=True)
    ips_per_month = fields.Float(string="Per Month", compute="get_ips_calculus", store=True, copy=True)
    ips_estimated_time = fields.Float(string="Estimated Time", compute="get_ips_calculus", store=True, copy=True)
    total_ips = fields.Float(string="Total IPS", compute="get_ips_calculus", store=True, copy=True)
    additionals_id = fields.One2many('presale.additionals', 'order_id_add', string="Additionals", tracking=True,
                                     copy=True)

    cost_percent = fields.Float(string="Of Costs", compute="calculate_cost_and_sp", store=True, copy=True)
    sale_price_percent = fields.Float(string="Of Sale Price", compute="calculate_cost_and_sp", store=True, copy=True)
    exclusions = fields.Html(string="Exclusions", tracking=True, copy=True)
    observations = fields.Html(string="Observations", tracking=True, copy=True)
    previous_state = fields.Selection([('Borrador', 'Borrador'), ('Aprobado', 'Aprobado')], string="State",
                                      default="Borrador", tracking=True, copy=True)

    type_heading = fields.Many2one('presale.type_headings', 'Rubros', tracking=True, copy=True)
    budget_sequence = fields.Char(string="Budget Number", copy=True)
    num_of_revs_commercial = fields.Integer(string="Number of Revisions of Commercial Team", copy=True)
    num_of_revs_technical = fields.Integer(string="Number of Revisions of Technical Area", copy=True)
    presale_full_nomenclature = fields.Char(string="Full Nomenclature", compute="set_presale_review_nomenclature",
                                            store=True, copy=True)
    type_labor_proration = fields.Selection([('Porcentaje', 'Porcentaje'), ('Monto', 'Monto')],
                                            string="Type of Proration", default="Porcentaje", tracking=True, copy=True)
    labor_per_floor_ids = fields.One2many('presale.auxiliary_calculation_per_floor', 'floor_order_id',
                                          string="Labour P/ Floor", copy=True)

    # ----- Total off for Proration Chart -----
    material_total_cost = fields.Float(string="Material Total Cost", compute="calculate_headings", store=True,
                                       copy=True)
    total_minor_materials = fields.Float(string="Total Minor Materials", compute="calculate_headings", store=True,
                                         copy=True)
    total_heading_proration = fields.Float(string="Total", compute="calculate_headings", store=True, copy=True)

    # ----- Exercise Chart -----
    total_mat_for_labour = fields.Float(string="Total Materials- For Labours", copy=True)
    bt_matl_wo_mm = fields.Float(string="BT materials (without MM)", copy=True)
    bt_labour = fields.Float(string="Labour BT", compute="calculate_exercise_chart", store=True, copy=True)
    only_labour = fields.Float(string="Labor Only Category", compute="calculate_exercise_chart", store=True, copy=True)
    diff_prorated_mat = fields.Float(string="Difference to be Prorated in Materials",
                                     compute="calculate_exercise_chart", store=True, copy=True)
    incidents_in_materials = fields.Float(string="Incidents in Materials", compute="calculate_exercise_chart",
                                          store=True, copy=True)
    # mont_artif_disassm = fields.Float(string="Mont. of Artifacts/Disassembly") # compute="get_proration_percentage", store=True

    labor_used_ids = fields.One2many('presale.labor_used', 'presale_labor_ids', string="Labour P/ Floor", copy=True)
    total_worked_days = fields.Float(string="Total Worked Days", compute="get_total_work_days_month", store=True,
                                     copy=True)
    month_of_works = fields.Float(string="Month of Work", compute="get_total_work_days_month", store=True, copy=True)
    laborer_summary_ids = fields.One2many('presale.auxiliary_summary_laborer', 'presale_labor_summary_ids',
                                          string="Labour P/ Floor", copy=True)
    create_update = fields.Selection([('crear', 'Crear'), ('actualizar', 'Actualizar')], string="Action to apply",
                                     default="crear", tracking=True, copy=True)

    mt_labour_summary_edit = fields.Float(string="MT Labour", copy=True)
    vat_mt_labour_summary_edit = fields.Float(string="IVA Mano de obra MT", compute="calculate_commisions", store=True,
                                              copy=True)
    vat_credit_other_costs = fields.Float(string="IVA Credito 10%", compute="calculate_commisions", store=True,
                                          copy=True)

    proportional_bonus = fields.Float(string="Proportional Bonus", compute="calculate_total_summary", store=True)
    grand_total_material = fields.Float(string="Grand total of materials", compute="calculate_total_summary",
                                        store=True)

    approving_signature = fields.Binary(string="Approving Signature", tracking=True)
    approving_signature_two = fields.Binary(string="Approving Signature", tracking=True)

    vat_other_costs = fields.Float(string="IVA Otros Costos", compute="calculate_net_total_costs", store=True)

    transfers_ids = fields.One2many('presale.transfers', 'transfers_order_id', string="Items", copy=True)
    total_con_descuento = fields.Float(string="Total con descuento", compute="calc_totales", store=True, readonly=True)
    total_sin_descuento = fields.Float(string="Total sin descuento", compute="calc_totales", store=True, readonly=True)
    margen_promedio = fields.Float(string="Margen promedio", compute="calc_totales", store=True, readonly=True)

    def aplicar_descuento_preventa(self):
        for record in self:
            for item in record.item_presale_ids:
                item.porcentaje_descuento = record.valor_descuento
                item._compute_costos_unitarios()
                item._compute_precios_venta()

    @api.depends('item_presale_ids.total_con_descuento', 'item_presale_ids.total_sin_descuento',
                 'item_presale_ids.margen_porcentaje_con_descuento')
    def calc_totales(self):
        for record in self:
            record.total_con_descuento = sum(item.total_con_descuento for item in record.item_presale_ids)
            record.total_sin_descuento = sum(item.total_sin_descuento for item in record.item_presale_ids)
            margen_values = [item.margen_porcentaje_con_descuento for item in record.item_presale_ids if
                             item.margen_porcentaje_con_descuento is not None]
            record.margen_promedio = (sum(margen_values) / len(margen_values) * 100) if margen_values else 0

    def request_validation(self):
        # Recorremos las líneas de la orden de venta
        stage_a_validar = self.env['crm.stage'].search([('name', '=', 'Cotizador a validar')])[0]
        self.lead_id.write({
            'stage_id': stage_a_validar.id
        })
        super(PreSaleOrder, self).request_validation()

    @api.model
    def create(self, vals):
        vals['budget_sequence'] = self.env['ir.sequence'].next_by_code('presale.order')
        return super(PreSaleOrder, self).create(vals)

    def assign_draft(self):
        for rec in self:
            rec.previous_state = 'Aprobado'
            rec.write({'state': 'Borrador'})
            current_state = 'Borrador'
            self.send_notification(rec.previous_state, current_state)

    # def assign_review(self):
    #     for rec in self:
    #         rec.previous_state = rec.state
    #         rec.write({'state': 'Revision'})
    #         current_state = 'Revision'
    #         self.send_notification(rec.previous_state, current_state)

    def assign_internal_approval(self):
        for rec in self:
            rec.previous_state = rec.state
            rec.sudo().write({'state': 'Aprobado'})
            stage_presupuesto_clientes = self.env['crm.stage'].search([('name', '=', 'Presupuestos para clientes')])[0]
            rec.lead_id.stage_id = stage_presupuesto_clientes
            current_state = 'Aprobado'
            self.send_notification(rec.previous_state, current_state)
            rec.aprobar_preventa()

    def get_time_by_datetime(self, current_hour):
        if current_hour < 5:
            part_of_day = "Buenas noches"
        elif current_hour < 12:
            part_of_day = "Buenos días"
        elif current_hour < 19:
            part_of_day = "Buenas tardes"
        else:
            part_of_day = "Buenas noches"
        return part_of_day

    def send_notification(self, previous_state, current_state):
        # try:
        subject = f'Pase de estapa {previous_state} a {current_state}'
        followers = self.env['mail.followers'].search([('res_model', '=', 'presale.order'), ('res_id', '=', self.id)])
        current_hour = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), "%H")
        for foll in followers:
            print(f"[FOLL:] {foll.partner_id.name}, [TARGET:] {current_state}")
            partner_email = email_split(foll.partner_id.email)
            if partner_email:
                partner_email = partner_email[0]
                current_hour = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), "%H")

                body = f"{self.get_time_by_datetime(int(current_hour))}  estimado/a {foll.partner_id.name},\n\nle informarmos que la cotización {self.name} pasó de la etapa de {previous_state} a la etapa de {current_state}."
                mail_send = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': partner_email,
                    'auto_delete': True,
                })
                try:
                    print("[ENTRA EN ESTA PARTE]")
                    mail_send.send()
                    sent_mail = self.env['mail.mail'].search([('id', '=', mail_send.id)])
                    print(f"[ESTADO-MENSAJE:] {sent_mail.state}")
                    if sent_mail.state == 'sent':
                        self.message_post(body="Notificación enviada satisfactoriamente!", message_type='notification')
                    elif sent_mail.state in ('exception', 'canceled'):
                        print("Error al enviar el correo.")
                        message_log = f"EL servicio de notificaciones presentó el siguiente inconveniente: {sent_mail.failure_reason}"
                        self.message_post(body=message_log, message_type='notification')
                    else:
                        print("Estado de correo desconocido.")
                        self.message_post(body="Estado de correo desconocido", message_type='notification')

                except Exception as exc:
                    self.message_post(body=exc, message_type='notification')  # subtype_xmlid='mail.mt_comment'
                except smtplib.SMTPSenderRefused as smtp_error:
                    error_message = f"Error al enviar el correo: {smtp_error}"
                    self.message_post(body=error_message, message_type='notification')
                except MailDeliveryException as mail_error:
                    error_message = f"Error al entregar el correo: {mail_error}"
                    self.message_post(body=error_message, message_type='notification')

                # except SMTPException as mail_error:
                #     print("[ENTRA EN ESTA PARTE 2]")
                #     raise ValidationError(f"El servicio de Notificación encontró este inconveniente {mail_error}. Verifique la configuación del servicio de correo o contactese con su administrador de servicio!")
                # except ConnectionRefusedError:
                #     raise ValidationError(f"El servicio de correo electrónico no está disponible en este momento, favor intentelo más tarde!")
                # except ConnectionError as error:
                #     raise ValidationError(error)
                # except MailDeliveryException as mail_delivery_error:
                #     raise ValidationError(str(mail_delivery_error))

    @api.depends('aux_labor_table_ids', 'aux_labor_table_ids.qty_labor',
                 'aux_labor_table_ids.labor_total_cost', 'aux_labor_table_ids.subtotal_one',
                 'aux_labor_table_ids.subtotal_two')
    def calculate_daily_monthly(self):
        for rec in self:
            rec.labor_qty_daily = sum(rec.aux_labor_table_ids.mapped('qty_labor'))
            rec.labor_cost_daily = sum(rec.aux_labor_table_ids.mapped('labor_total_cost'))
            rec.overtime_sub_daily_one = sum(rec.aux_labor_table_ids.mapped('subtotal_one'))
            rec.overtime_sub_daily_two = sum(rec.aux_labor_table_ids.mapped('subtotal_two'))
            rec.labor_cost_monthly = rec.labor_cost_daily * 24
            rec.overtime_sub_monthly_one = rec.overtime_sub_daily_one * 24
            rec.overtime_sub_monthly_two = rec.overtime_sub_daily_two * 24

    @api.depends('vehicle_id.consumption_per_kilometer')
    def set_consumption_value(self):
        for rec in self:
            if rec.vehicle_id:
                rec.consumption_per_liter = rec.vehicle_id.consumption_per_kilometer
            else:
                rec.consumption_per_liter = None

    @api.onchange('vehicle_id.consumption_per_kilometer')
    def set_consumption_value_onchange(self):
        self.set_consumption_value()

    # Add a list to the items validation, so we can validate multiple times in one line
    # Generate a new budget with only the action of clicking
    def generate_sale_order(self):
        for rec in self:
            order_line_test = []
            if rec.create_or_update != False:
                opportunity_id = self.env['crm.lead'].search([('presale_ids', '=', rec.id)])
                if not rec.sales_order_id:
                    if not rec.team_id:
                        raise ValidationError(_("Rellene el campo 'Equipo de Ventas' para realizar la operación!"))
                    if not rec.partner_id:
                        raise ValidationError(_("Rellene el campo 'Empresa' para realizar la operación!"))
                    if not rec.name:
                        raise ValidationError(_("Rellene el campo 'Nombre' para realizar la operación!"))
                    if not rec.pricelist_id:
                        raise ValidationError(_("Rellene el campo 'Tarifas' para realizar la operación!"))

                    sale_order_obj = self.env['sale.order']
                    team = self.team_id
                    new_order_vals = {
                        'partner_id': self.partner_id.id,
                        'team_id': team and team.id,
                        'origin': self.name,
                        'opportunity_id': opportunity_id.id if opportunity_id else False,
                        'presale_id': rec.id,
                        'pricelist_id': rec.pricelist_id.id
                    }
                    _logger.warning('[SO-HEAD:]' % order_line_test)
                    order = sale_order_obj.create(new_order_vals)
                    print("[STAT:] Save")
                    print(f"[OP:]{opportunity_id.id}")
                else:
                    if not rec.team_id:
                        raise ValidationError(_("Rellene el campo 'Equipo de Ventas' para realizar la operación!"))
                    if not rec.partner_id:
                        raise ValidationError(_("Rellene el campo 'Empresa' para realizar la operación!"))
                    if not rec.name:
                        raise ValidationError(_("Rellene el campo 'Nombre' para realizar la operación!"))

                    order_id = {
                        'opportunity_id': opportunity_id.id,
                        'pricelist_id': rec.pricelist_id.id,
                        'payment_term_id': rec.payment_term_ids.id
                    }

                    rec.sales_order_id.write(order_id)
                    print("[STAT:] Update")
                    order = rec.sales_order_id
                    order.order_line.unlink()
            else:
                raise ValidationError(
                    _("Para Crear o Actualizar un Presupuesto, el botón 'Crear Presupuesto' debe quedar tildado!"))

        for hd in rec.heading_ids:
            heading_data = (0, 0, {
                'name': hd.name,
                'display_type': 'line_section',
                'order_id': order.id
            })
            order_line_test.append(heading_data)
            for item in hd.item_id:
                if not item.detail_ids:
                    raise ValidationError("Favor cotizar los productos de Preventas de %s!" % (item.name))

                datos = (0, 0, {
                    'name': item.name,
                    'display_type': 'line_section',
                    'order_id': order.id
                })
                order_line_test.append(datos)

                for detail in item.detail_ids:
                    order_line_vals = (0, 0, {
                        'price_unit': detail.unit_price,
                        'product_id': detail.product_id.id,
                        'analytic_tag_ids': [((6, 0, detail.account_analytic_id.ids))],
                        'name': detail.product_id.name,
                        'product_uom_qty': item.total_item_qty,  # detail.qty,
                        'order_id': order.id,
                    })
                    order_line_test.append(order_line_vals)

        print(f"[SECTION:]{order_line_test}")
        order.write({'order_line': order_line_test})
        _logger.warning('[SO-SECTION:]' % order_line_test)
        self.sales_order_id = order

    @api.onchange('fuel_type')
    def get_fuel_type(self):
        for rec in self:
            rec.consumption_per_liter = rec.fuel_type.consumption_rate

    @api.depends('consumption_per_liter', 'distance_to_work', 'transfers', 'price_per_liter', 'toll', 'transfers_ids')
    def calculate_transfer(self):
        for rec in self:
            rec.consumption_till_work = rec.distance_to_work * 2 * rec.consumption_per_liter
            rec.price_per_tour = rec.price_per_liter * rec.consumption_till_work
            rec.total_price_per_tour = rec.price_per_tour * rec.transfers
            # rec.total_transfer_amount = rec.total_price_per_tour + rec.toll
            rec.total_transfer_amount = sum(rec.transfers_ids.mapped('total_transfer_amount')) + rec.toll

    # @api.depends('logistic_summary_id','total_estimated_time','total_transfer_amount', 'total_ips')
    @api.depends('total_transfer_amount', 'total_estimated_time', 'total_transfer_amount', 'ips_per_month',
                 'logistic_summary_id', 'expected_month', 'proportional_bonus', 'mt_labour_summary_edit')
    def calculate_total_summary(self):
        for rec in self:
            rec.proportional_bonus = (rec.labor_cost_monthly * rec.expected_month) / 12
            rec.summary_logistic = sum(rec.logistic_summary_id.mapped('total_cost'))
            rec.summary_estimated_time = rec.total_estimated_time
            rec.total_summary_amount = (rec.labor_cost_monthly * rec.summary_estimated_time) + (
                        (rec.ips_per_month * rec.summary_estimated_time) + (
                            rec.total_transfer_amount + rec.summary_logistic)) + rec.proportional_bonus + rec.mt_labour_summary_edit

    # @api.depends('qty_month')  #total_worked_days
    @api.depends('total_worked_days')
    def get_expected_months(self):
        for rec in self:
            rec.qty_month = rec.total_worked_days
            rec.expected_month = rec.qty_month / 24
            rec.journeys = rec.expected_month * 24
            rec.total_estimated_time = rec.expected_month

    @api.depends('employer_contribution', 'expected_month')
    def get_ips_calculus(self):
        for rec in self:
            rec.ips_per_month = rec.labor_cost_monthly * (rec.employer_contribution / 100)
            rec.ips_estimated_time = rec.expected_month
            rec.total_ips = rec.ips_per_month * rec.ips_estimated_time

    @api.depends('heading_ids', 'hundred_perc_unforseen_perc', 'financial_interest_perc_default',
                 'financial_interest_perc', 'tools_fixed_expenses_perc', 'minor_materials_perc',
                 'financial_interest', 'hundred_perc_unforseen', 'tools_fixed_expenses')
    def calculate_net_total_costs(self):
        for rec in self:
            total_materials = 0
            total_labour = 0
            others_costs = 0
            total_materials = 0
            total_minor_materials = 0
            test_value = 0
            for head in rec.heading_ids:
                # for item in head.item_id:
                total_materials += sum(head.item_id.mapped('price_subtotal'))
                total_labour += sum(head.item_id.mapped('labor_subtotal_price'))
                # others_costs += sum(head.item_id.mapped('unforseen_subtotal_material')) + sum(head.item_id.mapped('unforseen_subtotal_labor')) + rec.financial_interest
                minor_materials = head.item_id.filtered(
                    lambda x: x.creado_por_boton or (not x.creado_por_boton and x.is_minor_materials == True))
                total_minor_materials += sum(minor_materials.mapped('price_subtotal'))

            rec.total_materials = total_materials
            rec.total_labour = total_labour

            print(f"[TOTAL_MATERIALS:] {rec.total_materials}")
            print(f"[TOTAL_LABOUR:] {rec.total_labour}")
            print(f"[OTHER-COSTS] {others_costs}")

            print(f"[TOTAL_MINOR_MATERIALS:] {total_minor_materials}]")
            rec.net_total_cost = rec.total_materials + rec.total_labour
            rec.vat_credit_materials = rec.total_materials / 11
            # rec.others_costs = others_costs - rec.net_total_cost
            rec.others_costs = rec.financial_interest + rec.hundred_perc_unforseen + rec.tools_fixed_expenses
            rec.vat_other_costs = rec.others_costs / 11

            rec.gen_grand_total_costs = rec.others_costs + rec.net_total_cost
            rec.hundred_perc_unforseen = rec.net_total_cost * (rec.hundred_perc_unforseen_perc / 100)
            # SHEET VERSION NO. 2
            rec.financial_interest = ((rec.total_materials * (rec.financial_interest_perc_default / 100)) * (
                        rec.financial_interest_perc / 100))
            # SHEET VERSION NO.2
            rec.tools_fixed_expenses = (rec.total_labour * (rec.tools_fixed_expenses_perc / 100))
            # rec.minor_materials = rec.total_materials * (rec.minor_materials_perc / 100)
            rec.minor_materials = total_minor_materials

    def set_labour_line_by_line(self):
        for rec in self:
            print("[LINE_X_LINE]")
            for rd in rec.heading_ids:
                print(f"[test]")
                labour_items = rd.item_id.filtered(lambda item: item.labour_line_by_line)
                total_labour_items = len(labour_items)
                if total_labour_items > 0:
                    percent_prorated = 100 / total_labour_items
                    labor_amount_per_item = rec.total_summary_amount / total_labour_items
                else:
                    percent_prorated = 0
                for item in labour_items:
                    print(f"[NOMBRE DE ITEM:] {item.name}")
                    existing_lab_products = self.env['presale.order.item.detail'].search(
                        [('item_id', '=', item.id), ('create_labor', '=', True)])
                    for existing_lab_product in existing_lab_products:
                        print(f"[LABOUR PRODUCT UPDATE] {existing_lab_product.product_id.name}")
                        existing_lab_product.unlink()

                    labour_product = self.env['product.template'].search([('is_labour', '=', True)])
                    if labour_product:
                        print("[LABOUR PRODUCT CREATION]")
                        print(f"[PRORATE_BO_AMOUNT:] {rec.total_summary_amount}")
                        values = {
                            'item_id': item.id,
                            'product_id': labour_product.id,
                            'qty': 1,
                            'labor_unit_price': labor_amount_per_item,
                            'labor_percent': percent_prorated,
                            'create_labor': True,
                            'is_fixed_labor': False
                        }
                        print(f"[ITEM-ID]{item.id}")
                        self.env['presale.order.item.detail'].create(values)
                    else:
                        raise ValidationError(
                            "Estimado usuario... No se encontró producto alguno de Mano de Obra a ser utilizado!")

    @api.depends('heading_ids', 'total_materials')
    def get_minor_material_perc_average(self):
        for rec in self:
            template_sum = 0
            total_fixed_minor_material = 0
            for head in rec.heading_ids:
                fixed_minor_material = head.item_id.filtered(
                    lambda x: x.creado_por_boton is False and x.create_labor is False
                              and x.is_minor_materials == True)
                total_fixed_minor_material += sum(fixed_minor_material.mapped('price_subtotal'))

                # template_sum += sum(item.mapped('minor_materials_percent'))
            rec.minor_materials_perc = (
                        (total_fixed_minor_material / rec.total_materials) * 100) if rec.total_materials > 0 else 0

            # if len(rec.heading_ids.mapped('item_id')) > 0:
            #     rec.minor_materials_perc = template_sum / len(rec.heading_ids.mapped('item_id'))

    @api.onchange('require_discount')
    def change_discount_to_zero(self):
        for rec in self:
            if rec.require_discount == False:
                rec.discount_over_total = 0.00

    # @api.depends('heading_ids','vat_credit_materials','commission_sf_av_perc','external_commission_per','gen_grand_total_costs','gen_grand_total_costs','business_income_tax_per', 'require_discount', 'discount_over_total')
    @api.depends('heading_ids', 'heading_ids.item_id', 'heading_ids.item_id.lab_subtotal_price_final',
                 'discount_over_total')
    def calculate_price_vat_included(self):
        for rec in self:
            price_vat_included = 0
            for heading in rec.heading_ids:
                for item in heading.item_id:
                    price_vat_included += item.lab_subtotal_price_final - rec.discount_over_total
            rec.price_vat_included = price_vat_included

    @api.depends('price_vat_included', 'total_materials', 'vat_credit_materials', 'vat_other_costs',
                 'mt_labour_summary_edit', 'commission_sf_av_perc', 'external_commission_per', 'gen_grand_total_costs',
                 'discount_over_total')
    def calculate_commisions(self):
        for rec in self:
            rec.vat_mt_labour_summary_edit = rec.mt_labour_summary_edit / 11

            rec.vat_credit_other_costs = rec.vat_credit_materials + rec.vat_other_costs + rec.vat_mt_labour_summary_edit
            rec.vat_ten_percent = rec.price_vat_included / 11
            rec.price_without_vat = rec.price_vat_included - rec.vat_ten_percent

            rec.commission_sf_av = (rec.price_vat_included * (rec.commission_sf_av_perc / 100))
            rec.comm_sf_av_whithout_vat = rec.commission_sf_av / 1.1
            rec.external_commission = (rec.price_vat_included * (rec.external_commission_per / 100))
            rec.external_comm_without_vat = rec.external_commission / 1.1
            rec.gross_contribution = (rec.price_without_vat - rec.gen_grand_total_costs) + rec.vat_credit_other_costs

            rec.business_income_tax = (
                                                  rec.gross_contribution - rec.comm_sf_av_whithout_vat - rec.external_comm_without_vat) * (
                                                  rec.business_income_tax_per / 100)
            rec.total_expenses = (
                                             rec.gen_grand_total_costs - rec.vat_credit_other_costs) + rec.comm_sf_av_whithout_vat + rec.external_comm_without_vat + rec.business_income_tax
            rec.contributions = rec.price_without_vat - rec.total_expenses

    @api.depends('price_without_vat', 'total_expenses', 'contributions')
    def calculate_cost_and_sp(self):
        for rec in self:
            if rec.total_expenses > 0:
                rec.cost_percent = (rec.contributions / rec.total_expenses) * 100
            else:
                rec.cost_percent = 0

            if rec.price_without_vat > 0:
                rec.sale_price_percent = (rec.contributions / rec.price_without_vat) * 100
            else:
                rec.sale_price_percent = 0

    @api.depends('total_materials', 'bt_matl_wo_mm', 'total_summary_amount', 'mont_artif_disassm')
    def get_proration_percentage(self):
        for rec in self:
            rec.bt_matl_wo_mm = rec.total_materials
            rec.bt_labour = rec.total_summary_amount
            rec.diff_prorated_mat = rec.bt_labour - rec.mont_artif_disassm
            rec.mont_artif_disassm = rec.bt_matl_wo_mm / rec.diff_prorated_mat

    @api.depends('labor_per_floor_ids')
    def get_total_work_days_month(self):
        for rec in self:
            rec.total_worked_days = sum(rec.labor_per_floor_ids.mapped('workdays'))
            rec.month_of_works = rec.total_worked_days / 24

    def recalculate_amounts(self):
        self.calculate_daily_monthly()
        self.get_expected_months()
        self.get_ips_calculus()
        self.calculate_transfer()
        self.calculate_total_summary()
        self.calculate_net_total_costs()
        self.get_minor_material_perc_average()
        self.calculate_cost_and_sp()
        self.calculate_headings()

    def _update_summary_laborer(self):
        for rec in self:
            labor_type_summary = {}
            for floor in rec.labor_per_floor_ids:
                for labor_calculation in floor.labor_type_ids:
                    labor_type = labor_calculation.labor_type
                    # Tiene que hacer un search a la tabla presale.labor_used
                    # get_labor = self.env['presale.labor_used'].search([('labor_type','=', labor_type.id)])
                    subtotal_amount = labor_calculation.subtotal_amount
                    labor_type_id = labor_type.id
                    if labor_type_id in labor_type_summary:
                        labor_type_summary[labor_type_id] += subtotal_amount
                    else:
                        labor_type_summary[labor_type_id] = subtotal_amount

            for labor_type_id, subtotal_amount in labor_type_summary.items():
                summary_laborer = self.env['presale.auxiliary_summary_laborer'].search([
                    ('labor_type', '=', labor_type_id),
                    ('presale_labor_summary_ids', '=', rec.id)
                ])

                line_subtotal_amount = (subtotal_amount / rec.total_worked_days) if rec.total_worked_days > 0 else 0

                labor_used = rec.labor_used_ids.filtered(lambda x: x.labor_type.id == labor_type_id)

                if labor_used:
                    labor_unit_cost = labor_used.labor_unit_cost
                    if labor_unit_cost:
                        day_laborers = line_subtotal_amount / labor_unit_cost
                    else:
                        day_laborers = 0.0
                else:
                    day_laborers = 0.0

                if summary_laborer:
                    summary_laborer.write({'cost_laborers_per_day': line_subtotal_amount, 'day_laborers': day_laborers})
                else:
                    self.env['presale.auxiliary_summary_laborer'].create({
                        'presale_labor_summary_ids': rec.id,
                        'labor_type': labor_type_id,
                        # 'day_laborers': 1,
                        'cost_laborers_per_day': line_subtotal_amount,
                        'day_laborers': day_laborers
                    })

                labor_table = self.env['presale.auxiliary_labor_table']
                get_labor_data = labor_table.search([
                    ('order_id_aux', '=', rec.id), ('labor_type', '=', labor_type_id)])
                if get_labor_data:
                    get_labor_data.write({'qty_labor': day_laborers, 'labor_unit_cost': labor_unit_cost})
                else:
                    labor_table.create({'order_id_aux': rec.id, 'labor_type': labor_type_id,
                                        'qty_labor': day_laborers,
                                        'labor_unit_cost': labor_unit_cost})

    def _remove_obsolete_summary_laborer(self):
        for rec in self:
            labor_type_ids = rec.labor_per_floor_ids.mapped('labor_type_ids.labor_type.id')
            obsolete_laborers = rec.env['presale.auxiliary_summary_laborer'].search([
                ('presale_labor_summary_ids', '=', rec.id),
                ('labor_type', 'not in', labor_type_ids)
            ])
            obsolete_laborers.unlink()

    def _remove_obsolete_summary_items(self):
        for rec in self:
            labor_type_ids = rec.labor_per_floor_ids.mapped('labor_type_ids.labor_type.id')
            task_schedule_db = rec.env['presale.auxiliary_labor_table'].search([
                ('order_id_aux', '=', rec.id),
                ('labor_type', 'not in', labor_type_ids)])
            task_schedule_db.unlink()

    def update_auxiliary_calculation_per_floor(self):
        for rec in self:
            if rec.create_update == 'crear':
                per_floor = self.env['presale.auxiliary_calculation_per_floor'].create({
                    'name': 'Plantilla de Piso',
                    'floor_order_id': rec.id,
                    'num_items': 1,
                    'workdays': 0,
                })

                labor_type_values = []
                for labor_used in rec.labor_used_ids:
                    labor_type_values.append((0, 0, {
                        'labor_type': labor_used.labor_type.id,
                        'qty_labor': 0,
                        'workdays': 0,
                        'labor_unit_cost': labor_used.labor_unit_cost,
                    }))
                per_floor.write({'labor_type_ids': labor_type_values})
            else:
                for lab in rec.labor_used_ids:
                    for labor_order in rec.labor_per_floor_ids:
                        if labor_order.labor_type_ids:
                            existing_labor_type = labor_order.labor_type_ids.filtered(
                                lambda x: x.labor_type == lab.labor_type)
                            if existing_labor_type:
                                print(f"[UPDATE-LINE:]")
                                existing_labor_type.write({'labor_unit_cost': lab.labor_unit_cost})
                            else:
                                print(f"[CREATE-LINE:]")
                                floor_lines = {
                                    'cal_order_id': labor_order.id,
                                    'order_id': rec.id,
                                    'qty_labor': 0,
                                    'workdays': 0,
                                    'labor_unit_cost': lab.labor_unit_cost,
                                    'labor_type': lab.labor_type.id

                                }
                                self.env['presale.auxiliary_labor_calculation'].create(floor_lines)

        self._update_summary_laborer()

    @api.model
    def create(self, values):
        record = super(PreSaleOrder, self).create(values)
        record._remove_obsolete_summary_items()
        record._update_summary_laborer()
        return record

    def write(self, values):
        result = super(PreSaleOrder, self).write(values)
        self._remove_obsolete_summary_laborer()
        self._remove_obsolete_summary_items()
        self._update_summary_laborer()
        return result

    # def unlink(self):
    #     for record in self:
    #         if record.labor_used_ids:
    #             labor_types = record.labor_used_ids.mapped('labor_type')
    #             for labor_type in labor_types:
    #                 labor_type_ids = record.labor_per_floor_ids.filtered(lambda x: x.labor_type_ids and x.labor_type_ids.mapped('labor_type') == labor_type)
    #                 labor_type_ids.unlink()
    #     return super(PreSaleOrder, self).unlink()

    # @api.model
    # def default_get(self, fields_list):
    #    res = super(PreSaleOrder, self).default_get(fields_list)
    #    vals = [(0, 0, {'labor_type': 1, 'labor_unit_cost': float(1000)})]
    #    res.update({'labor_used_ids': vals})
    #    return res

    # @api.model
    # def create(self, vals):
    #     # Agrega los valores predeterminados en 'labor_used_ids' al crear un registro de 'presale.order'
    #     if 'labor_used_ids' not in vals:
    #         vals['labor_used_ids'] = [(0, 0, {'labor_type': 1, 'labor_unit_cost': 1000})]

    #     record = super(PreSaleOrder, self).create(vals)
    #     return record

    @api.depends('heading_ids')
    def calculate_headings(self):
        for rec in self:
            total_minor_materials = 0
            all_manual_labour = 0
            for head in rec.heading_ids:
                all_manual_labour += sum(item.price_subtotal for item in head.item_id.filtered(
                    lambda x: not x.create_labor and not x.is_minor_materials and x.has_labour and x.is_fixed_labor))
                all_minor_materials = head.item_id.filtered(
                    lambda x: x.creado_por_boton or (not x.creado_por_boton and x.is_minor_materials == True))
                total_minor_materials += sum(all_minor_materials.mapped('price_subtotal'))

            print(f"[Total Minor Materials:] {total_minor_materials}")
            rec.material_total_cost = all_manual_labour
            rec.total_minor_materials = total_minor_materials
            print(f"[FIXED MATERIALS:] {all_manual_labour}")
            rec.total_heading_proration = rec.material_total_cost + rec.total_minor_materials

    @api.depends('heading_ids', 'total_materials', 'total_heading_proration', 'mt_labour_summary_edit')
    def calculate_exercise_chart(self):
        fixed_labour = 0
        manual_labor = 0
        for rec in self:
            for head in rec.heading_ids:
                # for item in head.item_id:
                fixed_labour += sum(item.labor_subtotal_price for item in head.item_id.filtered(
                    lambda x: not x.create_labor and not x.is_minor_materials and x.has_labour and x.is_fixed_labor))
                manual_labor += sum(
                    item.labor_subtotal_price for item in head.item_id.filtered(lambda x: x.create_labor))
            print(f"[TOTAL WACHO:] {rec.total_materials}")

            rec.grand_total_material = rec.total_materials
            rec.total_mat_for_labour = rec.grand_total_material - rec.total_heading_proration  #
            print(f"[MANO DE OBRA Y TOTAL] {rec.total_mat_for_labour}")
            rec.bt_labour = rec.total_summary_amount + rec.mt_labour_summary_edit
            rec.only_labour = fixed_labour + manual_labor
            rec.diff_prorated_mat = rec.bt_labour - rec.only_labour
            rec.incidents_in_materials = (
                        (rec.diff_prorated_mat / rec.total_mat_for_labour) * 100) if rec.total_mat_for_labour > 0 else 0

    def update_labour_bo_proration(self):
        _logger.warning('[TESTING:]')

        for rec in self:
            n = 0
            for head in rec.heading_ids:
                filtered_amount = head.item_id.filtered(lambda x: (
                        not x.create_labor
                        and not x.is_minor_materials
                        and x.has_labour
                        and not x.id_distribuited_lines
                        and (not x.is_fixed_labor or not x.is_fixed_labor_unit)
                ))
                # size_detail = labour_percent / int(len(filtered_amount))
                for fa in filtered_amount:
                    if not fa.is_fixed_labor:
                        n += 1
                        print(f"[NUM:]{n} [DT-NAME:] {fa.name}")
                        _logger.warning('[PRORRATEO:] %s' % rec.incidents_in_materials)
                        fa.labor_percent = rec.incidents_in_materials


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    consumption_per_kilometer = fields.Float(string="Consumption per KM", tracking=True)


class PresaleAdditionals(models.Model):
    _name = "presale.additionals"

    name = fields.Char(string="Name", tracking=True)
    order_id_add = fields.Many2one('presale.order', string="Order Id", store=True)
    types_additionals = fields.Many2one('presale.types_additionals', string="Types of Additionals", tracking=True)
    amount_additionals = fields.Float(string="Amount", tracking=True)

    @api.constrains('name', 'order_id_add', 'types_additionals')
    def _check_presale_factors(self):
        for rec in self:
            presale_factors = self.env['presale.additionals'].search_count(
                [('name', '=', rec.name), ('order_id_add', '=', rec.order_id_add.id),
                 ('types_additionals', '=', rec.types_additionals.id)])
            if presale_factors > 1:
                raise ValidationError(_('A previously used factor rate already exists on this Presale Quote!'))

    @api.onchange('types_additionals')
    def set_additional_name(self):
        for rec in self:
            if rec.types_additionals:
                rec.name = rec.types_additionals.name


class PresaleTypeAdditionals(models.Model):
    _name = "presale.types_additionals"

    name = fields.Char(string="Name", tracking=True)

    @api.constrains('name')
    def _check_type_factors(self):
        for rec in self:
            type_factor = self.env['presale.types_additionals'].search_count([('name', '=', rec.name)])
            if type_factor > 1:
                raise ValidationError(_('This name was already used for this type of factor!'))


class PresaleTypeHeadings(models.Model):
    _name = "presale.type_headings"

    name = fields.Char(string="Name")


class AccountAnalyticTag_Inh(models.Model):
    _inherit = "account.account.tag"

    is_minor_material_tag = fields.Boolean(string="Is Minor Material?", default=False)

    @api.constrains('is_minor_material_tag')
    def _check_type_factors(self):
        for rec in self:
            type_factor = self.env['account.account.tag'].search_count([('is_minor_material_tag', '=', True)])
            if type_factor > 1:
                raise ValidationError(_('This name was already used for this type of factor!'))
