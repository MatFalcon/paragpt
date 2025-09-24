import os

from crontab import CronTab

JOBNAMES = ['importar_liquidaciones', 'importar_sen', 'importar_series','importar_valores','importar_reporte_series', 'importar_transferencia_cartera']
ignore = []

cron = CronTab(user=os.getlogin())

for job in cron:
    if job.comment in JOBNAMES:
        print('El cronjob ya existe.')
        ignore.append(job.comment)

for jobname in JOBNAMES:
    if jobname in ignore:
        continue

    if jobname == JOBNAMES[0]: 
        script = 'importar_liquidaciones.py'
    elif jobname == JOBNAMES[1]:
        script = 'importar_sen.py'
    elif jobname == JOBNAMES[2]:
        script = 'importar_series.py'
    elif jobname == JOBNAMES[3]:
        script = 'importar_valores.py'
    elif jobname == JOBNAMES[4]:
        script = 'importar_reporte_series.py'
    elif jobname == JOBNAMES[5]:
        script = 'importar_transferencia_cartera.py'

    script_path = os.path.join(os.path.dirname(__file__), 'script.py')
    job = cron.new(command=f'python3 -u {script_path} >> ~/{jobname}.log 2>&1', comment=jobname)
    job.setall('0 7 26 * *')
    cron.write()

print('OK')
