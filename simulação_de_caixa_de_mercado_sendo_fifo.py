# -*- coding: utf-8 -*-
"""Simulação de caixa de mercado sendo FIFO

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19I2wbbIWuBIrFvXTULs0SndowFIWU9On

## Métricas Globais usando fila FIFO
"""

!pip install simpy
import simpy
import numpy as np
from scipy.stats import expon, norm
import matplotlib.pyplot as plt

# Listas de horários de chegada e saída dos caixas
chegadas, saidas, desistencias = [], [], []
in_queue, in_system, tempos_de_atendimento = [], [], []
horarios_nas_filas, tamanho_da_fila = [], []

# Constantes para o tempo médio de chegada de clientes, atendimento e falha
MEDIA_DE_CHEGADA_DE_CLIENTES = 3
MEDIA_DO_TEMPO_DE_ATENDIMENTO = 3.0
DESVIO_PADRAO_DO_TEMPO_DE_ATENDIMENTO = 0.5
TEMPO_MAXIMO_DE_ESPERA = 1.5
TEMPO_DE_REPARO = 10
PROBABILIDADE_BASE_DE_FALHA = 0.05
AUMENTO_PROBABILIDADE_POR_USO = 0.01

# Configuração do pico
HORARIO_INICIO_PICO = 30  # Tempo de início do pico
HORARIO_FIM_PICO = 50     # Tempo de fim do pico
MEDIA_CHEGADA_PICO = 1    # Tempo médio de chegada reduzido durante o pico

# Contadores
uso_dos_caixas = 0
falhas_no_sistema = 0

# Função para registrar o estado da fila
def salva_info_da_fila(env, caixa):
    horario_medicao = env.now
    tamanho_da_fila_agora = len(caixa.queue)
    horarios_nas_filas.append(horario_medicao)
    tamanho_da_fila.append(tamanho_da_fila_agora)
    return horario_medicao

# Distribuição do tempo de chegada dos clientes com ajuste para o pico
def distribuicao_chegada_de_clientes(env):
    if HORARIO_INICIO_PICO <= env.now <= HORARIO_FIM_PICO:
        return expon.rvs(scale=MEDIA_CHEGADA_PICO)
    return expon.rvs(scale=MEDIA_DE_CHEGADA_DE_CLIENTES)

# Calcula o tempo total no sistema
def calcula_tempo_no_sistema(env, horario_chegada):
    horario_saida = env.now
    saidas.append(horario_saida)
    tempo_total = horario_saida - horario_chegada
    in_system.append(tempo_total)

# Função que define a chegada de clientes
def chegada_dos_clientes(env):
    cliente_id = 0
    while True:
        # Tempo de chegada do próximo cliente
        tempo_do_proximo_cliente = distribuicao_chegada_de_clientes(env)
        yield env.timeout(tempo_do_proximo_cliente)

        # Cliente chegou
        tempo_de_chegada = env.now
        chegadas.append(tempo_de_chegada)
        cliente_id += 1
        print('%3d cliente chegou no mercado em %.2f' % (cliente_id, tempo_de_chegada))

        # Processo de atendimento
        env.process(atendimento(env, cliente_id, tempo_de_chegada))

# Tempo de atendimento do cliente no caixa
def tempo_de_atendimento_cliente():
    return norm.rvs(loc=MEDIA_DO_TEMPO_DE_ATENDIMENTO, scale=DESVIO_PADRAO_DO_TEMPO_DE_ATENDIMENTO)

# Processo de atendimento no caixa
def atendimento(env, cliente_id, horario_chegada):
    global uso_dos_caixas, falhas_no_sistema
    with caixas.request() as req:
        print('%3d cliente entrou na fila em %.2f' % (cliente_id, env.now))
        horario_entrada_da_fila = salva_info_da_fila(env, caixas)

        # Espera até que o caixa esteja disponível ou até o tempo máximo de espera
        resultado = yield req | env.timeout(TEMPO_MAXIMO_DE_ESPERA)

        # Verifica se o cliente conseguiu ser atendido ou desistiu
        if req in resultado:
            uso_dos_caixas += 1
            probabilidade_de_falha = PROBABILIDADE_BASE_DE_FALHA + (uso_dos_caixas * AUMENTO_PROBABILIDADE_POR_USO)
            if np.random.rand() < probabilidade_de_falha:
                falhas_no_sistema += 1
                print(f'Falha no sistema! Caixa em reparo no tempo {env.now:.2f}. Total de falhas: {falhas_no_sistema}')
                yield env.timeout(TEMPO_DE_REPARO)
                uso_dos_caixas = 0

            print('%3d cliente saiu da fila em %.2f' % (cliente_id, env.now))
            horario_saida_da_fila = salva_info_da_fila(env, caixas)

            tempo_na_fila = horario_saida_da_fila - horario_entrada_da_fila
            in_queue.append(tempo_na_fila)

            tempo_atendimento = tempo_de_atendimento_cliente()
            tempos_de_atendimento.append(tempo_atendimento)
            yield env.timeout(tempo_atendimento)
            print('%3d cliente foi atendido em %.2f' % (cliente_id, tempo_atendimento))

            calcula_tempo_no_sistema(env, horario_chegada)
        else:
            print('%3d cliente desistiu da fila em %.2f' % (cliente_id, env.now))
            desistencias.append(env.now)

