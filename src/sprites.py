import pygame
from config import *
import math
import os
import random

class Spritesheet:
    """Handles loading and cutting individual sprites out of a larger texture sheet."""
    def __init__(self, file):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, file)

        self.sheet = pygame.image.load(full_path).convert()

    def get_sprite(self, x, y, width, height):
        """Extracts and returns a single sprite from the main spritesheet.

        :param x: The x-coordinate of the sprite on the sheet.
        :param y: The y-coordinate of the sprite on the sheet.
        :param width: The width of the sprite in pixels.
        :param height: The height of the sprite in pixels.
        :return: A new Pygame Surface containing the isolated sprite.
        """
        sprite = pygame.Surface([width, height])
        sprite.blit(self.sheet, (0,0), (x, y, width, height))
        sprite.set_colorkey(Black)
        return sprite
    
class Entity(pygame.sprite.Sprite):
    """The base class for all moving and destructible characters in the game."""
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
        """Handles horizontal and vertical collision detection against solid wall blocks.

        :param direction: The axis of movement to check ('x' or 'y').
        """
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
        """Applies velocity updates to the entity position and triggers collision checks."""
        self.rect.x += self.x_change
        self.collision('x')
        self.rect.y += self.y_change
        self.collision('y')

        self.x_change = 0
        self.y_change = 0
    
    def take_damage(self, amount):
        """Reduces the entity health and kills it if health drops to or below zero.

        :param amount: The total damage points to subtract from health.
        """
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.kill()

class Player(Entity):
    """Represents the player character, controlling movement inputs and animations."""
    def __init__(self, game, x, y):
        super().__init__(game, x, y, Player_Layer, game.all_sprites, Light_blue, 100)
        self.last_hit = 0
        self.damage_cooldown = 500
        self.facing = 'up'

        self.is_dashing = False
        self.dash_speed_multiplier = 3.0
        self.dash_duration = 150
        self.dash_cooldown = 2000
        self.last_dash = -self.dash_cooldown 
        self.dash_direction = pygame.Vector2(0, 0)

    def update(self):
        """Updates the state of the player including movement, collisions, and health."""
        self.movement()
        self.enemy_collision()
        self.apply_movement()
        self.check_dash_status()

        if self.hp <= 0:
            self.kill()
            self.game.playing = False

    def movement(self):
        """Processes keyboard inputs to calculate player directional movement vectors."""
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        if self.is_dashing:
            movement = self.dash_direction * (Player_Speed * self.dash_speed_multiplier)
            self.x_change = movement.x
            self.y_change = movement.y
            return
        
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

        if keys[pygame.K_LSHIFT] and (now - self.last_dash > self.dash_cooldown):
            self.is_dashing = True
            self.last_dash = now

            if self.game.sounds.get('player_dash'):
                self.game.sounds['player_dash'].play()
            
            if direction.length() != 0:
                self.dash_direction = direction
            else:
                if self.facing == 'left': self.dash_direction = pygame.Vector2(-1, 0)
                elif self.facing == 'right': self.dash_direction = pygame.Vector2(1, 0)
                elif self.facing == 'up': self.dash_direction = pygame.Vector2(0, -1)
                elif self.facing == 'down': self.dash_direction = pygame.Vector2(0, 1)

            movement = self.dash_direction * (Player_Speed * self.dash_speed_multiplier)
        else:
            movement = direction * Player_Speed

        self.x_change = movement.x
        self.y_change = movement.y

    def enemy_collision(self):
        """Detects if the player is touching an enemy and applies damage based on cooldowns."""
        hits = pygame.sprite.spritecollide(self, self.game.enemies, False)
        if hits:
            now = pygame.time.get_ticks()
            if now - self.last_hit > self.damage_cooldown:
                if self.game.sounds.get('player_hurt'):
                    self.game.sounds['player_hurt'].play()
                self.take_damage(10)
                self.last_hit = now
    
    def check_dash_status(self):
        """Tracks the active time of a dash and turns it off when elapsed."""
        if self.is_dashing:
            now = pygame.time.get_ticks()
            if now - self.last_dash > self.dash_duration:
                self.is_dashing = False

class Health_Bar:
    """A visual interface element tracking and rendering an entity's health percentage."""
    def __init__(self, owner, width, height, offset_y):
        self.owner = owner
        self.width = width
        self.height = height
        self.offset_y = offset_y

    def draw(self, surface):
        """Renders the red and green health bars onto the given game display surface.

        :param surface: The Pygame display surface where the health bar should be drawn.
        """
        ratio = self.owner.hp / self.owner.max_hp
        
        x = self.owner.rect.x
        y = self.owner.rect.y - self.offset_y

        pygame.draw.rect(surface, Red, (x, y, self.width, self.height))
        pygame.draw.rect(surface, Green, (x, y, self.width * ratio, self.height))


