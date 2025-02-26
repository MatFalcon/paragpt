from odoo import api,SUPERUSER_ID

def post_init_hook(cr,registry):
    env=api.Environment(cr,SUPERUSER_ID,{})


    env['ir.config_parameter'].set_param('account.show_line_subtotals_tax_selection','tax_included')