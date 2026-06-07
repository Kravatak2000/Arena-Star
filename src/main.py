import pygame
from config import *
from sprites import *
import sys
import random

class Game:
    """The central manager of the game lifecycle, handling loop setups, inputs, and updates."""
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((Win_Width, Win_Height), pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.running = True

        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, 'Assets/Sprites/AGoblinAppears-o2aV.ttf')
        self.font = pygame.font.Font(font_path, 70)
        self.small_font = pygame.font.Font(font_path, 35)
        self.extra_small_font = pygame.font.Font(font_path, 25)

        self.basic_attack_spritesheet = Spritesheet('Assets/Sprites/attack.png')
        
        intro_background_path = os.path.join(base_path, 'Assets/Sprites/hannah-oates-brick-wall-wip.jpg')
        original_bg = pygame.image.load(intro_background_path)

        self.intro_background = pygame.transform.scale(original_bg, (Win_Width, Win_Height))

        self.sounds = {}
        sound_files = {
            'player_attack': 'Assets/Sounds/player_attack.mp3',
            'player_dash': 'Assets/Sounds/player_dash.wav',
            'player_hurt': 'Assets/Sounds/player_hurt.wav',
            'enemy_shoot': 'Assets/Sounds/enemy_attack.mp3',
            'macek_charge': 'Assets/Sounds/krysa_macek.mp3',
            'macek_dash': 'Assets/Sounds/macek_dash.mp3',
            # 'cheese_teleport': 'Assets/Sounds/cheese_teleport.wav',
            'cheese_attack': 'Assets/Sounds/enemy_attack_2.wav',
        }

        for name, path in sound_files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
                self.sounds[name].set_volume(0.3)
            except pygame.error as e:
                print(f"Could not load sound effect {name}: {e}")
                self.sounds[name] = None

        self.current_level_num = 1
        self.available_levels = []
        

    def create_map(self, map_data):
        """Clears old assets and populates game groups based on string matrix maps.

        :param map_data: Multidimensional list of characters representing structural layouts.
        """
        for sprite in self.all_sprites:
            sprite.kill()

        for i, row in enumerate(map_data):
            for j, column in enumerate(row):
                if column == "B":
                    Wall(self, j, i)
                if column == "E":
                    Basic_enemy(self, j, i)
                if column == "R":
                    Ranged_enemy(self, j, i)
                if column == "C":
                    Big_Cheese(self, j, i)
                if column == "K":
                    Krysa_Macek(self, j, i)
                if column == "T":
                    self.exit_portal = Portal(self, j, i)
                    self.exit_portal.kill()
                if column == "P":
                    if hasattr(self, 'player'):
                        self.player.rect.x = j * Tilesize
                        self.player.rect.y = i * Tilesize
                        self.all_sprites.add(self.player)
                    else:
                        self.player = Player(self, j, i)

    def new(self):
        """Resets variables, instantiates new sprite layering setups, and loads index maps."""
        #new game starts
        self.playing = True
        self.current_level_num = 1
        self.loop_count = 0

        if hasattr(self, 'player'):
            del self.player

        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.blocks = pygame.sprite.LayeredUpdates()
        self.enemies = pygame.sprite.LayeredUpdates()
        self.portals = pygame.sprite.LayeredUpdates()
        self.attacks = pygame.sprite.LayeredUpdates()
        self.enemy_projectiles = pygame.sprite.LayeredUpdates()

        self.play_bg_music("level.mp3")

        self.available_levels = list(range(1, len(Tilemaps)))

        self.create_map(Tilemaps[0])
        # self.player = Player(self, 10, 10)

    def events(self):
        """Polls engine window callbacks, handling character attacks and general keystrokes."""
        #game loop events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.sounds.get('player_attack'):
                            self.sounds['player_attack'].play()
                    if self.player.facing == 'up':
                        Basic_Attack(self, self.player.rect.x, self.player.rect.y - Tilesize)
                    if self.player.facing == 'down':
                        Basic_Attack(self, self.player.rect.x, self.player.rect.y + Tilesize)
                    if self.player.facing == 'left':
                        Basic_Attack(self, self.player.rect.x - Tilesize, self.player.rect.y)
                    if self.player.facing == 'right':
                        Basic_Attack(self, self.player.rect.x + Tilesize, self.player.rect.y)

                if event.key == pygame.K_h:
                    if self.sounds.get('player_hurt'):
                        self.sounds['player_hurt'].play()
                    self.player.hp -= 10

                if event.key == pygame.K_ESCAPE:
                    self.playing = False
                    self.running = False


    def update(self):
        """Invokes group tick trackers and processes player portal collision transitions."""
        #game loop updaes
        self.all_sprites.update()

        if hasattr(self, 'exit_portal') and not self.exit_portal.alive():
            if len(self.enemies) == 0:
                self.all_sprites.add(self.exit_portal)
                self.portals.add(self.exit_portal)

        hits = pygame.sprite.spritecollide(self.player, self.portals, False)
        if hits:
            if not self.available_levels:
                self.available_levels = list(range(1, len(Tilemaps)))
                self.loop_count += 1

            random_index = random.choice(self.available_levels)
            
            self.available_levels.remove(random_index)

            self.current_level_num += 1
            self.create_map(Tilemaps[random_index])

    def draw(self):
        """Renders all updated entities and matching UI health meters to screen viewports."""
        self.screen.fill(Black)
        self.all_sprites.draw(self.screen)
        for sprite in self.all_sprites:
            if hasattr(sprite, 'health_bar'):
                sprite.health_bar.draw(self.screen)

        rooms_cleared = self.current_level_num - 1
        score_text = self.small_font.render(f"Score: {rooms_cleared}", True, White)

        self.screen.blit(score_text, (15, 15))

        self.clock.tick(Fps)
        pygame.display.update()

    def main(self):
        """Orchestrates standard structural ticks while the gameplay scene remains active."""
        #game loop
        while self.playing:
            self.events()
            self.update()
            self.draw()

    def game_over(self):
        """Halts runs upon player death and renders interactive restart/retry menus."""
        self.play_bg_music("game_not_over.mp3")
        title = self.font.render('You have died', True, Red)
        title_rect = title.get_rect(center=(Win_Width // 2, 260))
        # x = Win_width/2

        final_score = self.current_level_num - 1
        score_title = self.small_font.render(f"Final Score: {final_score} Rooms Cleared", True, (255, 215, 0))
        score_rect = score_title.get_rect(center=(Win_Width // 2, 390))

        restart_button = Button((Win_Width // 2) - 150, 480, 300, 50, White, Stone_gray, 'Try Again', 30)
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
            self.screen.blit(score_title, score_rect)
            self.screen.blit(restart_button.image, restart_button.rect)
            self.clock.tick(Fps)
            pygame.display.update()

    def help_screen(self):
        """Displays the help/controls page"""
        helping = True
        
        back_button = Button(10, 10, 100, 50, White, Stone_gray, 'Back', 20)
        

        lines = [
            "CONTROLS",
            "",
            "WASD / ARROWS: Move",
            "SPACE: Attack",
            "SHIFT: Dash",
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
                self.screen.blit(content, (50, 100 + (i * 50)))
            
            self.screen.blit(back_button.image, back_button.rect)
            
            self.clock.tick(Fps)
            pygame.display.update()

    def intro_screen(self):
        """Displays the splash welcome viewport until the user clicks the play option button."""
        intro = True
        self.play_bg_music("main_theme.mp3")

        title = self.font.render('Arena Star', True, White)
        title_rect = title.get_rect(center=(Win_Width // 2, 300))

        play_button = Button((Win_Width // 2) - 62, 480, 125, 50, White, Stone_gray, 'Play', 30)

        help_button = Button((Win_Width // 2) - 62, 560, 125, 50, White, Stone_gray, 'Help', 30)

        credits_button = Button((Win_Width // 2) - 120, 640, 240, 50, White, Stone_gray, 'Credits', 30)

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
            
            if credits_button.is_pressed(mouse_pos, mouse_pressed):
                self.credits_screen()

            self.screen.blit(self.intro_background, (0,0))
            self.screen.blit(title, title_rect)
            self.screen.blit(play_button.image, play_button.rect)
            self.screen.blit(help_button.image, help_button.rect)
            self.screen.blit(credits_button.image, credits_button.rect)
            self.clock.tick(Fps)
            pygame.display.update()

    def credits_screen(self):
        """Displays the music credits page."""
        crediting = True
        
        back_button = Button(10, 10, 100, 50, White, Stone_gray, 'Back', 20)

        lines = [
            "MUSIC CREDITS",
            "",
            "Main Menu Theme:", 
            "'Mountain Trials' by Joshua McLean",
            "Gameplay Theme:",
            "'Dungeon Boss' by Kevin MacLeod",
            "Game Over Theme:",
            "'Papers Please - Death Theme' by Lucas Pope"
        ]

        while crediting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    crediting = False
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        crediting = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if back_button.is_pressed(mouse_pos, mouse_pressed):
                crediting = False

            self.screen.blit(self.intro_background, (0, 0))

            for i, text in enumerate(lines):
                content = self.extra_small_font.render(text, True, White)
                self.screen.blit(content, (50, 100 + (i * 50)))
            
            self.screen.blit(back_button.image, back_button.rect)
            
            self.clock.tick(Fps)
            pygame.display.update()

    def play_bg_music(self, song_name):
        """Loads and infinitely loops a specific background track safely."""

        music_path = f"Assets/Music/{song_name}"
        
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1) #-1 protoze to da loop
            pygame.mixer.music.set_volume(0.5)
        except pygame.error as e:
            print(f"Could not load music file {song_name}: {e}")

g = Game()
g.intro_screen()
g.new()
while g.running:
    g.main()
    g.game_over()

pygame.quit()
sys.exit()