class Wall(pygame.sprite.Sprite):
    """A static environmental obstacle block that prevents entity movement."""
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
    """An enemy unit that tracks the player's position and targets them."""
    def __init__(self, game, x, y):
        super().__init__(game, x, y, Enemy_Layer, (game.all_sprites, game.enemies), Red, 50)
        self.last_hit = 0
        self.damage_cooldown = 200
        self.facing = 'up'
        self.speed = Basic_Enemey_Speed
        self.detection_radius = 300

    def damage_intake(self):
        """Checks if the enemy is being hit by any player attacks and applies damage."""
        hits = pygame.sprite.spritecollide(self, self.game.attacks, False)
        if hits:
            now = pygame.time.get_ticks()
            if now - self.last_hit > self.damage_cooldown:
                self.take_damage(10) 
                self.last_hit = now
    
    def ai(self):
        """Calculates pathing vectors to directly chase the current player location."""
        enemy_to_player = pygame.Vector2(
            self.game.player.rect.centerx - self.rect.centerx,
            self.game.player.rect.centery - self.rect.centery
        )

        distance = enemy_to_player.length()

        if distance <= self.detection_radius:
            if self.rect.x < self.game.player.rect.x:
                self.x_change = self.speed
            elif self.rect.x > self.game.player.rect.x:
                self.x_change = -self.speed

            if self.rect.y < self.game.player.rect.y:
                self.y_change = self.speed
            elif self.rect.y > self.game.player.rect.y:
                self.y_change = -self.speed
        else:
            self.x_change = 0
            self.y_change = 0

    def update(self):
        """Updates enemy state by executing AI logic, movement calculation, and damage checks."""
        self.ai()
        self.apply_movement()
        self.damage_intake()

class Ranged_enemy(Entity):
    """An enemy unit that maintains distance from the player and shoots projectiles."""

    def __init__(self, game, x: int, y: int):
        super().__init__(game, x, y, Enemy_Layer, (game.all_sprites, game.enemies), White, 30)
        self.last_hit = 0
        self.damage_cooldown = 300
        self.speed = Basic_Enemey_Speed

        self.shoot_cooldown = 2000
        self.last_shot = 0
        self.attack_range = 300

        self.detection_radius = 600

    def damage_intake(self):
        """Checks if the enemy is being hit by any player attacks and applies damage."""
        hits = pygame.sprite.spritecollide(self, self.game.attacks, False)
        if hits:
            now = pygame.time.get_ticks()
            if now - self.last_hit > self.damage_cooldown:
                self.take_damage(10) 
                self.last_hit = now

    def ai(self):
        """Calculates distance to player; approaches until in range, then shoots."""

        enemy_to_player = pygame.Vector2(
            self.game.player.rect.centerx - self.rect.centerx,
            self.game.player.rect.centery - self.rect.centery
        )
        distance = enemy_to_player.length()

        if distance > self.detection_radius:
            self.x_change = 0
            self.y_change = 0

        elif distance > self.attack_range:
            if self.rect.x < self.game.player.rect.x:
                self.x_change = self.speed
            elif self.rect.x > self.game.player.rect.x:
                self.x_change = -self.speed

            if self.rect.y < self.game.player.rect.y:
                self.y_change = self.speed
            elif self.rect.y > self.game.player.rect.y:
                self.y_change = -self.speed
        else:
            self.shoot(enemy_to_player)

    def shoot(self, direction_vector: pygame.Vector2):
        """Spawns a projectile traveling toward the player if cooldown has expired.

        :param direction_vector: Vector tracking distance and angle to player target.
        """
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_cooldown:
            if self.game.sounds.get('enemy_shoot'):
                self.game.sounds['enemy_shoot'].play()
            self.last_shot = now
            Enemy_projectile(self.game, self.rect.centerx, self.rect.centery, direction_vector)

    def update(self):
        """Updates enemy state by executing AI logic, movement calculation, and damage checks."""
        self.ai()
        self.apply_movement()
        self.damage_intake()

