import pygame
from config import *
import math
import os

class Spritesheet:
    def __init__(self, file):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, file)

        self.sheet = pygame.image.load(full_path).convert()

    def get_sprite(self, x, y, width, height):
        sprite = pygame.Surface([width, height])
        sprite.blit(self.sheet, (0,0), (x, y, width, height))
        sprite.set_colorkey(Black)
        return sprite

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = Player_Layer
        self.groups = self.game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.hp = 100
        self.max_hp = 100

        self.last_hit = 0
        self.damage_cooldown = 500

        self.x = x * Tilesize
        self.y = y * Tilesize
        self.width = Tilesize
        self.height = Tilesize

        self.x_change = 0
        self.y_change = 0

        self.facing = 'up'

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(Light_blue)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        self.movement()
        self.enemy_collision()

        self.rect.x += self.x_change
        self.collision('x')
        self.rect.y += self.y_change
        self.collision('y')

        self.x_change = 0
        self.y_change = 0

        if self.hp <= 0:
            self.kill()
            self.game.playing = False
    
    def movement(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT]:
            direction.x -= 1
            self.facing = 'left'
        if keys[pygame.K_RIGHT]:
            direction.x += 1
            self.facing = 'right'
        if keys[pygame.K_UP]:
            direction.y -= 1
            self.facing = 'up'
        if keys[pygame.K_DOWN]:
            direction.y += 1
            self.facing = 'down'

        if direction.length() != 0:
            direction = direction.normalize()

        movement = direction * Player_Speed
        self.x_change = movement.x
        self.y_change = movement.y

    def collision(self, direction):
        if direction == "x":
            hits = pygame.sprite.spritecollide(self, self.game.blocks, False)
            if hits:
                if self.x_change > 0:
                    self.rect.x = hits[0].rect.left - self.rect.width
                if self.x_change < 0:
                    self.rect.x = hits[0].rect.right
                
        if direction == "y":
            hits = pygame.sprite.spritecollide(self, self.game.blocks, False)
            if hits:
                if self.y_change > 0:
                    self.rect.y = hits[0].rect.top - self.rect.height
                if self.y_change < 0:
                    self.rect.y = hits[0].rect.bottom
    
    def enemy_collision(self):
        hits = pygame.sprite.spritecollide(self, self.game.enemies, False)
        if hits:
            now = pygame.time.get_ticks()
            if now - self.last_hit > self.damage_cooldown:
                self.hp -= 10
                self.last_hit = now
        

class Player_Health():
    def __init__(self, x, y, width, height, max_hp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hp = max_hp
        self.max_hp = max_hp

    def draw(self, surface):
        ratio = self.hp / self.max_hp

        pygame.draw.rect(surface, Red, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, Green, (self.x, self.y, self.width * ratio, self.height))


class Wall(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        
        self.game = game
        self._layer = Wall_Layer
        self.groups = self.game.all_sprites, self.game.blocks
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * Tilesize
        self.y = y * Tilesize
        self.width = Tilesize
        self.height = Tilesize

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(Stone_gray)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

class Basic_enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        
        self.game = game
        self._layer = Enemy_Layer
        self.groups = self.game.all_sprites, self.game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * Tilesize
        self.y = y * Tilesize

        self.width = Tilesize
        self.height = Tilesize

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(Red)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
    
    def update(self):
        pass



class Basic_Attack(pygame.sprite.Sprite):
    def __init__(self, game, x, y):

        self.game = game
        self._layer = Player_Layer
        self.groups = self.game.all_sprites, self.game.attacks
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x
        self.y = y
        self.width = Tilesize
        self.height = Tilesize

        self.animation_loop = 0

        self.image = self.game.basic_attack_spritesheet.get_sprite(0, 0, self.width, self.height)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        self.animate()

    def animate(self):
        direction = self.game.player.facing

        right_animations = [self.game.basic_attack_spritesheet.get_sprite(0, 64, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(32, 64, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(64, 64, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(96, 64, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(128, 64, self.width, self.height)]

        down_animations = [self.game.basic_attack_spritesheet.get_sprite(0, 32, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(32, 32, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(64, 32, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(96, 32, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(128, 32, self.width, self.height)]

        left_animations = [self.game.basic_attack_spritesheet.get_sprite(0, 96, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(32, 96, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(64, 96, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(96, 96, self.width, self.height),
                           self.game.basic_attack_spritesheet.get_sprite(128, 96, self.width, self.height)]

        up_animations = [self.game.basic_attack_spritesheet.get_sprite(0, 0, self.width, self.height),
                         self.game.basic_attack_spritesheet.get_sprite(32, 0, self.width, self.height),
                         self.game.basic_attack_spritesheet.get_sprite(64, 0, self.width, self.height),
                         self.game.basic_attack_spritesheet.get_sprite(96, 0, self.width, self.height),
                         self.game.basic_attack_spritesheet.get_sprite(128, 0, self.width, self.height)]

        if direction == 'up':
            self.image = up_animations[math.floor(self.animation_loop)]
            self.animation_loop += 0.5
            if self.animation_loop >= 5:
                self.kill()

        if direction == 'down':
            self.image = down_animations[math.floor(self.animation_loop)]
            self.animation_loop += 0.5
            if self.animation_loop >= 5:
                self.kill()
        
        if direction == 'left':
            self.image = left_animations[math.floor(self.animation_loop)]
            self.animation_loop += 0.5
            if self.animation_loop >= 5:
                self.kill()

        if direction == 'right':
            self.image = right_animations[math.floor(self.animation_loop)]
            self.animation_loop += 0.5
            if self.animation_loop >= 5:
                self.kill()

class Button:
    def __init__(self, x, y, width, height, font_color, background, content, fontsize):
        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, 'Assets/AGoblinAppears-o2aV.ttf')
        self.font = pygame.font.Font(font_path, fontsize)
        self.content = content

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font_color = font_color
        self.background = background

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.background)
        self.rect = self.image.get_rect()

        self.rect.x = self.x
        self.rect.y = self.y

        self.text = self.font.render(self.content, True, self.font_color)
        self.text_rect = self.text.get_rect(center=(self.width/2, self.height/2))
        self.image.blit(self.text, self.text_rect)
    
    def is_pressed(self, position, pressed):
        if self.rect.collidepoint(position):
            if pressed[0]:
                return True
            return False
        return False