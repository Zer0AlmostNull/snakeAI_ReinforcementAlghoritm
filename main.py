from game import SnakeBasic, SnakeWindowed, Direction

import numpy as np
from collections import deque
from console_colors import colors

from model import Linear_QNet, QTrainer
from helper import plot

import random
import torch
import pygame

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

SNAKE_DIMENSIONS = (20, 20)

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = .9 # discount rate
        self.memory = deque(maxlen = MAX_MEMORY) # popleft
        
        self.model = Linear_QNet((24, 256, 128, 4))
        self.trainer = QTrainer(self.model, lr = LR, gamma = self.gamma)        
        
    def get_state(self, game: SnakeBasic):        
        return np.array(game._get_basic_input_bin(), dtype = np.int)
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))  # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory
            
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)
    
    def get_action(self, state, game: SnakeBasic):
        # random moves tradeoff exploratation /exploitation
        self.epsilon = 80 - self.n_games
        move = 0
        
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 3)
                     
            # get nice moves from game
            #move = Direction.directions.index(random.choice(game._get_nice_moves()))      
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
        
        return move
            
def train():
    #
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    
    # setup pygame
    display = pygame.display.set_mode((720, 720))
    pygame.display.set_caption('Snake')
    clock = pygame.time.Clock()
    
    # some weird stuff
    agent = Agent()
    game = SnakeWindowed(SNAKE_DIMENSIONS, 30)
    
    TICK_INTERVAL = 0
    timer = 500
    
    
    while 1:
        # handling events
        for event in pygame.event.get():
            # quiting from an app
            if event.type == pygame.QUIT:
                exit(0)        
        
        
        if timer > TICK_INTERVAL:
            timer -= TICK_INTERVAL
            
            # get old state
            state_old = agent.get_state(game)
            
            # get_move
            move = agent.get_action(state_old, game)
            
            move_vector = [0, 0, 0, 0]
            move_vector[move] = 1
            
            # perform a move and get new state
            reward, done, score = game.tick(move)                        
            # draw game
            display.fill((10, 10, 10))
            game.draw(display, (0, 0))
            
            state_new = agent.get_state(game)
            
            # train short memory
            agent.train_short_memory(state_old, move_vector, reward, state_new, done)
            
            agent.remember(state_old, move_vector, reward, state_new, done)
            
            if done:
                # train long memory(replay), plot result
                game.reset()
                agent.n_games += 1
                agent.train_long_memory()
                
                if score > record:
                    record = score
                    agent.model.save()
            
                print(f'{colors.GREEN}»»»»{colors.ENDC}Game no.{agent.n_games}{colors.GREEN}««««{colors.ENDC}')
                print(f'\t->score = {score}')
                print(f'\t->record = {record}')
                
                plot_scores.append(score)
                total_score += score
                mean_score = total_score / agent.n_games
                plot_mean_scores.append(mean_score)
                plot(plot_scores, plot_mean_scores)
            
        # update the screen
        pygame.display.update()
        
        # control fps and get the interval
        timer += clock.tick(120)
    
if __name__ == '__main__':
    train()