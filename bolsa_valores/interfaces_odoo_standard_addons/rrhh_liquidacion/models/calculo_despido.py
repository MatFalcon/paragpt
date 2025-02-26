from dateutil.relativedelta import relativedelta
import datetime, math

#                                               Ejemplo de uso:
# import calculo_liquidacion
#
# calculo_liquidacion.salario_promedio = 3500000
# calculo_liquidacion.ipsStatus=True
#
# calculo_liquidacion.calcular_antiguedad(fecha_inicio='2008-04-07',fecha_final='2020-03-11',causa_justificada=False)
# calculo_liquidacion.calcular_salarios(tipoSueldo='30',knowSalarioProm=True)
#
# calculo_liquidacion.getLiquidacion(
# 		Sueldo_Prom_Diario=calculo_liquidacion.salario_diario,
# 		preaviso_Correspondido=calculo_liquidacion.getPreaviso(antig_a=calculo_liquidacion.antiguedadOj['years'],antig_m=calculo_liquidacion.antiguedadOj['months']),
# 		preaviso_Dado=30,
# 		vacaciones_Causada=calculo_liquidacion.getVacaciones(antig_a=calculo_liquidacion.antiguedadOj['years'],antig_m=calculo_liquidacion.antiguedadOj['months']),
# 		vacaciones_Causada_Dadas=30,
# 		vacaciones_Correspondida=calculo_liquidacion.getVacacionesProp(antig_a=calculo_liquidacion.antiguedadOj['years'],antig_m=calculo_liquidacion.antiguedadOj['months']),
# 		vacaciones_Dada=15,
# 		vacaciones_Atrasadas=0,
# 		fecha_inicio_a=2008,
# 		fecha_inicio_m=4,
# 		fecha_inicio_d=7,
# 		fecha_final_a=2020,
# 		fecha_final_m=3,
# 		fecha_final_d=11,
# 		perprueba=False,
# 		justificada=False
# 	)


# global dias_Falta_Pagar
# global advertAnt10noJuicio
# global advertAnt03
# global salario_promedio
# global antiguedadOj
# global salario_diario
# global liq_diasTrabaj
# global liq_Preaviso
# global liq_vaCau
# global liq_diasVacPropor
# global liq_vaCauAnt
# global liq_indemnizacion
# global liq_vaPropor
# global liq_aquin
# global liq_SubTot_1
# global liq_SubTot_2
# global liq_SubTot_3
# global liq_ips
# global ipsStatus
dias_Falta_Pagar = 0
advertAnt10noJuicio = 0
advertAnt03 = 0
salario_promedio = 0
antiguedadOj = {}
salario_diario = 0
liq_diasTrabaj = 0
liq_Preaviso = 0
liq_vaCau = 0
liq_diasVacPropor = 0
liq_vaCauAnt = 0
liq_indemnizacion_dias = 0
liq_indemnizacion = 0
liq_vaPropor = 0
liq_aquin = 0
liq_SubTot_1 = 0
liq_SubTot_2 = 0
liq_SubTot_3 = 0
liq_ips = 0
liq_amh = 0
ipsStatus = 0
amhStatus = 0


def calcular_antiguedad(fecha_inicio, fecha_final, causa_justificada):
    a = 0
    global dias_Falta_Pagar
    global advertAnt10noJuicio
    global advertAnt03
    global antiguedadOj
    global salario_diario

    if fecha_inicio and fecha_final:

        fecha_final_d = fecha_final.day

        d1 = fecha_inicio
        d2 = fecha_final

        antiguedadOj = {
            'years': relativedelta(d2, d1).years,
            'months': relativedelta(d2, d1).months,
            'days': relativedelta(d2, d1).days
        }

        dias_Falta_Pagar = fecha_final_d
        # $('#dias_Falta_Pagar').val(fecha_final_d);

        if ((antiguedadOj['years'] == 9 and antiguedadOj['months'] == 6 and
             antiguedadOj['days'] > 0) or (antiguedadOj['years'] == 9 and
                                           antiguedadOj['months'] > 6) or (antiguedadOj['years'] > 9)):
            # $("#antiguedadInfoBox").attr("data-content",
            #     "Si un trabajador ha prestado mas de 9 años y 6 meses de servicio ininterrumpido, este adquiere estabilidad laboral y no puede ser despedido sin justa causa  previamente probada en juicio"
            # );

            # SI TIENE MAS DE 10 ANHOS Y NO TIENE CAUSA JUSTIFICADA
            advertAnt10noJuicio = True if causa_justificada else False

        # OPCIONES SI TENES MAS DE 10 ANHOS

        if ((antiguedadOj['years'] == 0) and (
                (antiguedadOj['months'] <= 2) or (antiguedadOj['months'] == 3 and antiguedadOj['days'] < 1))):
            advertAnt03 = True
            antiguedadOj['prueba'] = True
        else:
            advertAnt03 = False
            antiguedadOj['prueba'] = False

        # OPCIONES SI TENES MENOS DE 3 MESES


