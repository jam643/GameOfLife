# -*- coding: utf-8 -*-
"""
Created on Mon May 30 23:55:39 2016

@author: Jesse
"""
import pygame
import math
import random
import pickle
import eztext

white = (255,255,255)
black = (0,0,0)
gray = (200,200,200)
red = (255,100,100)
green = (100,255,100)
cyan = (0,255,255)
gold = (255,215,0)
magenta = (255,0,255)
screen_width = 1100
screen_height = 600

def draw_score (score,screen,fontStyle):
    text = fontStyle.render("SCORE: "+str(score), True, white)
    screen.blit(text, [10,10])

def find_angle(char_xy,mouse_xy):
    return -math.degrees(math.atan2(mouse_xy[1]-char_xy[1],mouse_xy[0]-char_xy[0]))
    
def message_to_screen(text,color,displace,fontStyle,screen,justify='center'):
    textSurf = fontStyle.render(text, True, color)
    textRect = textSurf.get_rect()
    textRect.centery = (screen_height/2)+displace[1]
    if justify == 'center':
        textRect.centerx = (screen_width/2)+displace[0]
    elif justify == 'left':
        textRect.left = (screen_width/2)+displace[0]
        
    screen.blit(textSurf, textRect)
    return textRect
    
def compare_scores(fileName,score):
    high_scores = []
    try:
        with open(fileName, 'rb') as f:
            high_scores = pickle.load(f)          
    except (EOFError, IOError):
        pass
    
    rank = -1
    if score > 0:
        scores = [x[0] for x in high_scores]
        for idx, x in enumerate(scores):
            if score >= x:
                rank = idx + 1
                break
            elif idx + 1 == len(scores) and len(scores) < 10:
                rank = len(scores) + 1
    if rank != -1:
        high_scores.insert(rank-1,[score,''])
        high_scores = high_scores[:10]
    return rank, high_scores
        
def save_scores(fileName,score,name,rank,high_scores):
    
    high_scores[rank-1][1] = name
    with open(fileName, 'wb') as f:
        pickle.dump(high_scores, f)

class SceneBase:
    def __init__(self):
        self.next = self
    
    def ProcessInput(self, events, pressed_keys):
        raise NotImplementedError

    def Update(self):
        raise NotImplementedError

    def Render(self, screen):
        raise NotImplementedError

    def SwitchToScene(self, next_scene):
        self.next = next_scene
    
    def Terminate(self):
        self.SwitchToScene(None)
        
def main():
    pygame.init()
    screen = pygame.display.set_mode((screen_width,screen_height))
    pygame.display.set_caption('Game Of Life')
    player_icon = pygame.image.load('craft.png')
    pygame.display.set_icon(player_icon)
    clock = pygame.time.Clock()
    
    active_scene = TitleScene()
    
    while active_scene != None:
        if pygame.event.get(pygame.QUIT):
            active_scene.Terminate()
            
        events = pygame.event.get()
        pressed_keys = pygame.key.get_pressed()
        
        active_scene.ProcessInput(events, pressed_keys)
        active_scene.Update()
        active_scene.Render(screen)
        pygame.display.update()
        
        clock.tick(active_scene.FPS)
        active_scene = active_scene.next
        
    
        
class GameScene(SceneBase):
    FPS = 60
    def __init__(self):
        SceneBase.__init__(self)
        
        pygame.mouse.set_visible(0)
        self.score_font = pygame.font.Font("pixelFont.ttf", 16)
        
        self.bullet_list = pygame.sprite.Group()
        self.star_list = pygame.sprite.Group()
        self.dust_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.player_list = pygame.sprite.Group()
        self.crosshair_list = pygame.sprite.Group()
        self.heart_list = pygame.sprite.Group()
        self.all_sprites_list = pygame.sprite.Group()
        
        self.player = Player()
        self.player_list.add(self.player)
        self.all_sprites_list.add(self.player) 
        
        self.heart = Heart()
        self.heart_list.add(self.heart)
        self.all_sprites_list.add(self.heart)
        
        crosshair = Crosshair()
        self.crosshair_list.add(crosshair)
        self.all_sprites_list.add(crosshair)
        
        self.counter = 0
        self.score = 0
        numStars = 500
    
        for i in range(numStars):
            star = Star(cyan)
            self.star_list.add(star)
