# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo import models, fields, api, tools, _


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        res = super(BaseModel, self).check_access_rights(operation, raise_exception)
        if self._name not in ['res.users.log', 'bus.presence'] and raise_exception and operation != 'read' and self.env.user.has_group('web_readonly_user.group_readonly_user'):
            raise AccessError(_("Sorry, you are not allowed to access this document."))
        return res

    # @api.multi
    # def check_access_rule(self, operation):
    #     if self._name not in ['res.users.log', 'bus.presence'] and operation != 'read' and self.env.user.has_group('web_readonly_user.group_readonly_user'):
    #         raise AccessError(_("Sorry, you are not allowed to access this document."))
    #     return super(BaseModel, self).check_access_rule(operation)


class ResUsers(models.Model):
    _inherit = "res.users"

    is_readonly = fields.Boolean(default=False, help="Set readonly mode.")
    

    def toggle_readonly(self):
        group_id = self.env.ref('web_readonly_user.group_readonly_user', False)
        for rec in self:
            rec.is_readonly = not rec.is_readonly
            rec.update({'groups_id': [(rec.is_readonly and 4 or 3, group_id.id)]})


class IrModelAccess(models.Model):

    _inherit = "ir.model.access"

    @api.model
    @tools.ormcache_context('self.env.uid', 'self.env.su', 'model', 'mode', 'raise_exception', keys=('lang',))
    def check(self, model, mode='read', raise_exception=True):
        res = super(IrModelAccess, self).check(model, mode, raise_exception)
        if self.check_groups('web_readonly_user.group_readonly_user'):
            if mode != 'read':
                return False
        return res


    # @api.model
    # def check_access_rights(self, operation, raise_exception=True):
    #     res = super(IrModelAccess, self).check_access_rights(operation, raise_exception)
    #     if res and operation != 'read' and self.env.user.has_group('web_readonly_user.group_readonly_user'):
    #         raise AccessError(_("Sorry, you are not allowed to access this document."))
    #     return res