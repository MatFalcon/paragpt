# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import xlsxwriter, datetime, io, os, werkzeug, shutil


class ReportesEyOSyJZIP(http.Controller):
    @http.route('/reportes_ministerio_trabajo/reportes_eyo_syj_zip', auth='public')
    def download_empleados_obreros_report(self, kw_aux=False, **kw):
        if kw_aux:
            kw = kw_aux
        if request.env.user.has_group('hr.group_hr_manager'):
            wizard_id = int(kw.get('wizard_id'))
            mtess_reports_slow_server_mode = request.env['ir.config_parameter'].sudo().get_param('mtess_reports_slow_server_mode') == 'True'
            url_for_reports = (request.env['ir.config_parameter'].sudo().get_param('report.url') or
                               request.env['ir.config_parameter'].sudo().get_param('web.base.url'))
            dt = str(datetime.datetime.today())
            companies = request.env['res.company'].sudo().browse([int(id) for id in kw.get('cids').split(',')])
            # os.chdir('/tmp')
            foldername = "Reportes EyO SyJ " + dt
            folderpath = foldername
            zipname = foldername + '.zip'
            if mtess_reports_slow_server_mode or os.system("mkdir '" + folderpath + "'") == 0:
                for company in companies:
                    company_foldername = ''
                    curl_command = []
                    if not mtess_reports_slow_server_mode:
                        company_foldername = folderpath + "/" + company.name
                        os.system("mkdir '" + company_foldername + "'")
                        curl_command = [
                            'curl "' + url_for_reports + '/report/pdf/reportes_ministerio_trabajo_py.',
                            '" -H "Cookie: session_id=' + request.session.sid + '; oe_instance_hide_panel=true" --compressed --output "' + company_foldername + '/',
                            '"'
                        ]

                    sueldos_y_jornales_list = []
                    empleados_y_obreros_list = []
                    for i in range(1, 13):
                        sueldos_y_jornales = request.env['sueldos_y_jornales_zip_model'].sudo().create({
                            'wizard_id': wizard_id,
                            'company_id': company.id,
                            'year': kw.get('year'),
                            'month': str(i),
                        })
                        empleados_y_obreros = request.env['empleados_y_obreros_zip_model'].sudo().create({
                            'wizard_id': wizard_id,
                            'company_id': company.id,
                            'year': kw.get('year'),
                            'month': str(i),
                        })

                        request._cr.commit()
                        sueldos_y_jornales_list.append(str(sueldos_y_jornales.id))
                        empleados_y_obreros_list.append(str(empleados_y_obreros.id))
                        if not mtess_reports_slow_server_mode:
                            os.system(
                                curl_command[0] +
                                'sueldos_y_jornales_zip_t/' +
                                str(sueldos_y_jornales.id) +
                                curl_command[1] +
                                'Sueldos y Jornales - ' + str(i) + '.pdf' +
                                curl_command[2]
                            )
                            os.system(
                                curl_command[0] +
                                'empleados_y_obreros_zip_t/' +
                                str(empleados_y_obreros.id) +
                                curl_command[1] +
                                'Empĺeados y Obreros - ' + str(i) + '.pdf' +
                                curl_command[2]
                            )

                    vacaciones = request.env['vacaciones_zip_model'].sudo().create({
                        'wizard_id': wizard_id,
                        'company_id': company.id,
                        'year': kw.get('year'),
                    })
                    request._cr.commit()
                    if not mtess_reports_slow_server_mode:
                        os.system(
                            curl_command[0] +
                            'vacaciones_zip_t/' +
                            str(vacaciones.id) +
                            curl_command[1] +
                            'Vacaciones.pdf' +
                            curl_command[2]
                        )

                        os.system(
                            'curl "' + request.env['ir.config_parameter'].sudo().get_param(
                                'web.base.url') + '/report/pdf/reportes_ministerio_trabajo_py.vacaciones_zip_t/' + str(
                                vacaciones.id) + '" -H "Cookie: session_id=' + request.session.sid + '; oe_instance_hide_panel=true" --compressed --output "' + company_foldername + '/Vacaciones.pdf"')

                        os.system("echo 'company_id=" + str(company.id) +
                                  "\nempleados_y_obreros_id=[" + ','.join(empleados_y_obreros_list) +
                                  "]\nsueldos_y_jornales_id=[" + ','.join(sueldos_y_jornales_list) +
                                  "]\nvacaciones_id=" + str(vacaciones.id) +
                                  "' > '" + company_foldername + "/debug.txt'")
                if not mtess_reports_slow_server_mode and os.system("zip -r '" + zipname + "' '" + folderpath + "/'") == 0:
                    filepath = os.path.join(zipname)
                    r = http.send_file(filepath, zipname, as_attachment=True)
                    os.remove(filepath)
                    shutil.rmtree(folderpath)
                    return r

        else:
            # return request.redirect('/contactus')
            return werkzeug.utils.redirect('/web/login')

    @http.route('/reportes_ministerio_trabajo/reportes_eyo_syj_zip_xlsx', auth='public')
    def download_mtess_report_xlsx(self, kw_aux=False, **kw):
        if kw_aux:
            kw = kw_aux
        if request.env.user.has_group('hr.group_hr_manager'):
            wizard_id = int(kw.get('wizard_id'))
            mtess_reports_slow_server_mode = request.env['ir.config_parameter'].sudo().get_param('mtess_reports_slow_server_mode') == 'True'
            dt = str(datetime.datetime.today())
            companies = request.env['res.company'].sudo().browse([int(id) for id in kw.get('cids').split(',')])
            # os.chdir('/tmp')
            foldername = "Reportes EyO SyJ " + dt
            folderpath = foldername
            if mtess_reports_slow_server_mode or os.system("mkdir '" + folderpath + "'") == 0:
                for company in companies:
                    company_foldername = folderpath + "/" + company.name.replace("'", "")
                    os.system("mkdir '" + company_foldername + "'")

                    company_foldername = ''
                    if not mtess_reports_slow_server_mode:
                        company_foldername = folderpath + "/" + company.name.replace("'", "")
                        os.system("mkdir '" + company_foldername + "'")

                    empleados_y_obreros = request.env['empleados_y_obreros_zip_model'].sudo().create({
                        'wizard_id': wizard_id,
                        'company_id': company.id,
                        'year': kw.get('year'),
                        'month': '1',
                        'is_report_for_xlsx': True
                    })
                    request._cr.commit()
                    if not mtess_reports_slow_server_mode:
                        empleados_y_obreros.create_empleados_obreros_xlsx_file(dt)
                        empleados_y_obreros.create_sueldos_y_jornales_xlsx_file(dt)
                        empleados_y_obreros.create_resumen_general_mtess_xlsx_file(dt)
                if not mtess_reports_slow_server_mode and os.system("zip -r '" + foldername + ".zip' '" + folderpath + "/'") == 0:
                    filepath = os.path.join(foldername + '.zip')
                    r = http.send_file(filepath, foldername + '.zip', as_attachment=True)
                    os.remove(filepath)
                    shutil.rmtree(folderpath)
                    return r
        else:
            # return request.redirect('/contactus')
            return werkzeug.utils.redirect('/web/login')