#            self.all_sprites_list.add(star)
    
    def ProcessInput(self, events, pressed_keys):
        self.up, self.left, self.right, self.down = [pressed_keys[key] for key \
        in (pygame.K_w, pygame.K_a, pygame.K_d, pygame.K_s)]
        
    def Update(self):
        
        self.player.Fx = 0
        self.player.Fy = 0
        if self.up:
            self.player.Fy = -self.player.accel
        if self.left:
            self.player.Fx = -self.player.accel
        if self.right:
            self.player.Fx = self.player.accel
        if self.down:
            self.player.Fy = self.player.accel
            
        self.counter += 1
        if self.counter % (self.FPS/Bullet.rate) == 0:
            bullet=Bullet(self.player)
            self.all_sprites_list.add(bullet)
            self.bullet_list.add(bullet)
        
        if self.counter % (self.FPS/Dust.rate) == 0:
            dust = Dust(self.player,0.9,100,150,3,white,self.FPS)
            self.all_sprites_list.add(dust)
            self.dust_list.add(dust)
            
        if self.counter % (self.FPS/Ship.rate) == 0:
            ship = Ship(self.player)
            self.all_sprites_list.add(ship)
            self.enemy_list.add(ship)
            
        for bullet in self.bullet_list:
            if bullet.x < -bullet.size/2 or bullet.x > screen_width + bullet.size/2 \
            or bullet.y < -bullet.size/2 or bullet.y > screen_height + bullet.size/2:
                bullet.kill()
            enemy_kill_list = pygame.sprite.spritecollide(bullet,self.enemy_list,False)
            for enemy in enemy_kill_list:
                bullet.kill()
                self.score += enemy.points
                enemy.health -= 1
                if enemy.health == 0:
                    enemy.kill()
                    for i in range(100):
                        dust = Dust(enemy,0.9,100,1200,3,cyan,self.FPS)
                        self.all_sprites_list.add(dust)
                        self.dust_list.add(dust)     
                        
        for enemy in self.enemy_list:
            if pygame.sprite.collide_mask(enemy,self.player):
                
                for enemy in self.enemy_list:
                    enemy.kill()
                    for i in range(100):
                        dust = Dust(enemy,0.9,100,1200,3,cyan,self.FPS)
                        self.all_sprites_list.add(dust)
                        self.dust_list.add(dust)  
                
                self.player.health -= 1
                if self.player.health == 0:
                    rank, high_scores = compare_scores('HighScores.txt',self.score)
                    if rank == -1:
                        self.SwitchToScene(GameOverScene(self.score,rank,high_scores))
                    else:
                        self.SwitchToScene(HighScoreScene(self.score,rank,high_scores))
                            
        for dust in self.dust_list:
            if dust.image.get_alpha() <= 0:
                dust.kill()
        
        self.all_sprites_list.update(self.player,self.FPS)        
    
    def Render(self, screen):
        screen.fill(black)
        self.star_list.draw(screen)
        self.dust_list.draw(screen)
        self.enemy_list.draw(screen)
        self.bullet_list.draw(screen)
        self.player_list.draw(screen)
        self.crosshair_list.draw(screen)
        self.heart.draw(screen)
        draw_score(self.score,screen,self.score_font)
        
class TitleScene(SceneBase):
    FPS = 60
    def __init__(self):
        SceneBase.__init__(self)
        pygame.mouse.set_visible(1)
        self.play = pygame.image.load('play.png').convert()
        self.play.set_colorkey((1,1,1))
        self.play = pygame.transform.scale(self.play,(240,80))
        self.play_press = pygame.image.load('play_press.png').convert()
        self.play_press.set_colorkey((1,1,1))
        self.play_button = Button(self.play,self.play_press,(0,0))
        
        self.mouse = Mouse()
        
        self.title_font = pygame.font.Font("pixelFont.ttf", 60)
        self.star_list = pygame.sprite.Group() 
        numStars = 1000
        
        for i in range(numStars):
            star = Star(green)
            self.star_list.add(star)
    
    def ProcessInput(self, events, pressed_keys):
        self.play_button.event_handle(events)
        
    def Update(self):
        self.mouse.update(self.FPS)
        mouse_xy = pygame.mouse.get_pos()
        self.star_list.update(self.mouse,self.FPS)        
        
        pressed = self.play_button.update(mouse_xy)
        if pressed:
            self.SwitchToScene(GameScene())
    
    def Render(self, screen):
        screen.fill(black)
        self.star_list.draw(screen)
        self.play_button.draw(screen)
        message_to_screen("GAME OF LIFE",white,(0,-200),self.title_font,screen) 
        
