# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    continental_comprobante = fields.Char(string="Comprobante")


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    continental_fecha_hasta = fields.Date(string="Fecha hasta")
    journal_hash = fields.Boolean(compute='_compute_journal_hash', string='Diario tiene Hash')

    @api.depends('journal_id.api_continental_hash')
    def _compute_journal_hash(self):
        for record in self:
            record.journal_hash = bool(record.journal_id.api_continental_hash)

    def descargar_extracto(self):
        try:
            for record in self:
                hashContinental = record.journal_id.api_continental_hash
                fromDate = record.date
                toDate = record.continental_fecha_hasta
                nroPagina = 1
                cantRegistros = 50

                if not fromDate or not toDate:
                    raise exceptions.ValidationError("Debe ingresar las fechas desde y hasta")

                if fromDate > toDate:
                    raise exceptions.ValidationError("La fecha desde no puede ser mayor a la fecha hasta")

                # Formateamos la fecha a DD/MM/YYYY
                fromDate = fromDate.strftime("%d/%m/%Y")
                toDate = toDate.strftime("%d/%m/%Y")

                # Consultamos a continental el extracto
                data = hashContinental, fromDate, toDate, nroPagina, cantRegistros
                result = self.env["apicontinental.consultar_cuenta"].consultar_extracto(*data)

                # Si el result es diferente de 200, entonces retornamos el error
                if result.status_code != 200:
                    raise exceptions.ValidationError(result.text)

                # Obtenemos los datos
                cabecera = result.json()["cabecera"]
                movimientos = result.json()["movimientos"]

                # Verificamos que dentro de los movimientos no haya un movimiento ya registrado
                comprobantes = [m["comprobante"] for m in movimientos]
                transferencias = self.env["account.bank.statement.line"].search(
                    [('continental_comprobante', 'in', comprobantes)])

                if transferencias:
                    raise exceptions.ValidationError(
                        "En el rango de fechas seleccionado, ya existen detalles del extracto registrados en el sistema")

                # Guardamos la cabecera
                record.write({
                    'balance_start': cabecera["saldoInicial"],
                    'balance_end_real': cabecera["saldoDisponible"]
                })

                # Limpiamos los extractos anteriores
                record.write({'line_ids': [(5, 0, 0)]})

                # Guardamos los movimientos
                lines = []
                for m in movimientos:
                    # convertimos la fecha de "03/01/2023" a "2023-01-03" con split
                    fecha = m["fechaContable"].split("/")
                    fecha = f"{fecha[2]}-{fecha[1]}-{fecha[0]}"
                    monto = m["montoCredito"]
                    if monto == 0:
                        monto = m["montoDebito"] * -1

                    # Obtenemos el estado de la transferencia a traves del comprobante
                    transferencia = self.env["apicontinental.transferencias.estado"].search(
                        [('comprobante', '=', m["comprobante"])])

                    data = {
                        'date': fecha,
                        'amount': monto,
                        'payment_ref': m["concepto"],
                        'partner_id': transferencia.partner_id.id,
                        'continental_comprobante': m["comprobante"]
                    }
                    lines.append((0, 0, data))

                # Guardamos los movimientos en la BD
                record.write({'line_ids': lines})
        except Exception as e:
            print(e)
            raise exceptions.ValidationError(e)
