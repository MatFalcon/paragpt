import os
import fileinput

def comment_out_lines(file_path, imports):
    try:
        with fileinput.FileInput(file_path, inplace=True) as file:
            for line in file:
                for imp in imports:
                    if imp in line:
                        line = '#' + line
                print(line, end='')
    except FileNotFoundError:
        print(f"El archivo '{file_path}' no existe.")

def process_files(directory, imports):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                comment_out_lines(file_path, imports)

if __name__ == "__main__":
    directory = '/home/user/Descargas/localizacion/odoo_paraguay/bolsa_valores'  # RUTA DE LA CARPETA DONDE CREA PROBLEMA LAS IMPORTACIONES
#    imports_to_comment = ['from msal import PublicClientApplication']
    process_files(directory, imports_to_comment)