class GameOverScene(SceneBase):
    FPS = 60
    def __init__(self,score,rank,high_scores):
        SceneBase.__init__(self)
        pygame.mouse.set_visible(1)
        self.score = score
        self.rank = rank
        self.high_scores = high_scores
       
        self.retry = pygame.image.load('retry.png').convert()
        self.retry.set_colorkey((1,1,1))
        self.retry = pygame.transform.scale(self.retry,(240,80))
        self.retry_hover = pygame.image.load('retry_hover.png').convert()
        self.retry_hover.set_colorkey((1,1,1))
        self.retry_button = Button(self.retry,self.retry_hover,(-200,240))
        self.menu = pygame.image.load('menu.png').convert()
        self.menu.set_colorkey((1,1,1))
        self.menu = pygame.transform.scale(self.menu,(240,80))
        self.menu_hover = pygame.image.load('menu_hover.png').convert()
        self.menu_hover.set_colorkey((1,1,1))
        self.menu_button = Button(self.menu,self.menu_hover,(200,240))
        
        self.mouse = Mouse()
        
        self.large_font = pygame.font.Font("pixelFont.ttf", 50)
        self.med_font = pygame.font.Font("pixelFont.ttf", 24)
        self.small_font = pygame.font.Font("pixelFont.ttf", 16)
        self.win_font = pygame.font.Font("pixelFont.ttf", 20)
        
        self.star_list = pygame.sprite.Group() 
        numStars = 1000
        
        for i in range(numStars):
            star = Star(magenta)
            self.star_list.add(star)
    
    def ProcessInput(self, events, pressed_keys):
        self.retry_button.event_handle(events)
        self.menu_button.event_handle(events)
        
    def Update(self):
        self.mouse.update(self.FPS)
        mouse_xy = pygame.mouse.get_pos()
        self.star_list.update(self.mouse,self.FPS)
        
        retry_pressed = self.retry_button.update(mouse_xy)
        menu_pressed = self.menu_button.update(mouse_xy)
        if retry_pressed:
            self.SwitchToScene(GameScene())
        elif menu_pressed:
            self.SwitchToScene(TitleScene())
            
    
    def Render(self, screen):
        screen.fill(black)
        self.star_list.draw(screen)
        self.retry_button.draw(screen)
        self.menu_button.draw(screen)
        message_to_screen("GAME OVER",white,(0,-260),self.large_font,screen)
        message_to_screen("RANK",white,(-200,-180),self.med_font,screen)
        message_to_screen("NAME",white,(0,-180),self.med_font,screen)
        message_to_screen("SCORE",white,(200,-180),self.med_font,screen)
        for idx, high_score in enumerate(self.high_scores):
            rank = idx + 1
            if rank == self.rank:
                color = green
                font = self.win_font
            else:
                color = white
                font = self.small_font
            message_to_screen(str(rank),color,(-200,-140+35*idx),font,screen)
            message_to_screen(str(high_score[1]),color,(0,-140+35*idx),font,screen)
            message_to_screen(str(high_score[0]),color,(200,-140+35*idx),font,screen)
            
class HighScoreScene(SceneBase):
    FPS = 60
    def __init__(self,score,rank,high_scores):
        SceneBase.__init__(self)
        
        pygame.mouse.set_visible(1)
        self.score = score
        self.rank = rank
        self.high_scores = high_scores
       
        self.enter = pygame.image.load('enter.png').convert()
        self.enter.set_colorkey((1,1,1))
        self.enter = pygame.transform.scale(self.enter,(240,80))
        self.enter_hover = pygame.image.load('enter_hover.png').convert()
        self.enter_hover.set_colorkey((1,1,1))
        self.enter_button = Button(self.enter,self.enter_hover,(0,200))
        
        self.mouse = Mouse()
        
        self.large_font = pygame.font.Font("pixelFont.ttf", 40)
        self.med_font = pygame.font.Font("pixelFont.ttf", 30)
        self.small_font = pygame.font.Font("pixelFont.ttf", 16)
        self.win_font = pygame.font.Font("pixelFont.ttf", 20)
        
        self.txtbx = eztext.Input(maxlength=12, 
                                  color=white, 
                                  font = self.med_font,
                                  x = screen_width/2,
                                  y = screen_height/2-50)

        self.star_list = pygame.sprite.Group() 
        numStars = 1000
        
        for i in range(numStars):
            star = Star(gold)
            self.star_list.add(star)
    
    def ProcessInput(self, events, pressed_keys):
        self.enter_button.event_handle(events)
        self.txtbx.update(events)
        
    def Update(self):
        self.mouse.update(self.FPS)
        mouse_xy = pygame.mouse.get_pos()
        self.star_list.update(self.mouse,self.FPS)
        
        enter_pressed = self.enter_button.update(mouse_xy)
        if enter_pressed:
            name = self.txtbx.get_value()
            save_scores('HighScores.txt',self.score,name,self.rank,self.high_scores)
            self.SwitchToScene(GameOverScene(self.score,self.rank,self.high_scores))            
    
    def Render(self, screen):
        screen.fill(black)
        self.star_list.draw(screen)
        self.enter_button.draw(screen)
        message_to_screen("NEW HIGH SCORE!",gold,(0,-250),self.large_font,screen)
        message_to_screen("RANK:",white,(-350,-130),self.med_font,screen)
        message_to_screen("ENTER NAME:",white,(0,-130),self.med_font,screen)
        message_to_screen("SCORE:",white,(350,-130),self.med_font,screen)
        message_to_screen(str(self.rank),white,(-350,-50),self.med_font,screen)
        message_to_screen(str(self.score),white,(350,-50),self.med_font,screen)
        self.txtbx.draw(screen)

