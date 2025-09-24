# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, exceptions, fields, models


class TransferenciaEstado(models.Model):
    _name = "apicontinental.transferencias.estado"
    _description = "Registros del estado de una transferencia"

    name = fields.Char(string="Nombre")
    comprobante = fields.Char(string="Comprobante", unique=False, required=False)
    numero_ticket = fields.Char(string="Número de ticket")
    partner_id = fields.Many2one('res.partner', string="Proveedor")
    secuencia = fields.Char(string="Secuencia")
    estado = fields.Char(string="Estado")
    fecha_proceso = fields.Char(string="Fecha de proceso")
    cuenta_debito = fields.Char(string="Cuenta de débito")
    cuenta_credito = fields.Char(string="Cuenta de crédito")
    monto = fields.Char(string="Monto")
    moneda = fields.Char(string="Moneda")
    codigo_tib_web = fields.Char(string="Código TIB Web")
    beneficiario = fields.Char(string="Beneficiario")
    autoriza = fields.Char(string="Autoriza")
    carga = fields.Char(string="Carga")
    banco_beneficiario = fields.Char(string="Banco beneficiario")
    numero_factura = fields.Char(string="Número de factura")
    motivo_transferencia = fields.Char(string="Motivo de la transferencia")
    error = fields.Char(string="Error")
    tipo_transferencia = fields.Selection([
        ('interbancaria', 'Interbancaria'),
        ('interna', 'Interna'),
        ('cheque_gerencia', 'Cheque Gerencia'),
    ], string="Tipo de transferencia")

    # Cheque de gerencia
    sucursal = fields.Char(string="Sucursal")
    autorizado = fields.Char(string="Autorizado")

    # Cheque e interna
    fecha_pago = fields.Char(string="Fecha de pago")
    concepto = fields.Char(string="Concepto")

    _sql_constraints = [
        ('numero_ticket_unique', 'unique(numero_ticket)', 'El número de ticket debe ser único'),
    ]

    @api.model
    def create(self, vals):
        res = super(TransferenciaEstado, self).create(vals)
        if res:
            res.write({'name': res.id})

        return res

    def consultar_estado_transferencia(
            self, hash_api, nro_ticket, partner_id, fecha_inicio, fecha_fin, estado, tipo_pago, payment_id):
        """ Consulta y guarda el estado de una transferencia interbancaria"""
        try:
            if not hash_api or not nro_ticket or not partner_id:
                raise exceptions.ValidationError("Faltan parámetros para consultar el estado de la transferencia")

            if not fecha_inicio:
                fecha_inicio = datetime.now().strftime("%d/%m/%Y")
            if not fecha_fin:
                fecha_fin = datetime.now().strftime("%d/%m/%Y")
            if not estado:
                estado = "TODOS"

            data = None
            payload = {
                "cuenta": hash_api,
                "estado": estado,
                "fechaInicio": fecha_inicio,
                "fechaFin": fecha_fin
            }

            # Consultamos al API de continental para obtener el estado de la transferencia
            if tipo_pago == 'interbancaria':
                comprobante = self.env["apicontinental.pago_proveedores"].transferencia_interbancaria_consultar(payload, 1, 50, payment_id)
            elif tipo_pago == 'interna':
                comprobante = self.env["apicontinental.pago_proveedores"].transferencia_internav1_consultar(payload, 1, 50, payment_id)
            elif tipo_pago == 'cheque_gerencia':
                comprobante = self.env["apicontinental.pago_proveedores"].cheque_gerencia_consultar(payload, 1, 50, payment_id)
            else:
                raise exceptions.ValidationError("El tipo de pago no es válido")

            # Si el API no responde correctamente, lanzamos una excepción
            if comprobante.status_code != 200:
                raise exceptions.ValidationError("Error al consultar el estado de la transferencia")

            # Obtenemos el item individual que necesitamos. Identificamos por el número de ticket
            for item in comprobante.json()["data"]:
                if item.get('numeroTicket', '') == nro_ticket:
                    data = item
                    break

            if not data:
                raise exceptions.ValidationError("El número de ticket no existe")

            transferencia_estado = {
                'partner_id': partner_id.id,
                'comprobante': data.get('comprobante', ''),
                'secuencia': data.get('secuencia', ''),
                'estado': data.get('estado', ''),
                'fecha_proceso': data.get('fechaProceso', ''),
                'cuenta_debito': data.get('cuentaDebito', ''),
                'cuenta_credito': data.get('cuentaCredito', ''),
                'monto': data.get('monto', ''),
                'moneda': data.get('moneda', ''),
                'codigo_tib_web': data.get('codigoTibWeb', ''),
                'beneficiario': data.get('beneficiario', ''),
                'autoriza': data.get('autoriza', ''),
                'carga': data.get('carga', ''),
                'banco_beneficiario': data.get('bancoBeneficiario', ''),
                'numero_factura': data.get('numeroFactura', ''),
                'motivo_transferencia': data.get('motivoTransferencia', ''),
                'numero_ticket': data.get('numeroTicket', ''),
                'sucursal': data.get('sucursal', ''),
                'autorizado': data.get('autorizado', ''),
                'fecha_pago': data.get('fechaPago', ''),
                'concepto': data.get('concepto', ''),
                'tipo_transferencia': tipo_pago
            }

            # Buscamos el estado de la transferencia por el número de ticket
            estado = self.env["apicontinental.transferencias.estado"].search(
                [('numero_ticket', '=', data['numeroTicket'])])

            # Actualizamos o creamos el registro
            if estado:
                estado.sudo().write(transferencia_estado)
            else:
                estado = self.env["apicontinental.transferencias.estado"].sudo().create(transferencia_estado)

            return estado
        except Exception as e:
            print(e)
            raise exceptions.ValidationError(e)
