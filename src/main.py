import pygame
from config import *
from sprites import *
import sys

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Win_Width, Win_Height), pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.running = True

        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, 'Assets/AGoblinAppears-o2aV.ttf')
        self.font = pygame.font.Font(font_path, 38)
        self.small_font = pygame.font.Font(font_path, 22)

        self.basic_attack_spritesheet = Spritesheet('Assets/attack.png')
        
        intro_background_path = os.path.join(base_path, 'Assets/hannah-oates-brick-wall-wip.jpg')
        self.intro_background = pygame.image.load(intro_background_path)
        

    def create_map(self, map_data):
        for sprite in self.all_sprites:
            sprite.kill()

        for i, row in enumerate(map_data):
            for j, column in enumerate(row):
                if column == "B":
                    Wall(self, j, i)
                if column == "E":
                    Basic_enemy(self, j, i)
                if column == "T":
                    Portal(self, j, i) 
                if column == "P":
                    if hasattr(self, 'player'):
                        self.player.rect.x = j * Tilesize
                        self.player.rect.y = i * Tilesize
                        self.all_sprites.add(self.player)
                    else:
                        self.player = Player(self, j, i)

    def new(self):
        #new game starts
        self.playing = True

        if hasattr(self, 'player'):
            del self.player

        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.blocks = pygame.sprite.LayeredUpdates()
        self.enemies = pygame.sprite.LayeredUpdates()
        self.portals = pygame.sprite.LayeredUpdates()
        self.attacks = pygame.sprite.LayeredUpdates()

        self.create_map(Tilemaps[0])
        # self.player = Player(self, 10, 10)

    def events(self):
        #game loop events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.player.facing == 'up':
                        Basic_Attack(self, self.player.rect.x, self.player.rect.y - Tilesize)
                    if self.player.facing == 'down':
                        Basic_Attack(self, self.player.rect.x, self.player.rect.y + Tilesize)
                    if self.player.facing == 'left':
                        Basic_Attack(self, self.player.rect.x - Tilesize, self.player.rect.y)
                    if self.player.facing == 'right':
                        Basic_Attack(self, self.player.rect.x + Tilesize, self.player.rect.y)

                if event.key == pygame.K_h:
                    self.player.hp -= 10

                if event.key == pygame.K_ESCAPE:
                    self.playing = False
                    self.running = False


    def update(self):
        #game loop updaes
        self.all_sprites.update()

        hits = pygame.sprite.spritecollide(self.player, self.portals, False)
        if hits:
            import random
            new_layout = random.choice(Tilemaps)
            self.create_map(new_layout)

    def draw(self):
        self.screen.fill(Black)
        self.all_sprites.draw(self.screen)
        for sprite in self.all_sprites:
            if hasattr(sprite, 'health_bar'):
                sprite.health_bar.draw(self.screen)

        self.clock.tick(Fps)
        pygame.display.update()

    def main(self):
        #game loop
        while self.playing:
            self.events()
            self.update()
            self.draw()

    def game_over(self):
        title = self.font.render('You have died', True, Red)
        title_rect = title.get_rect(x=80, y=150)
        # x = Win_width/2

        restart_button = Button(160, 240, 300, 50, White, Stone_gray, 'Try Again', 30)
        for sprite in self.all_sprites:
            sprite.kill()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if restart_button.is_pressed(mouse_pos, mouse_pressed):
                self.new()
                self.main()

            self.screen.blit(self.intro_background, (0,0))
            self.screen.blit(title, title_rect)
            self.screen.blit(restart_button.image, restart_button.rect)
            self.clock.tick(Fps)
            pygame.display.update()

    def help_screen(self):
        helping = True
        
        back_button = Button(10, 10, 100, 50, White, Stone_gray, 'Back', 20)
        

        lines = [
            "CONTROLS",
            "",
            "WASD / ARROWS: Move",
            "SPACE: Attack",
            "H: Self Harm",
            "ESC: Quit Game"
        ]

        while helping:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    helping = False
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        helping = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if back_button.is_pressed(mouse_pos, mouse_pressed):
                helping = False

            self.screen.blit(self.intro_background, (0, 0))

            for i, text in enumerate(lines):
                content = self.small_font.render(text, True, White)
                self.screen.blit(content, (50, 100 + (i * 30)))
            
            self.screen.blit(back_button.image, back_button.rect)
            
            self.clock.tick(Fps)
            pygame.display.update()

    def intro_screen(self):
        intro = True

        title = self.font.render('Arena Star', True, White)
        title_rect = title.get_rect(x=120, y=150)

        play_button = Button(250, 240, 125, 50, White, Stone_gray, 'Play', 30)

        help_button = Button(250, 310, 125, 50, White, Stone_gray, 'Help', 30)

        while intro:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    intro = False
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        intro = False
                        self.running = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if play_button.is_pressed(mouse_pos, mouse_pressed):
                intro = False

            if help_button.is_pressed(mouse_pos, mouse_pressed):
                self.help_screen()

            self.screen.blit(self.intro_background, (0,0))
            self.screen.blit(title, title_rect)
            self.screen.blit(play_button.image, play_button.rect)
            self.screen.blit(help_button.image, help_button.rect)
            self.clock.tick(Fps)
            pygame.display.update()

g = Game()
g.intro_screen()
g.new()
while g.running:
    g.main()
    g.game_over()

pygame.quit()
sys.exit()