import pickle
import pygame
import neat
import sys
import random

# Refer to game.py for the comments on how the game works

# Load the genome (replace "best_genome.pkl" if you save a new one that has a different name)
with open("best_genome.pkl", "rb") as f:
	best_genome = pickle.load(f)

config_path = "config.txt"
config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
							neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

net = neat.nn.FeedForwardNetwork.create(best_genome, config)


# Mostly everything else is the same as game.py
def draw_floor():
	screen.blit(floor_surface,(floor_x_pos,900))
	screen.blit(floor_surface,(floor_x_pos + 576,900))

def create_pipe():
	random_pipe_pos = random.choice(pipe_height)
	bottom_pipe = pipe_surface.get_rect(midtop = (700,random_pipe_pos))
	top_pipe = pipe_surface.get_rect(midbottom = (700,random_pipe_pos - 300))
	return bottom_pipe,top_pipe

def move_pipes(pipes):
	for pipe in pipes:
		pipe.centerx -= 5
	visible_pipes = [pipe for pipe in pipes if pipe.right > -50]
	return visible_pipes

def draw_pipes(pipes):
	for pipe in pipes:
		if pipe.bottom >= 1024:
			screen.blit(pipe_surface,pipe)
		else:
			flip_pipe = pygame.transform.flip(pipe_surface,False,True)
			screen.blit(flip_pipe,pipe)




def score_display(game_state, bird):
	if game_state == 'main_game':
		score_surface = game_font.render(str(int(bird.score)),True,(255,255,255))
		score_rect = score_surface.get_rect(center = (288,100))
		screen.blit(score_surface,score_rect)
	if game_state == 'game_over':
		score_surface = game_font.render(f'Score: {int(bird.score)}' ,True,(255,255,255))
		score_rect = score_surface.get_rect(center = (288,100))
		screen.blit(score_surface,score_rect)

		high_score_surface = game_font.render(f'High score: {int(bird.high_score)}',True,(255,255,255))
		high_score_rect = high_score_surface.get_rect(center = (288,850))
		screen.blit(high_score_surface,high_score_rect)

def pipe_score_check(bird):
	
	if pipe_list:
		for pipe in pipe_list:
			if 95 < pipe.centerx < 105 and bird.can_score:
				bird.score += 1
				score_sound.play()
				bird.can_score = False
			if pipe.centerx < 0:
				bird.can_score = True

#pygame.mixer.pre_init(frequency = 44100, size = 16, channels = 2, buffer = 1024)
class Bird:
	def __init__(self, bird_downflap, bird_midflap, bird_upflap):
		self.bird_movement = 0
		self.bird_frames = [bird_downflap,bird_midflap,bird_upflap]
		self.bird_index = 0
		self.bird_surface = self.bird_frames[self.bird_index]
		self.bird_rect = self.bird_surface.get_rect(center = (100,512))
		self.score = 0
		self.high_score = 0
		self.rotated_bird = None
		self.can_score = True
	def draw_visuals(self, screen, pipes):
		# Get bird's position (center of bird)
		bird_x, bird_y = self.bird_rect.centerx, self.bird_rect.centery
		
		# Get the pipe positions using `get_data` method
		pipe_data = self.get_data_xy(pipes)
		
		# Draw line from bird to each pipe (we're assuming there's at least one pipe)
		for i in range(2):  # Since you need only 2 pipes (top and bottom)
				pipe_x = pipe_data[2+i * 2]
				pipe_y = pipe_data[3+i * 2]
				# Draw a line from the bird's center to the pipe's center
				pygame.draw.line(screen, (255, 0, 0), (bird_x, bird_y), (pipe_x, pipe_y), 2)
	def rotate_bird(self):
		new_bird = pygame.transform.rotozoom(self.bird_surface,-self.bird_movement * 3,1)
		return new_bird
	def bird_animation(self):
		new_bird = self.bird_frames[self.bird_index]
		new_bird_rect = new_bird.get_rect(center = (100,self.bird_rect.centery))
		self.bird_surface, self.bird_rect = new_bird,new_bird_rect
	def check_collision(self, pipes):
		for pipe in pipes:
			if self.bird_rect.colliderect(pipe):
				death_sound.play()
				self.can_score = True
				return False

		if self.bird_rect.top <= -100 or self.bird_rect.bottom >= 900:
			self.can_score = True
			return False

		return True
	def get_data(self, pipes):
		if pipes != []:
			next_pipes = []
			counter = 0 # we only need 2 (top and bottom)
			for pipe in pipes:
				if pipe.centerx > 100 - pipe.width:
					next_pipes.append(pipe)
					counter += 1
				if counter == 2:
					break
			if next_pipes:
				data = [self.bird_movement, self.bird_rect.centery, next_pipes[0].y, next_pipes[1].y + next_pipes[1].height]
			else:
				data = [self.bird_movement, self.bird_rect.centery, pipes[0].y, pipes[1].y + pipes[1].height]
		else:
			data = [self.bird_movement, self.bird_rect.centery, 600, 300]
		return data
	def get_data_xy(self, pipes):
		if pipes != []:
			next_pipes = []
			counter = 0 # we only need 2 (top and bottom)
			for pipe in pipes:
				if pipe.centerx > 100 - pipe.width:
					next_pipes.append(pipe)
					counter += 1
				if counter == 2:
					break
			if next_pipes:
				data = [self.bird_movement, self.bird_rect.centery, next_pipes[0].x, next_pipes[0].y, next_pipes[1].x,next_pipes[1].y + next_pipes[1].height]
			else:
				data = [self.bird_movement, self.bird_rect.centery, pipes[0].x, pipes[0].y, pipes[1].x , pipes[1].y + pipes[1].height]
		else:
			data = [self.bird_movement, self.bird_rect.centery,576, 600,576,300]
		return data

