import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import psycopg2
import math


def escolher_arquivo():
    caminho = filedialog.askopenfilename(
        title="Selecione arquivo CSV ou Excel",
        filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx;*.xls")]
    )
    entry_arquivo.delete(0, tk.END)
    entry_arquivo.insert(0, caminho)


def map_dtype(dtype):
    if 'int' in str(dtype):
        return 'INTEGER'
    elif 'float' in str(dtype):
        return 'NUMERIC'
    elif 'datetime' in str(dtype):
        return 'TIMESTAMP'
    else:
        return 'VARCHAR(255)'


def gerar_create_table(df, table_name):
    columns_with_types = []
    for col in df.columns:
        col_type = map_dtype(df[col].dtype)
        columns_with_types.append(f"{col} {col_type}")
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n  " + ",\n  ".join(columns_with_types) + "\n);\n"


def gerar_insert(df, table_name):
    columns = ', '.join(df.columns)
    values_list = []
    for _, row in df.iterrows():
        values = []
        for v in row.values:
            if pd.isna(v) or (isinstance(v, float) and math.isnan(v)):
                values.append('NULL')
            elif isinstance(v, pd.Timestamp):
                values.append(f"'{v.strftime('%Y-%m-%d %H:%M:%S')}'")
            elif isinstance(v, str):
                v_safe = v.replace("'", "''")
                values.append(f"'{v_safe}'")
            else:
                values.append(str(v))
        values_list.append(f"({', '.join(values)})")
    values_str = ',\n  '.join(values_list)
    return f"INSERT INTO {table_name} ({columns})\nVALUES\n  {values_str};"

def importar_para_postgres():
    caminho_arquivo = entry_arquivo.get()
    db_name = entry_db.get()
    table_name = entry_table.get()
    user = entry_user.get()
    password = entry_password.get()
    host = entry_host.get() or 'localhost'

    if not os.path.isfile(caminho_arquivo):
        messagebox.showerror("Erro", "Arquivo inválido ou não selecionado.")
        return

    try:
        if caminho_arquivo.lower().endswith('.csv'):
            df = pd.read_csv(caminho_arquivo)
        else:
            df = pd.read_excel(caminho_arquivo)

        for col in df.columns:
            if 'data' in col.lower():
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        create_sql = gerar_create_table(df, table_name)
        insert_sql = gerar_insert(df, table_name)

        conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host)
        cur = conn.cursor()
        cur.execute(create_sql)
        conn.commit()
        cur.execute(insert_sql)
        conn.commit()
        cur.close()
        conn.close()

        messagebox.showinfo("Sucesso", f"Dados importados para a tabela '{table_name}' no banco '{db_name}' com sucesso!")

    except Exception as e:
        mensagem = f"Falha no importação : {str(e)}" 
        messagebox.showerror("Erro", mensagem)
        print(mensagem)



def alternar_caminho():
    if mostrar_caminho.get():
        entry_arquivo.config(show='*')
    else:
        entry_arquivo.config(show='')


root = tk.Tk()
root.title("Importador CSV/Excel para PostgreSQL")

mostrar_caminho = tk.BooleanVar(value=True)
tk.Label(root, text="Arquivo CSV/Excel:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
entry_arquivo = tk.Entry(root, width=35, justify="left", show='')
entry_arquivo.grid(row=0, column=1, sticky="w", padx=4, pady=4)
tk.Button(root, text="Selecionar", command=escolher_arquivo).grid(row=0, column=2, sticky="w", padx=4, pady=4)
tk.Checkbutton(
    root,
    text="Ocultar caminho",
    variable=mostrar_caminho,
    command=alternar_caminho
).grid(row=0, column=3, sticky="w", padx=8, pady=4)
alternar_caminho()

tk.Label(root, text="Database:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
entry_db = tk.Entry(root, width=35, justify="left")
entry_db.grid(row=1, column=1, sticky="w", padx=4, pady=4)

tk.Label(root, text="Nome da Tabela:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
entry_table = tk.Entry(root, width=35, justify="left")
entry_table.grid(row=2, column=1, sticky="w", padx=4, pady=4)

tk.Label(root, text="Usuário:").grid(row=3, column=0, sticky="w", padx=8, pady=4)
entry_user = tk.Entry(root, width=35, justify="left")
entry_user.grid(row=3, column=1, sticky="w", padx=4, pady=4)

tk.Label(root, text="Senha:").grid(row=4, column=0, sticky="w", padx=8, pady=4)
entry_password = tk.Entry(root, show='*', width=35, justify="left")
entry_password.grid(row=4, column=1, sticky="w", padx=4, pady=4)

tk.Label(root, text="Host:").grid(row=5, column=0, sticky="w", padx=8, pady=4)
entry_host = tk.Entry(root, width=35, justify="left")
entry_host.grid(row=5, column=1, sticky="w", padx=4, pady=4)
entry_host.insert(0, 'localhost')

tk.Button(root, text="Importar", command=importar_para_postgres, width=15)\
    .grid(row=6, column=1, sticky="w", padx=4, pady=10)
tk.Button(root, text="Sair", command=root.destroy, width=11)\
    .grid(row=6, column=2, sticky="w", padx=4, pady=10)

root.columnconfigure(1, weight=1)

root.mainloop()
