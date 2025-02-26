from odoo import fields, api, models, exceptions
from odoo.exceptions import UserError, ValidationError


class PlantillaContrato(models.Model):
    _name = 'plantilla.contrato'
    _description = 'Plantilla de Contrato'

    name = fields.Char(string="Nombre")

    seccion_ids = fields.One2many('plantilla.contrato.seccion', 'plantilla_contrato_id', string="Secciones", copy=True)

    # Fake fields used to implement the placeholder assistant
    model_object_field = fields.Many2one('ir.model.fields', string="Campo")
    sub_object = fields.Many2one('ir.model', 'Sub-modelo', readonly=True)
    sub_model_object_field = fields.Many2one('ir.model.fields', 'Sub-campo')
    null_value = fields.Char('Valor por defecto')
    copyvalue = fields.Char('Expresión de marcador')
    model_id = fields.Many2one('ir.model', 'Modelo',
                               default=lambda self: self.env['ir.model'].search([('model', '=', 'hr.contract')]))

    def buttonAgregarItem(self):
        view_id = self.env.ref('plantilla_contrato.sub_seccion_plantilla_tree_view')
        return {
            'name': ('Items'),
            'res_model': 'plantilla.contrato.subseccion',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'context': {
                ''
            }
        }

    def build_expression(self, field_name, sub_field_name, null_value):
        """Returns a placeholder expression for use in a template field,
        based on the values provided in the placeholder assistant.

        :param field_name: main field name
        :param sub_field_name: sub field name (M2O)
        :param null_value: default value if the target value is empty
        :return: final placeholder expression """
        expression = ''
        if field_name:
            expression = "<<" + field_name
            if sub_field_name:
                expression += "__" + sub_field_name
            if null_value:
                expression += " or '''%s'''" % null_value
            expression += ">>"
        return expression

    @api.onchange('model_object_field', 'sub_model_object_field', 'null_value')
    def onchange_sub_model_object_value_field(self):
        if self.model_object_field:
            if self.model_object_field.ttype in ['many2one', 'one2many', 'many2many']:
                model = self.env['ir.model']._get(self.model_object_field.relation)
                if model:
                    self.sub_object = model.id
                    self.copyvalue = self.build_expression(self.model_object_field.name,
                                                           self.sub_model_object_field and self.sub_model_object_field.name or False,
                                                           self.null_value or False)
            else:
                self.sub_object = False
                self.sub_model_object_field = False
                self.copyvalue = self.build_expression(self.model_object_field.name, False, self.null_value or False)
        else:
            self.sub_object = False
            self.copyvalue = False
            self.sub_model_object_field = False
            self.null_value = False


class SeccionPlantilla(models.Model):
    _name = "plantilla.contrato.seccion"
    _description = "Secciones de plantilla"
    _order = 'plantilla_contrato_id, sequence, id'
    # _rec_name = "workorder_id"

    plantilla_contrato_id = fields.Many2one('plantilla.contrato', string='Plantilla')
    name = fields.Char('Titulo')
    tipo = fields.Selection([
        ('titulo_nueva_pagina', "Titulo nueva página"),
        ('normal', "Normal"),
        ('normal_items', "Normal + Items"),
        ('items', 'Items'),
        ('pie', 'Pie de Contrato')], default=False)
    texto = fields.Text('Contenido')
    sequence = fields.Integer(string='Secuencia', default=10)
    secuencia = fields.Integer(string="Secuencia")
    items_ids = fields.Many2many('plantilla.contrato.subseccion', 'seccion_id', string="Items")


class SubSeccionPlantilla(models.Model):
    _name = "plantilla.contrato.subseccion"
    _description = "Subsecciones de plantilla"
    _order = 'id'
    _rec_name = "texto"

    texto = fields.Text('Contenido')
    secuencia = fields.Integer(string="Secuencia")
    parent_id = fields.Many2one('plantilla.contrato.subseccion', string="Item Padre")

    @api.onchange('parent_id')
    def onChangeParent(self):
        if self.parent_id:
            if self.parent_id.parent_id.parent_id:
                raise UserError(_(
                    'No puede crear una jerarquia de cuarto nivel. Intente con otro Item.'))
