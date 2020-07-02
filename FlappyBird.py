# -*- coding: utf-8 -*-
"""
Created on Wed May 27 11:45:37 2020

@author: ACER
""" 
    
import pygame
import neat
import os
import random
import time
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800 #Dimensions of pygame window

#Next we load an array of images where each image will be scaled x2 and each image represents a different action = no flap, flap up,flap down
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bird1.png'))),pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bird2.png'))),pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bird3.png')))]
PIPE_IMG =pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','pipe.png'))) #image of pipe
BASE_IMG =pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','base.png'))) #image of ground/base
BG_IMG =pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bg.png'))) #image of background

STAT_FONT = pygame.font.SysFont("comicsans", 50)

GEN = 0 #to keep track of which generation

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25 #Rotation/tilt of bird whenever it wants to move up/down
    ROT_VEL = 20 #Rotation per frame
    ANIMATION_TIME = 5 #Time for which each bird animation will last
    
    def __init__(self,x,y):
        self.x = x
        self.y = y #Starting coordinates of bird
        self.tilt = 0 #How much the bird has tilted/rotated in order to draw it
        self.tick_count = 0 # checks how many frames ago was last action/movement
        self.vel = 0
        self.height = self.y
        self.image_count = 0 #Counts number of time a bird image has been shown
        self.img = self.IMGS[0] #Initial image
        
    def jump(self):
        self.vel = -10.5 #Here pygame window = 0,0 for top left. So up = -ve and down = +ve
        self.tick_count = 0
        self.height = self.y #Store current height before jumping in height
        
    def move(self):
        self.tick_count += 1 #We do a movement. Tick count essentially measures how many frames an action is carried for. It acts like time 
        
        d = self.vel * self.tick_count + 1.5*self.tick_count**2  #Displacement. For an upward jump, as tick count increases, d decreases emulating a decreasing disp as height increases
        
        if d>=16: #Threshold displacement for down
            d = 16
        if d<0: #If we are moving upward, jump a little more
            d-=2
            
        self.y = self.y + d
        
        if d<0 or self.y < self.height + 50: #Checks if we are moving up or moving down but still above previous height, we still want to tilt the bird upward
            if self.tilt<self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else: #Tilt downwards
            if self.tilt>-90:
                self.tilt -= self.ROT_VEL #i.e. Tilts downward more and more till it reaches -90 degrees
        
    
    def draw(self,win):
        self.image_count += 1 
        
        #The flapping motion of the bird
        if self.image_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.image_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.image_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.image_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.image_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.image_count = 0 #Reset count to repeat flapping motion
            
        if self.tilt<=-80:
            self.img = self.IMGS[1] #When almost -90 deg we dont want flapping motion
            self.image_count = self.ANIMATION_TIME*2 #so that next motion starts from correct bird image for smooth animation
        
        rotated_img = pygame.transform.rotate(self.img,self.tilt) #Rotates about top left corner
        new_rect = rotated_img.get_rect(center = self.img.get_rect(topleft = (self.x,self.y)).center) #Rotates image about its own center
        win.blit(rotated_img,new_rect.topleft) #Blit means draw
        
    def get_mask(self):
        return pygame.mask.from_surface(self.img) #Gets a mask i.e. a box surrounding the image with values denoting where in the box the pixels of the bird lie
    

