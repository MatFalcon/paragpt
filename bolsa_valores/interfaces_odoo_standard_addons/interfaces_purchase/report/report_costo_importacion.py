from odoo import api, fields, models, exceptions, _
from datetime import date


class ReportCostoImportacion(models.AbstractModel):
    _name = 'report.interfaces_purchase.report_costo_importacion'

    @api.model
    def _get_report_values(self, docids, data=None):
        if len(docids) > 1:
            raise exceptions.UserError(_('Seleccionar solo un documento'))

        purchase = self.env['purchase.order'].browse(docids)[0]
        landeds = self.env['stock.landed.cost'].search([
            ("picking_ids", "in", [x.id for x in purchase.picking_ids]),
            ("state", "=", 'done')
        ], order="date desc")
        po_currency_id = purchase.currency_id

        if landeds:
            last_land = landeds[0]
            reception = purchase.picking_ids[0]

            invoices = purchase.invoice_ids
            if invoices:
                prod_list = []
                for line in purchase.order_line:
                    standard_price = 0
                    valuations = self.env["stock.valuation.layer"].search([
                        ("product_id","=", line.product_id.id),
                        ("create_date","<=", last_land.date),
                        # ("stock_move_id","=", reception.id), # con move id no considera valor modificado manualmente
                        ])
                    if valuations:
                        cost_val = sum(x.value for x in valuations)
                        cost_qty = sum(x.quantity for x in valuations)
                        if cost_qty > 0:  # para evitar divisiones / 0 
                            standard_price = cost_val / cost_qty
                    else:
                        standard_price = line.product_id.standard_price

                    prod_list.append({
                        "default_code": line.product_id.default_code,
                        "name": line.product_id.name,
                        "price_unit": line.price_unit,
                        "product_qty": line.product_qty,
                        "standard_price": standard_price
                    })
                return {
                    "purchase": purchase,
                    "po_currency_id": po_currency_id,
                    "company_id": self.env.company,
                    "pickings": purchase.picking_ids,
                    "landeds": landeds ,
                    "prod_list": prod_list ,
                    "invoices": invoices
                }
            else:
                raise exceptions.ValidationError(_('No se encuentra factura asociada.'))
        else:
            raise exceptions.ValidationError(_('No se encuentran costos asociados.'))


class ReportCostoImportacionXls(models.AbstractModel):
    _name = 'report.interfaces_purchase.report_costo_importacion_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):
        global sheet
        global bold
        global num_format
        global position_x
        global position_y

        picking = self.env['stock.picking'].browse(data.get('active_id'))
        landeds = self.env['stock.landed.cost'].search([
            ("picking_ids", "in", [picking.id]),
            ("state", "=", 'done'),
            ("company_id", "=", self.env.company.id)
        ], order="date desc")
        purchase = self.env['purchase.order'].search([('picking_ids', 'in', [picking.id])])
        po_currency_id = purchase.currency_id

        move_ids = [x.id for x in picking.move_ids_without_package]

        invoices = purchase.invoice_ids

        prod_list = []
        if landeds:
            for line in purchase.order_line:
                standard_price = 0
                cost_val =  0
                cost_qty = 0

                # sumando los costos por cada producto
                for lan in landeds:
                    cost_val += sum(lan.valuation_adjustment_lines.filtered(lambda x: x.product_id == line.product_id and x.move_id.id in move_ids).mapped('additional_landed_cost'))
                for invo in invoices:
                    total_line = sum(invo.line_ids.filtered(lambda x:x.product_id == line.product_id).mapped('price_total'))
                    cost_val += invo.currency_id._convert(total_line, self.env.company.currency_id, self.env.company, invo.invoice_date)

                if not invoices:
                    total_line = sum(line.filtered(lambda x:x.product_id == line.product_id).mapped('price_subtotal'))
                    cost_val += purchase.currency_id._convert(total_line, self.env.company.currency_id, self.env.company, purchase.effective_date)


                standard_price = cost_val / line.product_qty

                prod_list.append({
                    "id": line.product_id.id,
                    "default_code": line.product_id.default_code,
                    "name": line.product_id.name,
                    "price_unit": line.price_unit,
                    "product_qty": line.product_qty,
                    "standard_price": standard_price,
                    "total": cost_val
                })
            # creacion de doc xlsx
            sheet = workbook.add_worksheet('Hoja 1')
            bold = workbook.add_format({'bold': True})
            tittle = workbook.add_format({'bold': True, 'bg_color': 'green','align':'center'})
            tittle_col = workbook.add_format({'bold': True, 'bg_color': 'gray','align':'center'})
            footer_col = workbook.add_format({'bold': True, 'bg_color': 'gray','align':'center'})
            footer_numeric = workbook.add_format({'bold': True, 'bg_color': 'gray','align':'right'})
            footer_numeric.set_num_format('#,##0')
            numerico = workbook.add_format({'num_format': True, 'align': 'right'})
            numerico.set_num_format('#,##0')
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

            # se ajusta el ancho de la celda
            sheet.set_column(0,0,50)
            sheet.set_column(1,1,15)
            sheet.set_column(2,2,15)
            sheet.set_column(3,3,15)

            # encavbezado
            breakAndWrite("Reporte de costeo",bold)
            breakAndWrite("Transferencia Nro: {0}".format(picking.name),bold)
            if invoices:
                # agregar facturas entre comas
                breakAndWrite("Factura de compra: {0}".format(", ".join([x.name for x in invoices])),bold)
            # addSalto()
            addSalto()

            sheet.merge_range(4, 0, 4, 3,'Productos', tittle)
            if landeds:
                sheet.merge_range(4, 4, 4, (4+len(landeds)),'Costos adicionales', tittle)
                sheet.merge_range(4, 4+len(landeds), 4, (5+len(landeds)),'Totales', tittle)
            else:
                sheet.merge_range(4, 4, 4, 5,'Totales', tittle)

            # titulos columnas
            breakAndWrite("Nombre",tittle_col)
            rightAndWrite("Cantidad",tittle_col)
            rightAndWrite("Costo Unitario",tittle_col)
            rightAndWrite("Costo Total",tittle_col)
            for lan in landeds:
                sheet.set_column(position_y ,(position_x+1),35)
                rightAndWrite("{0} ({1})".format(lan.name, lan.vendor_bill_id.name),tittle_col)
            rightAndWrite("Valor Unitario",tittle_col)
            rightAndWrite("Valor Total",tittle_col)

            for prod in prod_list:
                breakAndWrite(prod['name'])
                rightAndWrite(prod['product_qty'],numerico)
                rightAndWrite(prod['price_unit'],numerico)
                rightAndWrite(prod['product_qty'] * prod['price_unit'],numerico)
                for lan in landeds:
                    added_val = sum(lan.valuation_adjustment_lines.filtered(lambda x: x.product_id.id == prod['id'] and x.move_id.id in move_ids).mapped('additional_landed_cost'))
                    rightAndWrite(added_val, numerico)
                sheet.set_column((position_y+1) ,(position_x+1),15)
                rightAndWrite(prod['standard_price'], numerico)

                sheet.set_column((position_y+1) ,(position_x+1),15)
                rightAndWrite(prod['total'], numerico)
            
            # totales
            addSalto()
            breakAndWrite("")
            rightAndWrite("")
            rightAndWrite("")
            rightAndWrite("Total adicionales", footer_col)
            for lan in landeds:
                rightAndWrite(lan.amount_total, footer_numeric)
        else:
            raise ValidationError('No se encuentran costos asociados.')
