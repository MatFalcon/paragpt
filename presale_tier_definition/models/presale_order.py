# Copyright 2017 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import ValidationError


class PresaleOrder(models.Model):
    _name = "presale.order"
    _inherit = ["presale.order", "tier.validation"]
    _state_from = ["Borrador"]
    _state_to = ["Aprobado"]

    _tier_validation_manual_config = False