class Pipe:
    GAP = 200
    VEL = 5 #Velocity with which the pipe moves towards bird.
    
    def __init__(self,x):
        self.x = x
        self.height = 0
        self.gap = 100
        self.top = 0
        self.bottom = 0
        
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG,False,True) #To make upside down pipe
        self.PIPE_BOTTOM = PIPE_IMG
        
        self.passed = False #If bird has passed the pipe or not
        self.set_height()
    
    def set_height(self):
        self.height = random.randrange(50,450) #Setting random height for pipe
        self.top = self.height - self.PIPE_TOP.get_height() #To locate where top of upside down needs to be located
        self.bottom = self.height + self.GAP #This will leave a gap of 200 between top and bottom pipes
        
    def move(self):
        self.x -= self.VEL
        
    def draw(self,win):
        win.blit(self.PIPE_TOP,(self.x,self.top))
        win.blit(self.PIPE_BOTTOM,(self.x,self.bottom))
    
    def collide(self,bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        
        top_offset = (self.x - bird.x, self.top - round(bird.y)) #Offset from bird to top pipe
        bottom_offset= (self.x - bird.x, self.bottom - round(bird.y)) #Offset from bird to top pipe
        
        b_point = bird_mask.overlap(bottom_mask,bottom_offset) #Checks if the masks overlap at distance = bottom_offset. Returns none if no overlap
        t_point = bird_mask.overlap(top_mask,top_offset) 
        
        if t_point or b_point: #i.e. colliding if not none
            return True
        
        return False

class Base:
    VEL = 5 #same as pipe
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    
    def __init__(self,y):
        self.y = y
        self.x1 = 0 #Starting of base image 1
        self.x2 = self.WIDTH #starting of base image 2
        #We use 2 base images moving to the left to give a continous effect
    
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        if self.x1 + self.WIDTH <0:
            self.x1 = self.x2 + self.WIDTH #If base1 goes out of screen, push it to the front of base 2
        
        if self.x2 + self.WIDTH <0:
            self.x2 = self.x1 + self.WIDTH #If base2 goes out of screen, push it to the front of base 1
            
    def draw(self,win):
        win.blit(self.IMG,(self.x1,self.y))
        win.blit(self.IMG,(self.x2,self.y))

def draw_window(win,birds,pipes,base,score,gen):
    win.blit(BG_IMG,(0,0))
    for pipe in pipes:
        pipe.draw(win)
        
    text = STAT_FONT.render("Score: "+str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()

def main(genomes, config): #Note that these parameters are needed in a fitness function
    global GEN
    GEN += 1
    nets = [] #The neural network for each bird with the params of a genome
    ge = [] #The basic arch and params of a particular species/genome
    birds = []
    for _,g in genomes: #Here _ is for id
        net = neat.nn.FeedForwardNetwork.create(g,config)
        nets.append(net)
        birds.append(Bird(230,350))
        g.fitness = 0
        ge.append(g)
    
    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
    clock = pygame.time.Clock() 
    
    score = 0 #Total score
    
    run = True
    while run:
        clock.tick(30) #i.e. this now ticks 30 times per frame. So essentially decreases speed of while loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
        
        pipe_ind = 0 #Index of pipe to look at for NN inputs. 0 - 1st pipe, 1- 2nd pipe
        if len(birds)>0:
            if len(pipes)>1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): #Check if bird has crossed pipe
                pipe_ind = 1
        else: #If no birds left in generation
            run = False
            break
        
        for x,bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1 #Give incentive to move forward
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))  #Get NN output with inputs as y of bird, and distances from the mouths of the top and bottom pipes from the bird
            if output[0]>0.5:
                bird.jump()
        #bird.move()
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x,bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -=1 #penalize for colliding
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                if not pipe.passed and pipe.x < bird.x: #check if bird has passed pipe
                    pipe.passed = True
                    add_pipe = True
                    
            if pipe.x + pipe.PIPE_TOP.get_width() < 0: #if pipe has gone out of screen
                rem.append(pipe) #Remove pipe
            
            pipe.move()
        
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5 #Since only birds that made it through the pipe will still have g in ge
            pipes.append(Pipe(600))
        for r in rem:
            pipes.remove(r)
        
        for x,bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y<0: #Bird has hit the ground or goes above screen
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        base.move()
        draw_window(win,birds,pipes,base,score,GEN)
        
    #quit()
        


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation,config_path)
    p = neat.Population(config) #generate a population based on params in config
    
    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # Evaluate using main function as fitness function for upto 50 generation.
    winner = p.run(main, 50)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__) #current file
    config_path = os.path.join(local_dir,'config_.txt')
    run(config_path)

    
    
    
        
    
        
        