# Exibe as métricas globais
def exibir_metricas_globais():
    total_clientes = len(chegadas)
    total_desistencias = len(desistencias)
    media_tempo_fila = np.mean(in_queue) if in_queue else 0
    media_tempo_sistema = np.mean(in_system) if in_system else 0
    taxa_desistencia = (total_desistencias / total_clientes) * 100 if total_clientes > 0 else 0

    print("\n--- Métricas Globais ---")
    print(f"Total de clientes atendidos: {total_clientes - total_desistencias}")
    print(f"Total de desistências: {total_desistencias}")
    print(f"Taxa de desistência: {taxa_desistencia:.2f}%")
    print(f"Tempo médio na fila: {media_tempo_fila:.2f}")
    print(f"Tempo médio no sistema: {media_tempo_sistema:.2f}")
    print(f"Total de falhas no sistema: {falhas_no_sistema}")

# Configurações da simulação
TEMPO_DE_SIMULACAO = 100
QUANTIDADE_DE_CAIXAS = 3

np.random.seed#(seed=1)

# Ambiente e recursos
env = simpy.Environment()
caixas = simpy.Resource(env, capacity=QUANTIDADE_DE_CAIXAS)

# Inicia a simulação
env.process(chegada_dos_clientes(env))
env.run(until=TEMPO_DE_SIMULACAO)

# Exibe as métricas globais
exibir_metricas_globais()

"""# Gráfico com as entradas e saídas de cada cliente

---


"""

# Gráfico de Entradas e Saídas
plt.figure(figsize=(10, 6))

# Plotando chegadas
plt.plot(chegadas, range(1, len(chegadas) + 1), marker='o', linestyle='-', color='blue', label='Chegadas')
# Plotando saídas
plt.plot(saidas, range(1, len(saidas) + 1), marker='o', linestyle='-', color='red', label='Saídas')

# Configurando o gráfico
plt.title('Fluxo de Entrada e Saída na Fila do Supermercado')
plt.xlabel('Tempo')
plt.ylabel('Número de Clientes')
plt.legend()
plt.grid(True)

# Exibindo o gráfico
plt.show()

"""#Tempo de trabalho do servidor ao longo do tempo"""

# Configuração do tamanho do gráfico
fig, (ax1) = plt.subplots(1)
fig.set_size_inches(20, 8)

# Gráfico 1: Distribuição Gaussiana (Normal) para o tempo de atendimento
media, desvio = 10, 5  # média e desvio padrão
x_gaussiana = np.random.normal(media, desvio, 1000)
ax1.text(media - 10, 80, r'$\mu=' + str(media) + ',\ \sigma=' + str(desvio) + '$')
ax1.hist(x_gaussiana, bins=30, edgecolor="white")
ax1.set_xlabel('Tempo de Atendimento (min)')
ax1.set_ylabel('Ocorrências')
ax1.set_title('Distribuição Gaussiana (Normal)')
ax1.grid()

"""# Tempo que um usuário fica fila


"""

import matplotlib.pyplot as plt

# Gráfico de Tempo de Espera na Fila
plt.figure(figsize=(10, 6))

# Plotando o tempo de espera de cada cliente na fila
plt.plot(range(1, len(in_queue) + 1), in_queue, marker='o', linestyle='-', color='purple', label='Tempo na Fila')

# Configurando o gráfico
plt.title('Tempo de Espera na Fila para Cada Cliente')
plt.xlabel('Cliente')
plt.ylabel('Tempo na Fila')
plt.legend()
plt.grid(True)

# Exibindo o gráfico
plt.show()