class Enemy_projectile(pygame.sprite.Sprite):
    """A projectile shot by ranged enemies that travels toward the player.

    Inherits from Pygame's base Sprite class.
    """

    def __init__(self, game, x, y, direction: pygame.Vector2):
        self.game = game
        self._layer = Enemy_Layer
        self.groups = self.game.all_sprites, self.game.enemy_projectiles
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.width = 16
        self.height = 16

        base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, 'Assets/Sprites/ball.png')
        raw_image = pygame.image.load(full_path).convert_alpha()

        self.image = pygame.transform.scale(raw_image, (self.width, self.height))

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.direction = direction.normalize() if direction.length() != 0 else pygame.Vector2(1, 0)
        self.speed = 5

    def update(self):
        """Moves the projectile across the screen and checks for wall or player collisions."""
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        if pygame.sprite.spritecollide(self, self.game.blocks, False):
            self.kill()

        if pygame.sprite.collide_rect(self, self.game.player):
            now = pygame.time.get_ticks()
            if now - self.game.player.last_hit > self.game.player.damage_cooldown:
                if self.game.sounds.get('player_hurt'):
                    self.game.sounds['player_hurt'].play()
                self.game.player.take_damage(10)
                self.game.player.last_hit = now
            self.kill()

class Basic_Attack(pygame.sprite.Sprite):
    """An offensive projectile or swing animation triggered by the player."""
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
        """Advances the state of the basic attack object."""
        self.animate()

    def animate(self):
        """Cycles through directional frames and deletes the attack instance once complete."""
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
    """An interactive UI button element containing dynamic text and collision testing."""
    def __init__(self, x, y, width, height, font_color, background, content, fontsize):
        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, 'Assets/Sprites/AGoblinAppears-o2aV.ttf')
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
        """Determines if the mouse cursor overlaps the button and a mouse click is registered.

        :param position: Current coordinates of the mouse cursor (x, y).
        :param pressed: Mouse click state tuple representing mouse buttons.
        :return: True if the button is hovered and clicked, otherwise False.
        """
        if self.rect.collidepoint(position):
            if pressed[0]:
                return True
            return False
        return False
    
class Portal(pygame.sprite.Sprite):
    """A level transition objective that transports the player to a randomized layout."""
    def __init__(self, game, x, y):
        self.game = game
        self._layer = Wall_Layer
        self.groups = self.game.all_sprites, self.game.portals
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * Tilesize
        self.y = y * Tilesize
        
        self.image = pygame.Surface([Tilesize, Tilesize])
        self.image.fill(Purple) # Purple

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