def roundUpToHundred(n):
    return round(n)
    return int(math.ceil(n / 100.0)) * 100


def calcular_salarios(tipoSueldo, knowSalarioProm, salario_ant=False):
    a = 0
    global salario_promedio
    global salario_diario

    Sueldo_Prom = 0
    if tipoSueldo in ['30', '24']:
        if not knowSalarioProm:
            # if not salario_ant:
            #     raise Exception('El tercer argumento debe de contener un array de numeros')
            cobradoMes = 0
            divididoMes = 0
            for i in range(0, len(salario_ant)):
                cobradoMes = salario_ant[i]
                if cobradoMes:
                    divididoMes = divididoMes + 1
                    Sueldo_Prom = Sueldo_Prom + cobradoMes

            Sueldo_Prom = (Sueldo_Prom / divididoMes) if divididoMes else 0
            salario_promedio = Sueldo_Prom
        else:
            inputVal = salario_promedio
            Sueldo_Prom = inputVal

        if Sueldo_Prom != 0 and tipoSueldo:
            dias = 30 if tipoSueldo == '30' else (26 if tipoSueldo == '24' else 0)
            Sueldo_Prom_Diario = Sueldo_Prom / dias
            salario_diario = Sueldo_Prom_Diario

    else:
        # ES JORNALERO
        Sueldo_Prom_Diario = salario_diario


def getPreaviso(antig_a):
    if (antig_a < 1):
        dias = 30
    elif (antig_a <= 4):
        dias = 45
    elif (antig_a < 10):
        dias = 60
    else:
        dias = 90
    return dias


def getVacaciones(antig_a):
    if (antig_a < 1):
        dias = 0
    elif (antig_a <= 4):
        dias = 12
    elif (antig_a < 10):
        dias = 18
    else:
        dias = 30

    return dias


def getVacacionesProp():
    global antiguedadOj

    antAnho = antiguedadOj['years']
    month = antiguedadOj['months']
    month_Salida = month
    if (antAnho < 0):
        dias = 0
    elif (antAnho <= 4):
        dias = 12
    elif (antAnho <= 9):
        dias = 18
    else:
        dias = 30

    dias = (month_Salida / 12) * dias
    return round(dias, 1)