class ReporteSETZIP(http.Controller):
    @http.route('/reportes_ministerio_trabajo/reporte_set_zip', auth='public')
    def download_set_report(self, **kw):
        if request.env.user.has_group('hr.group_hr_manager'):
            dt = str(datetime.datetime.today())
            year = kw.get('year')
            companies = request.env['res.company'].sudo().browse([int(id) for id in kw.get('cids').split(',')])
            os.chdir('/tmp')
            foldername = "Reporte SET " + dt
            folderpath = foldername
            if os.system("mkdir '" + folderpath + "'") == 0:
                for company in companies:
                    company_foldername = folderpath + "/" + company.name
                    os.system("mkdir '" + company_foldername + "'")
                    # empleados_y_obreros = request.env['reporte_set_zip_model'].sudo().create({
                    #     'company_id': company.id,
                    #     'year': kw.get('year'),
                    #     'month': kw.get('month')
                    # })
                    # request._cr.commit()
                    nominas_periodo = request.env['hr.payslip'].sudo().search([
                        ('state', '=', 'done'),
                        ('contract_id.company_id', '=', company.id),
                    ]).filtered(lambda x: x.date_to.year == int(year))
                    contenido_txt = ''
                    contenido_txt_cabecera = ''
                    monto_bruto_sin_descuentos_total = 0
                    # lineas
                    for employee in nominas_periodo.contract_id.employee_id:
                        employee_payslips = nominas_periodo.filtered(lambda x: x.contract_id.employee_id == employee)
                        employee_payslips_normal = employee_payslips.filtered(lambda x: x.structure_type_tag == 'normal')
                        employee_payslips_liquidacion = employee_payslips.filtered(lambda x: x.structure_type_tag == 'liquidacion')
                        employee_payslips_aguinaldo = employee_payslips.filtered(lambda x: x.structure_type_tag == 'aguinaldo')
                        # 1
                        contenido_txt += '\n2;'
                        # 2
                        contenido_txt += (employee.identification_id.split('-')[0] if employee.identification_id else '') + ';'
                        # 3
                        contenido_txt += (employee.identification_id.split('-')[
                                              1] if employee.identification_id and '-' in employee.identification_id else '') + ';'
                        # 4
                        contenido_txt += (employee.apellido.split(' ', 1)[0] if employee.apellido else '') + ';'
                        # 5
                        contenido_txt += (employee.apellido.split(' ', 1)[1] if employee.apellido and ' ' in employee.apellido else '') + ';'
                        # 6
                        contenido_txt += (employee.nombre.split(' ', 1)[0] if employee.nombre else '') + ';'
                        # 7
                        contenido_txt += (employee.nombre.split(' ', 1)[1] if employee.nombre and ' ' in employee.nombre else '') + ';'
                        # 8
                        contenido_txt += '1;'
                        # 9
                        monto_bruto_sin_descuentos = int(
                            sum(employee_payslips_normal.line_ids.filtered(lambda x: x.code == 'GROSS').mapped('total'))
                        )
                        monto_bruto_sin_descuentos += int(
                            sum(employee_payslips_liquidacion.line_ids.filtered(lambda x: x.code == 'GROSS').mapped('total'))
                        )
                        monto_bruto_sin_descuentos += int(
                            sum(employee_payslips_aguinaldo.line_ids.filtered(lambda x: x.code == 'GROSS').mapped('total'))
                        )
                        monto_bruto_sin_descuentos_total += monto_bruto_sin_descuentos
                        contenido_txt += str(monto_bruto_sin_descuentos) + ';'
                        # 10
                        contenido_txt += '0;'
                        # 11
                        descuento_por_seguro_social = int(
                            sum(employee_payslips_normal.line_ids.filtered(lambda x: x.code in ['IPS']).mapped('total'))
                        )
                        descuento_por_seguro_social += int(
                            sum(employee_payslips_liquidacion.line_ids.filtered(lambda x: x.code in ['IPS']).mapped('total'))
                        )
                        descuento_por_seguro_social += int(
                            sum(employee_payslips_aguinaldo.line_ids.filtered(lambda x: x.code in ['IPS']).mapped('total'))
                        )
                        contenido_txt += str(descuento_por_seguro_social) + ';'
                        # 12
                        otros_descuentos = int(
                            sum(employee_payslips_normal.line_ids.filtered(lambda x: x.category_id.code == 'DED' and x.code not in ['IPS']).mapped('total'))
                        )
                        otros_descuentos += int(
                            sum(employee_payslips_liquidacion.line_ids.filtered(lambda x: x.category_id.code == 'DED' and x.code not in ['IPS']).mapped(
                                'total'))
                        )
                        otros_descuentos += int(
                            sum(employee_payslips_aguinaldo.line_ids.filtered(lambda x: x.category_id.code == 'DED' and x.code not in ['IPS']).mapped('total'))
                        )
                        contenido_txt += str(otros_descuentos) + ';'
                        # 13
                        monto_aguinaldo = int(
                            sum(employee_payslips_aguinaldo.line_ids.filtered(lambda x: x.code == 'GROSS').mapped('total'))
                        )
                        contenido_txt += str(monto_aguinaldo) + ';'
                        # 14
                        contenido_txt += (employee.private_email or '') + ';'
                        # 15
                        contenido_txt += '16;'
                        # 16
                        contenido_txt += '5523;'
                        # 17
                        contenido_txt += ';'
                        # 18
                        direccion_completa = []
                        if employee.address_home_id:
                            direccion_completa_street = ''
                            if employee.address_home_id.street:
                                direccion_completa_street += employee.address_home_id.street
                                if employee.address_home_id.street2:
                                    direccion_completa_street += ' ' + employee.address_home_id.street2
                                direccion_completa.append(direccion_completa_street)
                            if employee.address_home_id.city:
                                direccion_completa.append(employee.address_home_id.city)
                            if employee.address_home_id.state_id:
                                direccion_completa.append(employee.address_home_id.state_id.name)
                            if employee.address_home_id.country_id:
                                direccion_completa.append(employee.address_home_id.country_id.name)
                        contenido_txt += (', '.join(direccion_completa)) + ';'
                        # 19
                        contenido_txt += ';'
                        # 20
                        contenido_txt += ';'
                        # 21
                        contenido_txt += ';'
                        # 22
                        contenido_txt += (employee.phone or '') + ';'
                        # 23
                        contenido_txt += '1'
                    # Cabecera
                    contenido_txt_cabecera += '1;'
                    contenido_txt_cabecera += (company.vat.split('-')[0] if company.vat else '') + ';'
                    contenido_txt_cabecera += year + ';'
                    contenido_txt_cabecera += str(len(nominas_periodo.contract_id.employee_id)) + ';'
                    contenido_txt_cabecera += str(monto_bruto_sin_descuentos_total) + ';'

                    contenido_txt = contenido_txt_cabecera + contenido_txt
                    os.system("echo '" + contenido_txt + "' > '" + company_foldername + "/" + (
                        company.vat if company.vat else '') + ".txt'")
                if os.system("zip -r '" + foldername + ".zip' '" + folderpath + "/'") == 0:
                    filepath = os.path.join(foldername + '.zip')
                    r = http.send_file(filepath, foldername + '.zip', as_attachment=True)
                    # os.remove(filepath)
                    return r
        else:
            # return request.redirect('/contactus')
            return werkzeug.utils.redirect('/web/login')