class Big_Cheese(Entity):
    """The Big Cheese type shi"""

    def __init__(self, game, x: int, y: int):
        pixel_x = x * Tilesize
        pixel_y = y * Tilesize

        self.pos_x = float(pixel_x)
        self.pos_y = float(pixel_y)

        super().__init__(game, x, y, Enemy_Layer, (game.all_sprites, game.enemies), (255, 215, 0), 1000)

        self.width = 64
        self.height = 64

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill((255, 215, 0))

        self.rect = self.image.get_rect()
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        self.health_bar = Health_Bar(self, self.width, 6, 12)

        self.speed = Basic_Enemey_Speed * 0.6
        self.last_hit = 0
        self.damage_cooldown = 150

        self.states = ['WALKING', 'SHOOTING', 'OMNI_ATTACK', 'RESTING']
        self.current_state = 'WALKING'
        self.state_timer = pygame.time.get_ticks()

        self.walking_duration = 3000
        self.resting_duration = 2500
        self.attack_range = 250

        self.last_shot = 0
        self.shoot_cooldown = 800
        self.has_fired_omni = False

        self.last_teleport = pygame.time.get_ticks()
        self.teleport_cooldown = 7000

    def damage_intake(self):
        """Checks for incoming player attacks."""
        hits = pygame.sprite.spritecollide(self, self.game.attacks, False)
        if hits:
            if self.current_state == 'RESTING':
                now = pygame.time.get_ticks()
                if now - self.last_hit > self.damage_cooldown:
                    damage = 20
                    self.take_damage(damage)
                    self.last_hit = now
            else:
                #soundeffect here
                pass

    def ai(self):
        """Orchestrates boss behavior based on state timers and active phase constraints."""
        now = pygame.time.get_ticks()

        boss_to_player = pygame.Vector2(
            self.game.player.rect.centerx - self.rect.centerx,
            self.game.player.rect.centery - self.rect.centery
        )
        distance = boss_to_player.length()

        if now - self.last_teleport > self.teleport_cooldown:
            self.teleport_behind_player()
            self.last_teleport = now

        if self.current_state == 'WALKING':
            if distance > self.attack_range:
                self.x_change = self.speed if boss_to_player.x > 0 else -self.speed
                self.y_change = self.speed if boss_to_player.y > 0 else -self.speed
            else:
                self.x_change = 0
                self.y_change = 0

            if now - self.state_timer > self.walking_duration:
                self.current_state = random.choice(['SHOOTING', 'OMNI_ATTACK'])
                self.state_timer = now
                self.has_fired_omni = False

        elif self.current_state == 'SHOOTING':
            self.x_change = 0
            self.y_change = 0

            if now - self.last_shot > self.shoot_cooldown:
                if self.game.sounds.get('cheese_attack'):
                    self.game.sounds['cheese_attack'].play()
                self.last_shot = now
                Boss_projectile(self.game, self.rect.centerx, self.rect.centery, boss_to_player, size=24, speed=6.5)

            if now - self.state_timer > 3000:
                self.current_state = 'RESTING'
                self.state_timer = now

        elif self.current_state == 'OMNI_ATTACK':
            self.x_change = 0
            self.y_change = 0

            if not self.has_fired_omni:
                angles = [
                    pygame.Vector2(1, 0), pygame.Vector2(-1, 0),
                    pygame.Vector2(0, 1), pygame.Vector2(0, -1),
                    pygame.Vector2(1, 1), pygame.Vector2(-1, 1), 
                    pygame.Vector2(1, -1), pygame.Vector2(-1, -1)
                ]
                for target_dir in angles:
                    if self.game.sounds.get('cheese_attack'):
                        self.game.sounds['cheese_attack'].play()
                    Boss_projectile(self.game, self.rect.centerx, self.rect.centery, target_dir, size=12, speed=4.0)
                self.has_fired_omni = True

            if now - self.state_timer > 1000:
                self.current_state = 'RESTING'
                self.state_timer = now

        elif self.current_state == 'RESTING':
            self.x_change = 0
            self.y_change = 0
            self.image.fill((139, 0, 0))

            if now - self.state_timer > self.resting_duration:
                self.image.fill((255, 215, 0))
                self.current_state = 'WALKING'
                self.state_timer = now

    def teleport_behind_player(self):
        """Finds the player's rear direction and shifts coordinates instantly."""
        player_facing = self.game.player.facing
        offset = Tilesize * 2
        
        new_x = self.game.player.rect.x
        new_y = self.game.player.rect.y

        if player_facing == 'up':    new_y += offset
        elif player_facing == 'down':  new_y -= offset
        elif player_facing == 'left':  new_x += offset
        elif player_facing == 'right': new_x -= offset

        self.rect.x = int(new_x)
        self.rect.y = int(new_y)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        # if self.game.sounds.get('cheese_teleport'):
        #     self.game.sounds['cheese_teleport'].play()

    def update(self):
        """Updates boss state by executing AI logic, movement calculation, and damage checks."""
        self.ai()
        self.apply_movement()
        self.damage_intake()

class Boss_projectile(pygame.sprite.Sprite):
    """A small projectile fired by the boss in various directional patterns."""

    def __init__(self, game, x: int, y: int, direction: pygame.Vector2, size: int = 12, speed: float = 5.0):
        self.game = game
        self._layer = Enemy_Layer
        self.groups = self.game.all_sprites, self.game.enemy_projectiles
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.width = size
        self.height = size

        base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, 'Assets/Sprites/ball.png')
        raw_image = pygame.image.load(full_path).convert_alpha()
        self.image = pygame.transform.scale(raw_image, (self.width, self.height))

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.direction = direction.normalize() if direction.length() != 0 else pygame.Vector2(1, 0)
        self.speed = speed

    def update(self):
        """Moves the projectile and handles screen bounds or player damage."""
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        if pygame.sprite.spritecollide(self, self.game.blocks, False):
            self.kill()

        if pygame.sprite.collide_rect(self, self.game.player):
            now = pygame.time.get_ticks()
            if now - self.game.player.last_hit > self.game.player.damage_cooldown:
                if self.game.sounds.get('player_hurt'):
                    self.game.sounds['player_hurt'].play()
                self.game.player.take_damage(15)
                self.game.player.last_hit = now
            self.kill()

