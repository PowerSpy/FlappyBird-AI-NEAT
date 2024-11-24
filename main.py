import pickle
import pygame, sys, random 
import neat
generation = 0
# Refer to the game.py script for comments on game functionality since I'm too lazy to add them here
def draw_floor(screen, floor_surface, floor_x_pos):
	screen.blit(floor_surface,(floor_x_pos,900))
	screen.blit(floor_surface,(floor_x_pos + 576,900))

def create_pipe(pipe_height, pipe_surface):
	random_pipe_pos = random.choice(pipe_height)
	bottom_pipe = pipe_surface.get_rect(midtop = (700,random_pipe_pos))
	top_pipe = pipe_surface.get_rect(midbottom = (700,random_pipe_pos - 300))
	return bottom_pipe,top_pipe

def move_pipes(pipes):
	for pipe in pipes:
		pipe.centerx -= 2
	visible_pipes = [pipe for pipe in pipes if pipe.right > -50]
	return visible_pipes

def draw_pipes(screen, pipes, pipe_surface):
	for pipe in pipes:
		if pipe.bottom >= 1024:
			screen.blit(pipe_surface,pipe)
		else:
			flip_pipe = pygame.transform.flip(pipe_surface,False,True)
			screen.blit(flip_pipe,pipe)




def score_display(screen, game_state, bird, game_font):
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


def pipe_score_check(bird, pipe_list):
	
	if pipe_list:
		for pipe in pipe_list:
			if 95 < pipe.centerx < 105 and bird.can_score:
				bird.score += 1
				bird.can_score = False
				return 1
			if pipe.centerx < 0:
				bird.can_score = True
	return 0

#pygame.mixer.pre_init(frequency = 44100, size = 16, channels = 2, buffer = 1024)
class Bird:
	def __init__(self, bird_downflap, bird_midflap, bird_upflap):
		self.alive = True
		self.bird_movement = 0
		self.bird_frames = [bird_downflap,bird_midflap,bird_upflap]
		self.bird_index = 0
		self.bird_surface = self.bird_frames[self.bird_index]
		self.bird_rect = self.bird_surface.get_rect(center = (100,512))
		self.score = 0
		self.high_score = 0
		self.rotated_bird = None
		self.can_score = True
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
				self.can_score = True
				return False

		if self.bird_rect.top <= -100 or self.bird_rect.bottom >= 900:
			self.can_score = True
			return False

		return True
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

	# Returns the parameters passed into the neural net
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
	# Returns the some stuff for visualization
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
# Main game loop (takes genomes for all birds and config file)
def game_loop(genomes, config):
	pygame.init()
	
	# Each birds respective ANN and object
	nets = []
	birds = []
	
	screen = pygame.display.set_mode((576, 1024))
	clock = pygame.time.Clock()
	game_font = pygame.font.Font('04B_19.ttf', 40)
	
	bird_downflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-downflap.png').convert_alpha())
	bird_midflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
	bird_upflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-upflap.png').convert_alpha())
	
	for id, g in genomes:
		# for each genome in the input (bird) it will create a new bird
		net = neat.nn.FeedForwardNetwork.create(g, config) # ANN
		nets.append(net)
		g.fitness = 0
		birds.append(Bird(bird_downflap, bird_midflap, bird_upflap))
	
	# Game Variables
	gravity = 0.25
	bg_surface = pygame.image.load('assets/background-day.png').convert()
	bg_surface = pygame.transform.scale2x(bg_surface)
	floor_surface = pygame.image.load('assets/base.png').convert()
	floor_surface = pygame.transform.scale2x(floor_surface)
	floor_x_pos = 0
	pipe_surface = pygame.image.load('assets/pipe-green.png')
	pipe_surface = pygame.transform.scale2x(pipe_surface)
	pipe_list = []
	pipe_height = [400, 600, 800]
	frame_counter = 0
	PIPE_SPAWN_INTERVAL = 1800  # Spawn pipes every 2000 ms
	pipe_timer = 0  # Time accumulator for pipe spawning
	FITNESS_THRESH = 10000
	global generation
	generation += 1

	while True:
		delta_time = clock.tick(120) / 1000.0  # Time in seconds since last frame
		pipe_timer += delta_time * 1000  # Convert delta_time to milliseconds for comparison
		
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			if event.type == pygame.USEREVENT + 1:  # BIRDFLAP
				for bird in birds:
					bird.bird_index = (bird.bird_index + 1) % 3
					bird.bird_animation()
		
		# Spawn pipes based on timer
		if pipe_timer >= PIPE_SPAWN_INTERVAL:
			pipe_list.extend(create_pipe(pipe_height, pipe_surface))
			pipe_timer = 0  # Reset pipe timer

		for i, bird in enumerate(birds):
			if bird.alive:
				output = nets[i].activate(bird.get_data(pipe_list))
				if output[0] > 0:
					bird.bird_movement = -7

		screen.blit(bg_surface, (0, 0))

		remaining = 0
		for i, bird in enumerate(birds):
			if bird.alive:
				bird.alive = bird.check_collision(pipe_list)
			if bird.alive:
				remaining += 1
				bird.bird_movement += gravity * delta_time * 60  # Scale gravity to match delta_time
				bird.rotated_bird = bird.rotate_bird()
				bird.bird_rect.centery += bird.bird_movement
				screen.blit(bird.rotated_bird, bird.bird_rect)

				# Score and fitness updates
				score = pipe_score_check(bird, pipe_list)
				# Gives them some rewards (numbers) for meeting different criteria (they like numbers)
				genomes[i][1].fitness += score * 100 # They get 100 for each pipe they pass through
				genomes[i][1].fitness += 0.1  # Small bonus for survival (per frame)
				if genomes[i][1].fitness > FITNESS_THRESH:
					return # If one of them manages to survive 100 pipes its basically good enough to go infinitely so return (neat handles the rest)
				
				bird.draw_visuals(screen, pipe_list) # Draws red lines for where the bird sees (comment out if you don't want to be overwhelmed)

		if remaining == 0: # If they all lose keep the best several, kill the rest off, and breed the survivors (its evolution) (see config for specifics)
			break

		# Move pipes
		for pipe in pipe_list:
			pipe.centerx -= 6 * delta_time * 60  # Adjust for delta_time
		pipe_list = [pipe for pipe in pipe_list if pipe.right > -50]

		draw_pipes(screen, pipe_list, pipe_surface)

		# Move floor
		floor_x_pos -= 6 * delta_time * 60
		if floor_x_pos <= -576:
			floor_x_pos = 0
		draw_floor(screen, floor_surface, floor_x_pos)

		pygame.display.update()
		
if __name__ == "__main__":
	# Set configuration file
	config_path = "config.txt"
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
								neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

	# Create core evolution algorithm class
	p = neat.Population(config)

	# Add reporter for fancy statistical result
	p.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	p.add_reporter(stats)
	

	# Run NEAT
	winner = p.run(game_loop, 2500)
	with open("best_genome.pkl", "wb") as f:
		pickle.dump(winner, f)
	print("Best genome saved as 'best_genome.pkl'") # Saves the best one