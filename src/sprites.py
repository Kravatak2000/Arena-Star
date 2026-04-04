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
    
class Entity(pygame.sprite.Sprite):
    def __init__(self, game, x, y, layer, groups, color, max_hp):
        self.game = game
        self._layer = layer
        self.groups = groups
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * Tilesize
        self.y = y * Tilesize
        self.width = Tilesize
        self.height = Tilesize

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(color)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.x_change = 0
        self.y_change = 0

        self.max_hp = max_hp
        self.hp = max_hp
        
        self.health_bar = Health_Bar(self, self.width, 5, 10)

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

    def apply_movement(self):
        self.rect.x += self.x_change
        self.collision('x')
        self.rect.y += self.y_change
        self.collision('y')

        self.x_change = 0
        self.y_change = 0
    
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.kill()

class Player(Entity):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, Player_Layer, game.all_sprites, Light_blue, 100)
        self.last_hit = 0
        self.damage_cooldown = 500
        self.facing = 'up'

    def update(self):
        self.movement()
        self.enemy_collision()
        self.apply_movement()

        if self.hp <= 0:
            self.kill()
            self.game.playing = False

    def movement(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
            self.facing = 'left'
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
            self.facing = 'right'
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
            self.facing = 'up'
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
            self.facing = 'down'

        if direction.length() != 0:
            direction = direction.normalize()
        movement = direction * Player_Speed
        self.x_change = movement.x
        self.y_change = movement.y

    def enemy_collision(self):
        hits = pygame.sprite.spritecollide(self, self.game.enemies, False)
        if hits:
            now = pygame.time.get_ticks()
            if now - self.last_hit > self.damage_cooldown:
                self.take_damage(10)
                self.last_hit = now

class Health_Bar:
    def __init__(self, owner, width, height, offset_y):
        self.owner = owner
        self.width = width
        self.height = height
        self.offset_y = offset_y

    def draw(self, surface):
        ratio = self.owner.hp / self.owner.max_hp
        
        x = self.owner.rect.x
        y = self.owner.rect.y - self.offset_y

        pygame.draw.rect(surface, Red, (x, y, self.width, self.height))
        pygame.draw.rect(surface, Green, (x, y, self.width * ratio, self.height))


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

class Basic_enemy(Entity):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, Enemy_Layer, (game.all_sprites, game.enemies), Red, 50)
        self.last_hit = 0
        self.damage_cooldown = 200
        self.facing = 'up'
        self.speed = Basic_Enemey_Speed

    def damage_intake(self):
        hits = pygame.sprite.spritecollide(self, self.game.attacks, False)
        if hits:
            now = pygame.time.get_ticks()
            if now - self.last_hit > self.damage_cooldown:
                self.take_damage(10) 
                self.last_hit = now
    
    def ai(self):
        if self.rect.x < self.game.player.rect.x:
            self.x_change = self.speed
        elif self.rect.x > self.game.player.rect.x:
            self.x_change = -self.speed

        if self.rect.y < self.game.player.rect.y:
            self.y_change = self.speed
        elif self.rect.y > self.game.player.rect.y:
            self.y_change = -self.speed

    def update(self):
        self.ai()
        self.apply_movement()
        self.damage_intake()



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
    
class Portal(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = Wall_Layer
        self.groups = self.game.all_sprites, self.game.portals
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * Tilesize
        self.y = y * Tilesize
        
        self.image = pygame.Surface([Tilesize, Tilesize])
        self.image.fill((100, 0, 255)) # Purple

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y