class Krysa_Macek(Entity):
    """A charging boss entity that dashes in straight lines through map corridors and rests at spawn."""

    def __init__(self, game, x: int, y: int):
        pixel_x = x * Tilesize
        pixel_y = y * Tilesize

        self.pos_x = float(pixel_x)
        self.pos_y = float(pixel_y)

        super().__init__(game, x, y, Enemy_Layer, (game.all_sprites, game.enemies), (128, 128, 128), 750)

        self.width = 128
        self.height = 128

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(Gray)

        self.rect = self.image.get_rect()
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        self.spawn_x = float(self.pos_x)
        self.spawn_y = float(self.pos_y)


        self.health_bar = Health_Bar(self, self.width, 6, 12)

        self.last_hit = 0
        self.damage_cooldown = 300

        self.current_state = 'RESTING'
        self.state_timer = pygame.time.get_ticks()

        self.resting_duration = 4000
        self.prep_duration = 1000

        self.dash_speed = Basic_Enemey_Speed * 4.5
        self.return_speed = Basic_Enemey_Speed * 1.5

        self.dash_direction = pygame.Vector2(0, 0)
        self.dash_choices = [
            pygame.Vector2(1, 0),
            pygame.Vector2(-1, 0),
            pygame.Vector2(0, 1),
            pygame.Vector2(0, -1)
        ]

    def damage_intake(self):
        """Applies weapon damage to the boss ONLY when it is in the RESTING phase."""
        hits = pygame.sprite.spritecollide(self, self.game.attacks, False)
        if hits:
            if self.current_state == 'RESTING':
                now = pygame.time.get_ticks()
                if now - self.last_hit > self.damage_cooldown:
                    self.take_damage(15)
                    self.last_hit = now

    def ai(self):
        """Dashes continuously through corridors, turning at walls with a random chance to rest."""
        now = pygame.time.get_ticks()
        import random

        if self.current_state == 'RESTING':
            self.x_change = 0
            self.y_change = 0
            self.image.fill(Green)

            if now - self.state_timer > self.resting_duration:
                self.current_state = 'PREPARING'
                self.state_timer = now

        elif self.current_state == 'PREPARING':
            self.x_change = 0
            self.y_change = 0
            self.image.fill(Orange)

            if now - self.state_timer > self.prep_duration:
                valid_dirs = []
                for direction in self.dash_choices:
                    test_rect = self.rect.copy()
                    test_rect.x += int(direction.x * self.dash_speed)
                    test_rect.y += int(direction.y * self.dash_speed)
                    if not any(test_rect.colliderect(block.rect) for block in self.game.blocks):
                        valid_dirs.append(direction)

                self.dash_direction = random.choice(valid_dirs) if valid_dirs else random.choice(self.dash_choices)
                self.current_state = 'DASHING'
                self.state_timer = now

                if self.game.sounds.get('macek_charge'):
                    self.game.sounds['macek_charge'].play()

        elif self.current_state == 'DASHING':
            if self.game.sounds.get('macek_dash'):
                    self.game.sounds['macek_dash'].play()
            self.image.fill(Gray)
            
            self.x_change = self.dash_direction.x * self.dash_speed
            self.y_change = self.dash_direction.y * self.dash_speed

            future_rect = self.rect.copy()
            future_rect.x += int(self.x_change)
            future_rect.y += int(self.y_change)
            
            wall_hits = any(future_rect.colliderect(block.rect) for block in self.game.blocks)

            if wall_hits:
                opposite_dir = -self.dash_direction
                alternatives = []

                for direction in self.dash_choices:
                    if direction == opposite_dir or direction == self.dash_direction:
                        continue

                    test_rect = self.rect.copy()
                    test_rect.x += int(direction.x * self.dash_speed)
                    test_rect.y += int(direction.y * self.dash_speed)
                    if not any(test_rect.colliderect(block.rect) for block in self.game.blocks):
                        alternatives.append(direction)

                if alternatives:
                    self.dash_direction = random.choice(alternatives)
                else:
                    self.dash_direction = opposite_dir

                if random.random() < 0.30:
                    self.current_state = 'RESTING'
                    self.state_timer = now
                else:
                    self.rect.x += int(self.dash_direction.x * self.dash_speed)
                    self.rect.y += int(self.dash_direction.y * self.dash_speed)

    def player_collision(self):
        """Deals massive contact collision damage if the player fails to dodge the dash."""
        if pygame.sprite.collide_rect(self, self.game.player):
            now = pygame.time.get_ticks()
            if now - self.game.player.last_hit > self.game.player.damage_cooldown:
                damage_amt = 0 if self.current_state == 'RESTING' else 25
                if damage_amt > 0:
                    if self.game.sounds.get('player_hurt'):
                        self.game.sounds['player_hurt'].play()
                    self.game.player.take_damage(damage_amt)
                    self.game.player.last_hit = now

    def update(self):
        """Tracks core AI routines, coordinates transforms, and triggers player damage sweeps."""
        self.ai()
        self.apply_movement()
        self.damage_intake()
        self.player_collision()