pygame.init()
screen = pygame.display.set_mode((576,1024))
clock = pygame.time.Clock()
game_font = pygame.font.Font('04B_19.ttf',40)

# Game Variables
gravity = 0.25
game_active = True
bg_surface = pygame.image.load('assets/background-day.png').convert()
bg_surface = pygame.transform.scale2x(bg_surface)

floor_surface = pygame.image.load('assets/base.png').convert()
floor_surface = pygame.transform.scale2x(floor_surface)
floor_x_pos = 0

bird_downflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-downflap.png').convert_alpha())
bird_midflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
bird_upflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-upflap.png').convert_alpha())

bird = Bird(bird_downflap, bird_midflap, bird_upflap)

BIRDFLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRDFLAP,200)

# bird_surface = pygame.image.load('assets/bluebird-midflap.png').convert_alpha()
# bird_surface = pygame.transform.scale2x(bird_surface)
# bird_rect = bird_surface.get_rect(center = (100,512))

pipe_surface = pygame.image.load('assets/pipe-green.png')
pipe_surface = pygame.transform.scale2x(pipe_surface)
pipe_list = []
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE,1200)
pipe_height = [400,600,800]

game_over_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
game_over_rect = game_over_surface.get_rect(center = (288,512))

flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
death_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
score_sound_countdown = 100
SCOREEVENT = pygame.USEREVENT + 2
pygame.time.set_timer(SCOREEVENT,100)
PIPE_SPAWN_INTERVAL = 1800  # Spawn pipes every 2000 ms
pipe_timer = 0  # Time accumulator for pipe spawning

while True:
	delta_time = clock.tick(120) / 1000.0  # Time in seconds since last frame
	pipe_timer += delta_time * 1000  # Convert delta_time to milliseconds for comparison
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

		if event.type == BIRDFLAP:
			if bird.bird_index < 2:
				bird.bird_index += 1
			else:
				bird.bird_index = 0

			bird.bird_animation()
	# Checks if bird ANN wants to press space basically
	output = net.activate(bird.get_data(pipe_list)) 
	if game_active:
		if output[0] > 0:
			bird.bird_movement = 0
			bird.bird_movement -= 7
			flap_sound.play()
	else:
		game_active = True
		pipe_list.clear()
		bird.bird_rect.center = (100,512)
		bird.bird_movement = 0
		bird.score = 0

	screen.blit(bg_surface,(0,0))

	if pipe_timer >= PIPE_SPAWN_INTERVAL:
			pipe_list.extend(create_pipe())
			pipe_timer = 0  # Reset pipe timer
	if game_active:
		# Bird
		bird.bird_movement += gravity
		bird.rotated_bird = bird.rotate_bird()
		bird.bird_rect.centery += bird.bird_movement
		screen.blit(bird.rotated_bird,bird.bird_rect)
		game_active = bird.check_collision(pipe_list)

		for pipe in pipe_list:
			pipe.centerx -= 6 * delta_time * 60  # Adjust for delta_time
		pipe_list = [pipe for pipe in pipe_list if pipe.right > -50]
		draw_pipes(pipe_list)
		
		# Score
		pipe_score_check(bird)
		score_display('main_game', bird)
	else:
		screen.blit(game_over_surface,game_over_rect)
		bird.high_score = max(bird.score,bird.high_score)
		score_display('game_over', bird)


	# Floor
	floor_x_pos -= 1
	draw_floor()
	if floor_x_pos <= -576:
		floor_x_pos = 0
	

	pygame.display.update()
	