class Button(object):
    def __init__(self,image_orig,image_press,loc):
        self.loc = loc        
        self.image_orig = image_orig      
        self.rect_orig = self.image_orig.get_rect()
        self.rect_orig.center = (screen_width/2) + self.loc[0], \
        (screen_height/2) + self.loc[1]
        
        self.image_press = image_press
        self.rect_press = self.image_press.get_rect()
        self.rect_press.center = (screen_width/2) + self.loc[0], \
        (screen_height/2) + self.loc[1]
        
        self.pressed = False
        self.rect = self.rect_orig
        
    def update(self,mouse_xy):
            
        if mouse_xy[0] > self.rect[0] and \
        mouse_xy[0] < self.rect[0] + self.rect.width and \
        mouse_xy[1] > self.rect[1] and \
        mouse_xy[1] < self.rect[1] + self.rect.height:
            self.image = self.image_press
            self.rect = self.rect_press    
            if self.clicked:
                self.pressed = True
        else:
            self.image = self.image_orig  
            self.rect = self.rect_orig   
        
        return self.pressed
        
    def draw(self,screen):
       
        screen.blit(self.image,self.rect)
        
    def event_handle(self,events):
        self.clicked = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                self.clicked = True
                
class Mouse(object):
    def __init__(self):
        self.vx = 0
        self.vy = 0
        self.x = 0
        self.y = 0
        
    def update(self,FPS):
        mouse_vel = pygame.mouse.get_rel()
        self.vx = mouse_vel[0] * FPS/4
        self.vy = mouse_vel[1] * FPS/4
        
        mouse_xy = pygame.mouse.get_pos()
        self.x = mouse_xy[0]
        self.y = mouse_xy [1]
        
