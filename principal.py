import numpy as np
import random
import json
import matplotlib.pyplot as plt
import pickle
from pyboy.pyboy import PyBoy
from pyboy.utils import WindowEvent
import time

class Ambiente:
    def __init__(self, nome_arquivo='mario.gb', modo_silencioso=True):
        tipo_janela = "headless" if modo_silencioso else "SDL2"
        self.pyboy = PyBoy(nome_arquivo, window=tipo_janela, debug=modo_silencioso)
        self.pyboy.set_emulation_speed(100)
        self.mario = self.pyboy.game_wrapper
        self.mario.start_game()

    def calcular_fitness(self):
        # TODO: Pode mudar o cálculo do fitness
        return self.mario.score + 2 * self.mario.level_progress + self.mario.time_left

    def fim_de_jogo(self):
        return self.mario.lives_left == 1 or self.mario.score < 0

    def reset(self):
        self.mario.reset_game()
        self.pyboy.tick()
        return self.get_estado()

    def passo(self, indice_acao, duracao):
        if self.fim_de_jogo():
            print("Fim de jogo detectado")
            return None, 0, 0, "Fim de Jogo"
        # TODO: Pode mudar as ações, ainda pode usar down e up
        acoes = {
            0: WindowEvent.PRESS_ARROW_LEFT,
            1: WindowEvent.PRESS_ARROW_RIGHT,
            2: WindowEvent.PRESS_BUTTON_A
        }
        acoes_liberacao = {
            0: WindowEvent.RELEASE_ARROW_LEFT,
            1: WindowEvent.RELEASE_ARROW_RIGHT,
            2: WindowEvent.RELEASE_BUTTON_A
        }

        acao = acoes.get(indice_acao, WindowEvent.PASS)
        self.pyboy.send_input(acao)
        for _ in range(duracao):
            self.pyboy.tick()

        acao_liberacao = acoes_liberacao.get(indice_acao, WindowEvent.PASS)
        self.pyboy.send_input(acao_liberacao)
        self.pyboy.tick()

        tempo_restante = self.mario.time_left
        progresso_nivel = self.mario.level_progress
        return self.get_estado(), self.calcular_fitness(), tempo_restante, progresso_nivel

    def get_estado(self):
        return np.asarray(self.mario.game_area())

    def fechar(self):
        self.pyboy.stop()

class Individuo:
    # TODO: Pode mudar a quantidade de ações e a duração
    def __init__(self):
        self.acoes = [(random.randint(1, 4), random.randint(10, 12)) for _ in range(5000)]
        self.fitness = 20

    # TODO: Fique à vontade para mudar a função de avaliação e adicionar/remover parâmetros
    def avaliar(self, ambiente):
        estado = ambiente.reset()
        fitness_total = 0
        tempo_maximo = 0
        movimentos_direita = 0
        jogo_terminou = False

        for acao, duracao in self.acoes:
            if jogo_terminou == "Fim de Jogo":
                break
            novo_estado, fitness, tempo_restante, jogo_terminou = ambiente.passo(acao, duracao)
            fitness_total += fitness
            tempo_maximo = max(tempo_maximo, tempo_restante)
            movimentos_direita += 1 if acao == 1 else 0
            estado = novo_estado

        pontos_tempo = 500 if tempo_maximo > 0 else 0
        self.fitness = fitness_total + pontos_tempo + movimentos_direita * 5
        return self.fitness

# A divisão é para dar numeros mais manejáveis
def avaliar_fitness(individuo, ambiente):
    fitness = individuo.avaliar(ambiente)
    fitness_normalizado = fitness / 10000
    return fitness_normalizado

def iniciar_individuos(populacao):
    return [Individuo() for _ in range(populacao)]

def selecao(populacao, qtd_pais , tamanho_torneio):
    pais_selecionados = []
    for _ in range(qtd_pais//2):
        candidatos_torneio = random.sample(populacao, tamanho_torneio)
        casal = torneio(candidatos_torneio)
        pais_selecionados.append(casal)
    return pais_selecionados
    
def torneio(candidatos):
    individuo_mais_apto = max(candidatos, key=candidatos.fitness)
    def filtro(e):
        return e != individuo_mais_apto
    candidatos = list(map(filtro, candidatos))
    individuo_segundo_mais_apto = max(candidatos, key=candidatos.fitness)
    casal = [individuo_mais_apto, individuo_segundo_mais_apto]
    return casal
def cruzamento(pai1, pai2):
        ponto_cruzamento = random.randint(1, len(pai1) - 1)
        filho = pai1[:ponto_cruzamento] + pai2[ponto_cruzamento:]
        return filho 
def mutacao(individuo):
    mutacao_quantidade = random.randint(1, 2)
    genes_mutaveis = random.sample(range(len(individuo)), mutacao_quantidade)
    for i in genes_mutaveis:
        valor_atual = individuo[i]
        valor_novo = valor_atual + random.randint(-1, 1)
        individuo[i] = valor_novo
    return individuo

def imprimir_acoes_individuo(individuo):
    nomes_acoes = ["esquerda", "direita", "A"]
    acoes = [f"{nomes_acoes[acao]} por {duracao} ticks" for acao, duracao in individuo.acoes]
    return acoes

def algoritmo_genetico(populacao, ambiente, geracoes=100):
    melhor_individuo = None
    melhor_fitness = -np.inf

    for geracao in range(geracoes):
        for individuo in populacao:
            individuo.fitness = avaliar_fitness(individuo, ambiente)
            print(f"Fitness: {individuo.fitness}")

        selecionadas = selecao(populacao, 2, 200)
        descendentes = []
        while len(descendentes) < len(populacao) - len(selecionadas):
            pai1, pai2 = random.sample(selecionadas, 2)
            filho1, filho2 = cruzamento(pai1, pai2)
            descendentes.extend([filho1, filho2])

        for filho in descendentes:
            mutacao(filho)

        populacao = selecionadas + descendentes

        fitness_atual = max(individuo.fitness for individuo in populacao)
        individuo_atual = max(populacao, key=lambda n: n.fitness)
        if fitness_atual > melhor_fitness:
            melhor_fitness = fitness_atual
            melhor_individuo = individuo_atual

        print(f"Geração {geracao}: Melhor Fitness {melhor_fitness}")
        print(f"Melhores Ações: {imprimir_acoes_individuo(melhor_individuo)}")

    return melhor_individuo

def rodar_melhor_modelo(ambiente, melhor_individuo):
    while True:
        estado = ambiente.reset()
        for acao in melhor_individuo.acoes:
            estado, fitness, tempo_restante, progresso_nivel = ambiente.passo(acao)

        print("Loop completado, reiniciando...")

ambiente = Ambiente(modo_silencioso=False)
populacao = iniciar_individuos(10)
algoritmo_genetico(populacao, ambiente)

# TODO: O que fazer com tamanho dos indivíduos? Podem aumentar ao longo do tempo?