def getLiquidacion(Sueldo_Prom_Diario, preaviso_Correspondido, preaviso_Dado, vacaciones_Causada,
                   vacaciones_Causada_Dadas, vacaciones_Correspondida, vacaciones_Dada, vacaciones_Atrasadas,
                   fecha_final_a, fecha_final_m, fecha_final_d, fecha_inicio_a, fecha_inicio_m, fecha_inicio_d,
                   antiguedadOj, perprueba, justificada, otros_haberes, otros_deberes, tipo_empleado,
                   salario_diario_real, dias_mes_aun_no_abonados):
    a = 0
    global dias_Falta_Pagar
    global liq_diasTrabaj
    global liq_Preaviso
    global liq_indemnizacion_dias
    global liq_indemnizacion
    global liq_vaCau
    global liq_vaCauAnt
    global liq_vaPropor
    global liq_aquin
    global liq_SubTot_1
    global liq_SubTot_2
    global liq_SubTot_3
    global liq_ips
    global liq_amh
    global ipsStatus
    global amhStatus

    liq_SubTot_1 = 0
    liq_diasTrabaj = 0
    liq_Preaviso = 0
    liq_Indemniz = 0
    liq_Vacaciones = 0
    liq_VacacionesAtras = 0
    liq_diasVacPropor = 0
    liq_AguinPropor = 0
    liq_ipsStatus = 0
    # liq_diasTrabaj = dias_mes_aun_no_abonados * (Sueldo_Prom_Diario if tipo_empleado == '30' else salario_real)
    liq_diasTrabaj = dias_mes_aun_no_abonados * (salario_diario_real or Sueldo_Prom_Diario)

    liq_diasTrabaj = roundUpToHundred(liq_diasTrabaj)

    liq_diasPreaviso = preaviso_Correspondido
    liq_diasPreavisoDado = preaviso_Dado

    if liq_diasPreaviso:
        liq_Preaviso = ((liq_diasPreaviso - liq_diasPreavisoDado) * Sueldo_Prom_Diario)
        liq_Preaviso = roundUpToHundred(liq_Preaviso)

    if antiguedadOj:
        antAnho = antiguedadOj['years']
        month = antiguedadOj['months']
        dias_indem = 0
        if (antAnho < 10):
            dias_indem = 15
        else:
            dias_indem = 30

        if (month >= 6):
            antAnho += 1

        if (antAnho > 0):
            dias_indem = (dias_indem * antAnho)
            liq_Indemniz = (dias_indem * Sueldo_Prom_Diario)
        else:
            liq_Indemniz = (dias_indem * Sueldo_Prom_Diario)

        liq_Indemniz = roundUpToHundred(liq_Indemniz)
        liq_indemnizacion_dias = dias_indem
        liq_indemnizacion = liq_Indemniz

    liq_vacacionesCausada = vacaciones_Causada
    liq_vacacionesCausadaDada = vacaciones_Causada_Dadas
    if liq_vacacionesCausada:
        liq_vacacionesCausada = (
                (liq_vacacionesCausada - liq_vacacionesCausadaDada) * (salario_diario_real or Sueldo_Prom_Diario))
        liq_vacacionesCausada = roundUpToHundred(liq_vacacionesCausada)
        if (antiguedadOj['months'] >= 6):
            liq_vacacionesCausada = liq_vacacionesCausada * 2

        liq_vaCau = liq_vacacionesCausada
    else:
        liq_vaCau = 0

    liq_diasVacaciones = vacaciones_Correspondida
    liq_diasVacacionesDada = vacaciones_Dada
    if liq_diasVacaciones:
        liq_diasVacPropor = (
                (liq_diasVacaciones - liq_diasVacacionesDada) * (salario_diario_real or Sueldo_Prom_Diario))
        liq_diasVacPropor = roundUpToHundred(liq_diasVacPropor)
        liq_vaPropor = liq_diasVacPropor

    liq_diasVacacionesAtras = vacaciones_Atrasadas
    if not liq_diasVacacionesAtras:
        liq_diasVacacionesAtras = 0

    liq_VacacionesAtras = ((liq_diasVacacionesAtras) * (salario_diario_real or Sueldo_Prom_Diario))
    # if antiguedadOj['months'] >= 6:
    if liq_diasVacacionesAtras >= 120:
        liq_VacacionesAtras = liq_VacacionesAtras * 2

    liq_VacacionesAtras = roundUpToHundred(liq_VacacionesAtras)
    liq_vaCauAnt = liq_VacacionesAtras * 2

    if antiguedadOj:
        antAnho = fecha_final_a
        antmonth = fecha_final_m
        antday = fecha_final_d
        incAnho = fecha_inicio_a
        incmonth = fecha_inicio_m
        incday = fecha_inicio_d
        if ((antiguedadOj['years'] >= 1) or (antAnho != incAnho)):
            liq_AguinPropor = ((((antmonth - 1) * 30) * Sueldo_Prom_Diario) + liq_vaPropor + liq_diasTrabaj) / 12
            liq_AguinPropor = roundUpToHundred(liq_AguinPropor)
            liq_aquin = liq_AguinPropor
        else:
            resmonth = antmonth - incmonth
            liq_AguinPropor = ((resmonth * 30) * Sueldo_Prom_Diario + liq_vaPropor + liq_diasTrabaj) / 12
            liq_AguinPropor = roundUpToHundred(liq_AguinPropor)
            liq_aquin = liq_AguinPropor

    if perprueba:
        liq_SubTot_1 = liq_diasTrabaj + liq_Vacaciones + liq_VacacionesAtras + liq_diasVacPropor + liq_vacacionesCausada
        liq_preaviso = 0
        liq_indemnizacion = 0
    else:
        if justificada:
            liq_SubTot_1 = liq_diasTrabaj + liq_Vacaciones + liq_VacacionesAtras + liq_vacacionesCausada
            liq_indemnizacion = 0
            liq_preaviso = 0
        else:
            liq_SubTot_1 = liq_diasTrabaj + liq_Preaviso + liq_Indemniz + liq_Vacaciones + liq_VacacionesAtras + liq_diasVacPropor + liq_vacacionesCausada

    liq_SubTot_1 = liq_SubTot_1 + otros_haberes - otros_deberes

    if ipsStatus:
        ipsStatus = liq_SubTot_1 * 0.09
    else:
        ipsStatus = 0
        if amhStatus:
            amhStatus = liq_SubTot_1 * 0.05

    ipsStatus = roundUpToHundred(ipsStatus)
    amhStatus = roundUpToHundred(amhStatus)
    liq_ips = ipsStatus
    liq_amh = amhStatus
    liq_SubTot_2 = liq_SubTot_1 - ipsStatus - amhStatus
    liq_SubTot_3 = liq_SubTot_2 + liq_AguinPropor
