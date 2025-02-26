# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    obviar_validacion = fields.Boolean(string='Obviar validación de RUC', default=False)
    vat = fields.Char(string="RUC", index=True)

    def clear_vat(self, vat):
        allowed_characters = '1234567890-'
        if vat:
            for vat_character in vat:
                if vat_character not in allowed_characters:
                    vat = vat.replace(vat_character, '')
        return vat

    @api.constrains('vat', 'company_id', 'id')
    def validar_duplicado(self):
        ruc = self.clear_vat(self.vat) if not self.obviar_validacion else self.vat
        if ruc:
            company = self.company_id
            contacts = self.env['res.partner'].search([('vat', '=', ruc), ('company_id', '=', company.id), ('id', '!=', self.id), ('parent_id', '=', None)])
            if contacts and self.parent_id:
                contacts = contacts.filtered(lambda x: x.id != self.parent_id.id)
            # if contacts:
            #    raise exceptions.ValidationError('RUC ya existente')

    @api.depends('vat', 'obviar_validacion')
    def val_ruc(self, vals):
        obviar_validacion_ruc = vals.get('obviar_validacion') if vals.get('obviar_validacion') != None else self.obviar_validacion
        parent = self.parent_id
        if parent:
            obviar_validacion_ruc_parent = parent.obviar_validacion
            if obviar_validacion_ruc_parent:
                obviar_validacion_ruc = True
        if not obviar_validacion_ruc:
            vals['vat'] = self.clear_vat(vals.get('vat') or self.vat)
        if not obviar_validacion_ruc:
            ruc = None
            if vals.get('vat'):
                ruc = vals['vat']
            elif not vals.get('vat') and self.vat:
                ruc = self.vat
            if ruc:
                pattern = "^[0-9]+-[0-9]$"
                if re.match(pattern, ruc):
                    ruc_das = str(ruc).split("-")
                    ruc_dig = ruc_das[1]
                    if (str(self.digito_verificador(ruc)) != ruc_dig):
                        raise exceptions.ValidationError(
                            "El digito verificador deberia de ser " + str(self.digito_verificador(ruc)))
                else:
                    raise exceptions.ValidationError("Error de formato de RUC! (Ejemplo: 12345678-9)")
        return

    def digito_verificador(self, ruc):
        ruc_asd = str(ruc).split("-")
        ruc_ci = ruc_asd[0]
        ruc_str = str(ruc_ci)[::-1]
        v_total = 0
        basemax = 11
        k = 2
        for i in range(0, len(ruc_str)):
            if k > basemax:
                k = 2
            v_total += int(ruc_str[i]) * k
            k += 1
            resto = v_total % basemax
        if resto > 1:
            return basemax - resto
        else:
            return 0

    @api.model
    def create(self, vals):
        self.val_ruc(vals)
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        for i in self:
            i.val_ruc(vals)
            return super(ResPartner, i).write(vals)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        result = super(ResPartner, self).name_search(name, args=args, operator=operator, limit=limit)
        if not result:
            result = self.env['res.partner'].search([('vat', 'ilike', name)])
            return result.name_get()
        else:
            return result