class Heart(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('heart.png').convert()
        self.image.set_colorkey((1,1,1))
        self.rect = self.image.get_rect()
        
    def update(self,player,FPS):
        self.health = player.health
        
    def draw(self,screen):
        self.rect.x = screen_width
        self.rect.y = 10
        for i in range(self.health):
            self.rect.x -= self.rect.width + 10
            screen.blit(self.image,self.rect)

class Star(pygame.sprite.Sprite):
    def __init__(self,color):
        pygame.sprite.Sprite.__init__(self)
        maxSize = 3
        rand = maxSize*random.random()
        self.speed = 0.1 * rand
        self.size = int(math.ceil(rand))

        self.image = pygame.Surface([self.size,self.size])
        self.image.fill(color)
        self.image.set_alpha(255)
        self.rect = self.image.get_rect()
        
        self.ax = 0.0
        self.ay = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vy_rel = 0
        self.vx_rel = 0
        self.x = screen_width*random.random()
        self.y = screen_height*random.random()
        self.x_orig = self.x
        self.y_orig = self.y
        self.rect.x = self.x-self.rect.width/2
        self.rect.y = self.y-self.rect.height/2
        self.phase = 2*math.pi*random.random()
        self.amp = 10 + 40*random.random()
        self.freq = 10+20*random.random()
        self.image.set_alpha(80)
        
    def update(self,player,FPS):
        time = pygame.time.get_ticks()/1000.0
        dist = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
        self.image.set_alpha(max(60,min(255,(260**2-dist**2)*255/250**2) - self.amp*(1 - math.sin(self.freq*time-self.phase))))
        dist = max((dist,1))
        self.ax = 30000*(self.x - player.x)/dist**2 + 10*(self.x_orig - self.x) - 5*self.vx
        self.ay = 30000*(self.y - player.y)/dist**2 + 10*(self.y_orig - self.y) - 5*self.vy
        self.vx += self.ax/FPS
        self.vy += self.ay/FPS
        self.x += self.vx/FPS
        self.y += self.vy/FPS
        
        self.rect.x = self.x-self.rect.width/2
        self.rect.y = self.y-self.rect.height/2  
        

class Player(pygame.sprite.Sprite):
    accel = 3000
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.health = 2
        self.maxV = 200
        self.decel = 400
        self.rest_coeff = 0.3  
        self.size = 30
        
        self.image = pygame.image.load('boat_anim3.png').convert()
        self.image.set_colorkey((1,1,1))
        self.image_orig = self.image
        self.rect = self.image.get_rect()
        
        self.theta = 0
        self.x = screen_width/2
        self.y = screen_height/2
        self.ax = 0.0
        self.ay = 0.0
        self.vx = 0.0
        self.vy = 0.0  
        self.Fx = 0.0
        self.Fy = 0.0
        
        self.coll_x = False
        self.coll_y = False
        self.coll_time = 0
        self.coll_pause = 0.2
        
    def update(self,player,FPS):
        
        self.collision_wall()
        
        mouse_xy = pygame.mouse.get_pos()
        self.theta = find_angle((self.x,self.y),mouse_xy) + 45
        if self.theta >-22.5 and self.theta < 22.5:            
            self.image_temp =  self.image_orig.subsurface((0,0,self.size,self.size))
        elif self.theta > 22.5 and self.theta < 67.5:
            self.image_temp =  self.image_orig.subsurface((self.size,0,self.size,self.size))
        elif self.theta > 67.5 and self.theta < 112.5:
            self.image_temp =  self.image_orig.subsurface((2*self.size,0,self.size,self.size))
        elif self.theta > 112.5 and self.theta < 157.5:
            self.image_temp =  self.image_orig.subsurface((3*self.size,0,self.size,self.size))
        elif self.theta > 157.5 and self.theta < 202.5:
            self.image_temp =  self.image_orig.subsurface((4*self.size,0,self.size,self.size))
        elif self.theta < -112.5 or self.theta > 202.5:
            self.image_temp =  self.image_orig.subsurface((5*self.size,0,self.size,self.size))
        elif self.theta > -112.5 and self.theta < -67.5:
            self.image_temp =  self.image_orig.subsurface((6*self.size,0,self.size,self.size))
        else:
            self.image_temp =  self.image_orig.subsurface((7*self.size,0,self.size,self.size))
            
        self.image = pygame.transform.rotate(self.image_temp,self.theta)
        self.rect = self.image.get_rect()
        
        if self.Fx == 0:            
            self.ax = -self.vx*self.decel/self.maxV
        else:
            self.ax = self.Fx - self.vx*self.accel/self.maxV
        if self.Fy == 0:            
            self.ay = -self.vy*self.decel/self.maxV
        else:
            self.ay = self.Fy - self.vy*self.accel/self.maxV
            
        self.vx += self.ax/FPS
        self.vy += self.ay/FPS
        self.x += self.vx/FPS
        self.y += self.vy/FPS
        
        self.rect.x = self.x-self.rect.width/2
        self.rect.y = self.y-self.rect.height/2     
        
    def collision_wall(self):
        time = pygame.time.get_ticks()/1000.0
        if (self.rect.x < 0 or self.rect.x > screen_width - self.size) \
        and not self.coll_x:
            self.vx = -self.vx * self.rest_coeff
            self.Fx = 0
            self.coll_x = True
            self.coll_time = pygame.time.get_ticks()/1000.0
        elif not (self.rect.x < 0 or self.rect.x > screen_width - self.rect.width) \
        and time > self.coll_time + self.coll_pause:
            self.coll_x = False
        elif self.coll_x:
            self.Fx = 0
        if (self.rect.y < 0 or self.rect.y > screen_height - self.rect.height) \
        and not self.coll_y:
            self.vy = -self.vy * self.rest_coeff
            self.Fy = 0
            self.coll_y = True
            self.coll_time = pygame.time.get_ticks()/1000.0
        elif not (self.rect.y < 0 or self.rect.y > screen_height - self.rect.height) \
        and time > self.coll_time + self.coll_pause:
            self.coll_y = False
        elif self.coll_y:
            self.Fy = 0

class Crosshair(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('crosshair.png').convert()
        self.image.set_colorkey((1,1,1))
        self.rect = self.image.get_rect()
        
    def update(self,player,FPS):
        
        mouse_xy = pygame.mouse.get_pos()
        self.rect.x = mouse_xy[0]-self.rect.width/2
        self.rect.y = mouse_xy[1]-self.rect.height/2

class Dust(pygame.sprite.Sprite):
    rate = 30
    def __init__(self,player,lifeSpan,minV,rangeV,decel,color,FPS):
        pygame.sprite.Sprite.__init__(self)
        
        self.decel = decel
        self.vel = minV+rangeV*random.random()
        if self.vel > minV+rangeV*2/3:
            self.size = 1
        elif self.vel > minV+rangeV/3:
            self.size = 3
        else:
            self.size = 4
            
        self.image = pygame.Surface([self.size,self.size])
        self.image.fill(color)
        self.image.set_alpha(255)
        self.alpha_dec = self.image.get_alpha()/(lifeSpan*FPS)
        self.theta = random.random()*2*math.pi 
        self.rect = self.image.get_rect()
        
        self.x = player.x
        self.y = player.y
        self.rect.x = self.x-self.rect.width/2
        self.rect.y = self.y-self.rect.height/2
        self.accel = 0
        
    def update(self,player,FPS):
        self.accel = -self.decel*self.vel
        self.vel += self.accel/FPS
        self.x += math.cos(self.theta)*self.vel/FPS
        self.y -= math.sin(self.theta)*self.vel/FPS
        self.rect.x = self.x-self.rect.width/2
        self.rect.y = self.y-self.rect.height/2
        self.image.set_alpha(self.image.get_alpha() - self.alpha_dec)        
        
class Ship(pygame.sprite.Sprite):
    rate = 2
    size = 30
    radius = 300
    birth_time = 0.5
    points = 100
    def __init__(self,player):
        pygame.sprite.Sprite.__init__(self)

        self.vel = 100     
        self.health = 1
        
        self.image = pygame.image.load('ship.png').convert()
        self.image.set_colorkey((1,1,1))
        self.image_orig= self.image
        self.rect_orig = self.image.get_rect()
        self.width = self.rect_orig.width
        self.height = self.rect_orig.height
        self.rect = self.image.get_rect()
        self.theta = 0
        done = False
        while not done:
            self.x = random.random()*screen_width
            self.y = random.random()*screen_height
            if math.sqrt((player.x-self.x)**2+(player.y-self.y)**2) >= self.radius:
                done = True
        self.startTime = pygame.time.get_ticks()/1000.0

        self.mask = pygame.mask.from_surface(self.image)
        
    def update(self,player,FPS):
        time = pygame.time.get_ticks()/1000.0 - self.startTime
        
        if time < self.birth_time:
            self.image = pygame.transform.scale(self.image_orig,(int(self.width*time/self.birth_time),int(self.height*time/self.birth_time)))
            
        else:
            self.image = pygame.transform.scale(self.image_orig,(int(self.width+\
            2*math.sin(10*time)),int(self.height+2*math.sin(10*time+math.pi))))
            
        self.rect = self.image.get_rect()
        self.theta = find_angle((self.x,self.y),(player.x,player.y))
        self.vx = self.vel*math.cos(math.radians(self.theta))
        self.vy = -self.vel*math.sin(math.radians(self.theta))
        self.x += self.vx/FPS
        self.y += self.vy/FPS
        
        self.rect.x = self.x-self.rect.width/2
        self.rect.y = self.y-self.rect.height/2 
    
        
class Bullet(pygame.sprite.Sprite):
    rate = 10
    def __init__(self,player):
        pygame.sprite.Sprite.__init__(self)

        self.vel = 900
        self.size = random.random()*3+5
        self.image = pygame.Surface([self.size,self.size])
        self.image.fill(white)
        
        rand_angle = random.random()*4-2
        mouse_xy = pygame.mouse.get_pos()
        self.theta = find_angle((player.x,player.y),mouse_xy)+rand_angle

        self.rect = self.image.get_rect()  
        self.x = player.x
        self.y = player.y
        self.rect.x = self.x-self.size/2
        self.rect.y = self.y-self.size/2
        
    def update(self,player,FPS):
        self.x += math.cos(math.radians(self.theta))*self.vel/FPS
        self.y -= math.sin(math.radians(self.theta))*self.vel/FPS
        self.rect.x = self.x-self.size/2
        self.rect.y = self.y-self.size/2


if __name__ == "__main__":
    main()
