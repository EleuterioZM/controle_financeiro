from flask import Flask, render_template, request, redirect
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Usa o backend não interativo
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Caminho para o arquivo CSV
CSV_PATH = "dados.csv"

# Função para inicializar o arquivo CSV (se não existir)
def inicializar_csv():
    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=["Data", "Valor", "Categoria", "Periodo"])
        df.to_csv(CSV_PATH, index=False)
    else:
        # Verifica se o arquivo já existe e está vazio
        with open(CSV_PATH, "r") as f:
            if not f.read().strip():  # Se o arquivo estiver vazio
                df = pd.DataFrame(columns=["Data", "Valor", "Categoria", "Periodo"])
                df.to_csv(CSV_PATH, index=False)

# Função para adicionar gastos
def adicionar_gasto(data, valor, categoria, periodo):
    df = pd.read_csv(CSV_PATH)
    novo_gasto = {"Data": [data], "Valor": [valor], "Categoria": [categoria], "Periodo": [periodo]}
    df_novo = pd.DataFrame(novo_gasto)
    df = pd.concat([df, df_novo], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)

# Função para calcular saldo
def calcular_saldo(renda, periodo):
    df = pd.read_csv(CSV_PATH)
    df_periodo = df[df["Periodo"] == periodo]
    total_gastos = df_periodo["Valor"].sum()
    saldo = renda - total_gastos
    return saldo, total_gastos

# Função para gerar gráficos
def gerar_graficos(periodo):
    df = pd.read_csv(CSV_PATH)
    df_periodo = df[df["Periodo"] == periodo]
    if not df_periodo.empty:
        plt.figure()  # Cria uma nova figura
        df_periodo.groupby("Categoria")["Valor"].sum().plot(kind="bar")
        plt.title(f"Gastos por Categoria ({periodo})")
        plt.xlabel("Categoria")
        plt.ylabel("Valor Gasto (R$)")
        plt.tight_layout()  # Ajusta o layout para evitar cortes
        plt.savefig("static/gastos.png")  # Salva o gráfico
        plt.close()  # Fecha a figura para liberar memória
    else:
        # Se não houver dados, remove o gráfico antigo (se existir)
        if os.path.exists("static/gastos.png"):
            os.remove("static/gastos.png")

# Função para gerar extrato
def gerar_extrato(renda, periodo):
    df = pd.read_csv(CSV_PATH)
    df_periodo = df[df["Periodo"] == periodo]
    total_gastos = df_periodo["Valor"].sum()
    saldo = renda - total_gastos
    gastos_por_categoria = df_periodo.groupby("Categoria")["Valor"].sum().to_dict()

    extrato = {
        "renda": renda,
        "total_gastos": total_gastos,
        "saldo": saldo,
        "gastos_por_categoria": gastos_por_categoria,
        "periodo": periodo,
    }
    return extrato

# Rota principal
@app.route("/", methods=["GET", "POST"])
def index():
    try:
        # Inicializa o CSV
        inicializar_csv()

        # Variáveis para exibir na interface
        saldo = None
        total_gastos = None
        extrato = None
        alerta = None

        if request.method == "POST":
            # Obtém os dados do formulário
            periodo = request.form["periodo"]
            renda = float(request.form["renda"])
            data = request.form["data"]
            valor = float(request.form["valor"])
            categoria = request.form["categoria"]

            # Adiciona o gasto
            adicionar_gasto(data, valor, categoria, periodo)

            # Calcula o saldo
            saldo, total_gastos = calcular_saldo(renda, periodo)

            # Verifica se o orçamento foi estourado
            if saldo < 0:
                alerta = f"ALERTA: Orçamento estourado! Você gastou R$ {-saldo:.2f} a mais."

            # Gera gráficos
            gerar_graficos(periodo)

            # Gera extrato se for o último dia do período
            hoje = datetime.now().date()
            if periodo == "semanal":
                fim_periodo = (datetime.strptime(data, "%Y-%m-%d") + timedelta(days=6)).date()
            elif periodo == "mensal":
                fim_periodo = (datetime.strptime(data, "%Y-%m-%d") + timedelta(days=30)).date()
            else:  # anual
                fim_periodo = (datetime.strptime(data, "%Y-%m-%d") + timedelta(days=365)).date()

            if hoje >= fim_periodo:
                extrato = gerar_extrato(renda, periodo)

        # Renderiza a página com os resultados
        return render_template("index.html", saldo=saldo, total_gastos=total_gastos, extrato=extrato, alerta=alerta)

    except Exception as e:
        # Em caso de erro, exibe uma mensagem amigável
        return f"Ocorreu um erro: {str(e)}", 500

# Executa o aplicativo
if __name__ == "__main__":
    # Cria a pasta 'static' se não existir
    if not os.path.exists("static"):
        os.makedirs("static")

    # Inicia o servidor Flask
    app.run(debug=True)