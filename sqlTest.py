import psycopg2
import psycopg2.extras
import json
from scipy.fft import fft
import scipy.signal as signal 
import numpy as np
import plotly.graph_objects as go
from config import db_config

# Substitua as configurações pelos valores do arquivo config.py
host = db_config['host']
port = db_config['port']
database = db_config['database']
user = db_config['user']
password = db_config['password']

# Estabelece a conexão com o banco de dados
conexao = psycopg2.connect(host=host, database=database, user=user, password=password)

# Cria um cursor para executar a consulta
cursor = conexao.cursor(cursor_factory=psycopg2.extras.DictCursor)

consulta_sql_ids = """
SELECT "Id", "Sensor_Mac", "DataHoraComFuso"
FROM public."Maquina_DatasSensor"
ORDER BY "DataHoraComFuso" DESC
LIMIT 50;
"""
consulta_sql_idsG = """
SELECT "Id", "Sensor_Mac", "DataHoraComFuso"
FROM public."Maquina_DatasSensorGlobal"
ORDER BY "DataHoraComFuso" DESC
LIMIT 50;
"""


try:
    # Executa a consulta para buscar todos os IDs
    cursor.execute(consulta_sql_ids)
    registros_espectros = cursor.fetchall()

    cursor.execute(consulta_sql_idsG)
    registros_globais = cursor.fetchall()
    
    if registros_espectros:
        print("Registros disponíveis:")
        for i, reg in enumerate(registros_espectros):
            print(f"{i + 1}: ID: {reg['Id']}, Sensor Mac: {reg['Sensor_Mac']}, Data e Hora: {reg['DataHoraComFuso']}")
        
        # Solicita ao usuário para escolher um registro
        escolha_id = int(input("Escolha o número correspondente ao registro desejado: ")) - 1
        id_maquina = registros_espectros[escolha_id]['Id']

    # Consulta SQL para obter "AxisSensorJson"
    consulta_sql = f"""
    SELECT "AxisSensorJson"
    FROM public."Maquina_DatasSensor"
    WHERE "Id"='{id_maquina}'::uuid;
    """

    # Consulta SQL para obter "SampleRate"
    consulta_sql2 = f"""
    SELECT "SamplingRate"
    FROM public."Maquina_DatasSensor"
    WHERE "Id"='{id_maquina}'::uuid;
    """

      # Consulta SQL para obter "AxisSensorDeVelocidadeJson"
    consulta_sql3 = f"""
    SELECT "AxisSensorDeVelocidadeJson"
    FROM public."Maquina_DatasSensor"
    WHERE "Id"='{id_maquina}'::uuid;
    """


    # Executa a consulta
    cursor.execute(consulta_sql)
    resultado = cursor.fetchone()
    
    cursor.execute(consulta_sql2)
    resultado2 = cursor.fetchone()

    cursor.execute(consulta_sql3)
    resultadoV = cursor.fetchone()


    if resultado:
        dataAcce = json.loads(resultado["AxisSensorJson"])

        # Debugging: Imprimir o comprimento das listas de coordenadas para verificar se os dados foram extraídos corretamente
        print(f"Tamanho da lista de coordenadas X: {len(dataAcce['Xs'])}")
        print(f"Tamanho da lista de coordenadas Y: {len(dataAcce['Ys'])}")
        print(f"Tamanho da lista de coordenadas Z: {len(dataAcce['Zs'])}")

        # Extrai as listas de coordenadas
        x = dataAcce["Xs"]
        y = dataAcce["Ys"]
        z = dataAcce["Zs"]

        sampling_rate = resultado2[0]
    
        # plotando forma de onda no tempo com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.arange(len(x)), y=x, mode='lines', name='X'))
        fig.add_trace(go.Scatter(x=np.arange(len(y)), y=y, mode='lines', name='Y'))
        fig.add_trace(go.Scatter(x=np.arange(len(z)), y=z, mode='lines', name='Z'))
        fig.update_layout(title='Forma de Onda no Tempo', xaxis_title='Amostra', yaxis_title='Valor')
        fig.show()

        # 1. Criando o sinal de senoide
        num_points = np.size(x)
        T = 1.0 / sampling_rate

        # 2. Processando o sinal com FFT
        x = x - np.mean(x)
        y = y - np.mean(y)
        z = z - np.mean(z)

        xf = fft(x)
        yf = fft(y)
        zf = fft(z)
        tf = np.linspace(0.0, 1.0/(2.0*T), num_points//2)

        # Plotando a FFT do sinal de aceleração com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tf, y=2.0/num_points * np.abs(xf[0:num_points//2]),mode='lines',name='X',hovertemplate='%{x:.2f} Hz<br>%{y:.2f} m/s²'))
        fig.add_trace(go.Scatter(x=tf, y=2.0/num_points * np.abs(yf[0:num_points//2]),mode='lines',name='Y',hovertemplate='%{x:.2f} Hz<br>%{y:.2f} m/s²'))
        fig.add_trace(go.Scatter(x=tf, y=2.0/num_points * np.abs(zf[0:num_points//2]),mode='lines',name='Z',hovertemplate='%{x:.2f} Hz<br>%{y:.2f} m/s²'))
        fig.update_layout(title="Espectro de Aceleração", xaxis_title="Frequência (Hz)", yaxis_title="Amplitude (m/s²)")
        fig.show()

       # 1. Obter a velocidade
        dataVel = json.loads(resultadoV["AxisSensorDeVelocidadeJson"])

        # Extrai as listas de coordenadas
        x_v = dataVel["Xs"]
        y_v = dataVel["Ys"]
        z_v = dataVel["Zs"]

        # plotando forma de onda no tempo velocidade com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.arange(len(x_v)), y=x_v, mode='lines', name='X'))
        fig.add_trace(go.Scatter(x=np.arange(len(y_v)), y=y_v, mode='lines', name='Y'))
        fig.add_trace(go.Scatter(x=np.arange(len(z_v)), y=z_v, mode='lines', name='Z'))
        fig.update_layout(title='Forma de Onda no Tempo Velocidade BD', xaxis_title='Amostra', yaxis_title='Valor')
        fig.show()

        #INTEGRAÇÃO DA ONDA EM ACELERÇÃO

        x_vel = np.cumsum(x) * T
        y_vel = np.cumsum(y) * T
        z_vel = np.cumsum(z) * T

        # Definir a frequência de corte do filtro passa-alta em Hz
        frequencia_corte = 5  # Hz

        # Calcular a frequência de corte relativa à taxa de amostragem
        frequencia_corte_normalizada = frequencia_corte / (0.5 * sampling_rate)

        # Criar o filtro passa-alta
        b, a = signal.butter(1, frequencia_corte_normalizada, btype='high', analog=False)

        # Aplicar o filtro passa-alta aos sinais de velocidade integrados
        x_vel_filtrada = signal.filtfilt(b, a, x_vel)
        y_vel_filtrada = signal.filtfilt(b, a, y_vel)
        z_vel_filtrada = signal.filtfilt(b, a, z_vel)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.arange(len(x_vel_filtrada)), y=x_vel_filtrada * 1000, mode='lines', name='X'))
        fig.add_trace(go.Scatter(x=np.arange(len(y_vel_filtrada)), y=y_vel_filtrada * 1000, mode='lines', name='Y'))
        fig.add_trace(go.Scatter(x=np.arange(len(z_vel_filtrada)), y=z_vel_filtrada * 1000, mode='lines', name='Z'))
        fig.update_layout(title='Forma de Onda no Tempo Velocidade Pos filtro', xaxis_title='Amostra', yaxis_title='Valor')
        fig.show()

        # Processamento do sinal de velocidade filtrada com FFT
        xf_vel_filtrada = fft(x_vel_filtrada)
        yf_vel_filtrada = fft(y_vel_filtrada)
        zf_vel_filtrada = fft(z_vel_filtrada)
        tf_vel_filtrada = np.linspace(0.0, 1.0/(2.0*T), num_points//2)

        # Plotando a FFT do sinal de velocidade filtrada com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tf_vel_filtrada, y=2.0/num_points * np.abs(xf_vel_filtrada[0:num_points//2])*1000, mode='lines', name='X', hovertemplate='%{x:.2f} Hz<br>%{y:.2f} mm/s'))
        fig.add_trace(go.Scatter(x=tf_vel_filtrada, y=2.0/num_points * np.abs(yf_vel_filtrada[0:num_points//2])*1000, mode='lines', name='Y', hovertemplate='%{x:.2f} Hz<br>%{y:.2f} mm/s'))
        fig.add_trace(go.Scatter(x=tf_vel_filtrada, y=2.0/num_points * np.abs(zf_vel_filtrada[0:num_points//2])*1000, mode='lines', name='Z', hovertemplate='%{x:.2f} Hz<br>%{y:.2f} mm/s'))
        fig.update_layout(title="Espectro de Velocidade", xaxis_title="Frequência (Hz)", yaxis_title="Amplitude (mm/s)")
        fig.show()
        
    else:
        print("Nenhum Espectro para o ID especificado.")


except psycopg2.Error as e:
    print("Erro ao executar a consulta:", e)
finally:
    # Fecha o cursor e a conexão
    cursor.close()
    conexao.close()
