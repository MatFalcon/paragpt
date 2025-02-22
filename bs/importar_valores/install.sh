if [[ ! $(python3 -V) =~ "Python 3" ]]; then
    echo "ERROR: Python 3 no está instalado"
    exit
fi

if [[ ! $(pip3 -V) =~ "pip" ]]; then
    echo "ERROR: PIP no está instalado"
    exit
fi

pip3 install -r requirements.txt
python3 schedule_cron.py
