# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

import datetime, os, shutil


class ReportesEyOSyJSlowMode(http.Controller):
    @http.route('/reportes_ministerio_trabajo/slow_mode/reporte_xlsx_eyo', auth='public')
    def download_eyo_report_slow_mode(self, **kw):
        # reportes_ministerio_trabajo_py/controllers/controllers_slow_mode.py
        dt = str(datetime.datetime.today())
        foldername = "Reportes EyO SyJ " + dt
        folderpath = foldername
        eyo_id = request.env['empleados_y_obreros_zip_model'].sudo().browse(int(kw.get('eyo_id')))

        if os.system("mkdir '" + folderpath + "'") == 0:
            company_foldername = folderpath + "/" + eyo_id.company_id.name.replace("'", "")
            os.system("mkdir '" + company_foldername + "'")
            eyo_id.create_empleados_obreros_xlsx_file(dt)
            filepath = os.path.join(
                company_foldername +
                '/Empleados y Obreros ' +
                str(eyo_id.year) +
                ' - ' +
                eyo_id.company_id.name.replace("'", "") +
                ' - ' +
                (eyo_id.company_id.nro_patronal or '') +
                '.xlsx'
            )

            r = http.send_file(filepath, filepath, as_attachment=True)
            os.remove(filepath)
            shutil.rmtree(folderpath)
            return r

    @http.route('/reportes_ministerio_trabajo/slow_mode/reporte_xlsx_syj', auth='public')
    def download_syj_report_slow_mode(self, **kw):
        # reportes_ministerio_trabajo_py/controllers/controllers_slow_mode.py
        dt = str(datetime.datetime.today())
        foldername = "Reportes EyO SyJ " + dt
        folderpath = foldername
        eyo_id = request.env['empleados_y_obreros_zip_model'].sudo().browse(int(kw.get('eyo_id')))

        if os.system("mkdir '" + folderpath + "'") == 0:
            company_foldername = folderpath + "/" + eyo_id.company_id.name.replace("'", "")
            os.system("mkdir '" + company_foldername + "'")
            eyo_id.create_sueldos_y_jornales_xlsx_file(dt)
            filepath = os.path.join(
                company_foldername +
                '/Sueldos y Jornales ' +
                str(eyo_id.year) +
                ' - ' +
                eyo_id.company_id.name.replace("'", "") +
                ' - ' +
                (eyo_id.company_id.nro_patronal or '') +
                '.xlsx'
            )

            r = http.send_file(filepath, filepath, as_attachment=True)
            os.remove(filepath)
            shutil.rmtree(folderpath)
            return r

    @http.route('/reportes_ministerio_trabajo/slow_mode/reporte_xlsx_rg', auth='public')
    def download_rg_report_slow_mode(self, **kw):
        # reportes_ministerio_trabajo_py/controllers/controllers_slow_mode.py
        dt = str(datetime.datetime.today())
        foldername = "Reportes EyO SyJ " + dt
        folderpath = foldername
        eyo_id = request.env['empleados_y_obreros_zip_model'].sudo().browse(int(kw.get('eyo_id')))

        if os.system("mkdir '" + folderpath + "'") == 0:
            company_foldername = folderpath + "/" + eyo_id.company_id.name.replace("'", "")
            os.system("mkdir '" + company_foldername + "'")
            eyo_id.create_resumen_general_mtess_xlsx_file(dt)
            filepath = os.path.join(
                company_foldername +
                '/Resumen General ' +
                str(eyo_id.year) +
                ' - ' +
                eyo_id.company_id.name.replace("'", "") +
                ' - ' +
                (eyo_id.company_id.nro_patronal or '') +
                '.xlsx'
            )

            r = http.send_file(filepath, filepath, as_attachment=True)
            os.remove(filepath)
            shutil.rmtree(folderpath)
            return r
