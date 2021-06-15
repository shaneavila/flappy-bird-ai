import pygame
import os
import random
import neat
import itertools

FPS = 15
VELOCITY = 5
WINDOW_WIDTH = 288
WINDOW_HEIGHT = 512
IMAGES, HITMASKS = {}, {}

# Image paths
BACKGROUND_PATH = os.path.join('assets', 'background.png')
BASE_PATH = os.path.join('assets', 'base.png')
BIRD_PATHS = (
    os.path.join('assets', 'bird-up.png'),
    os.path.join('assets', 'bird-mid.png'),
    os.path.join('assets', 'bird-down.png')
)
PIPE_PATH = os.path.join('assets', 'pipe.png')

# Load images into dictionary
IMAGES['background'] = pygame.image.load(BACKGROUND_PATH)
IMAGES['base'] = pygame.image.load(BASE_PATH)
IMAGES['bird'] = (
    pygame.image.load(BIRD_PATHS[0]),
    pygame.image.load(BIRD_PATHS[1]),
    pygame.image.load(BIRD_PATHS[2]),
)
IMAGES['pipe'] = (
    pygame.transform.flip(pygame.image.load(PIPE_PATH), False, True),
    pygame.image.load(PIPE_PATH),
)


class Base:
    """Represents the floor image

    Attributes
    ----------
    WIDTH : int
        The pixel width of the bird's image

    Methods
    -------
    move()
        Moves adjacent floor images left
    draw()
        Draws floor to screen
    """
    WIDTH = IMAGES['base'].get_width()

    def __init__(self, y):
        """
        Parameters
        ----------
        y : int
            Vertical position of the floor

        Attributes
        ----------
        x1 : int
            The position of the first floor image
        x2 : int
            The position of the second floor image
        """
        self.y = y

        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        # move images to the left
        self.x1 -= VELOCITY
        self.x2 -= VELOCITY
        # once the image leaves the screen move image to
        # the right of the other floor image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self):
        WINDOW.blit(IMAGES['base'], (self.x1, self.y))
        WINDOW.blit(IMAGES['base'], (self.x2, self.y))


class Bird:
    """Represents the bird controlled by the output neuron

    Attributes
    ----------
    MAX_ROTATION : int
        The max degrees of rotation for the bird's image
    ROT_VEL : int
        The speed of rotation for the bird's image
    HEIGHT : int
        The pixel height of the bird's image

    Methods
    -------
    flap()
        Moves the bird upward to keep it from falling
    move()
        Moves the bird up/down and rotates the bird
    draw()
        Animates the bird and draws bird to screen
    """
    MAX_ROTATION = 25
    ROT_VEL = 20
    HEIGHT = IMAGES['bird'][0].get_height()

    def __init__(self, x, y):
        """
        Parameters
        ----------
        x : int
            Horizontal position of the bird
        y : int
            Vertical position of the bird

        Attributes
        ----------
        height : int
            The height of the bird
        img : Surface
            The current bird image
        tick_count : int
            The amount of time passed since last jump
        tilt : int
            The rotation of the bird's image
        vel : int
            The speed the bird flaps or falls
        """
        self.x = x
        self.y = y

        self.height = y
        self.img = IMAGES['bird'][0]
        self.tick_count = 0
        self.tilt = 0
        self.vel = 0

    def flap(self):
        self.height = self.y
        self.tick_count = 0
        self.vel = -5.5

    def move(self):
        self.tick_count += 1
        # vertical displacement
        displacement = self.vel * self.tick_count + 0.5 * 4 * self.tick_count ** 2
        # prevents bird from falling too quickly
        if displacement >= 24:
            displacement = 24
        # gives flap movement more bounce
        if displacement < 0:
            displacement -= 12
        # moves up or down
        self.y += displacement
        # tilt upwards for upward displacement
        if displacement < 0 or self.y < self.height + 25:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        # tilt downwards while falling
        else:
            if self.tilt >= -70:
                self.tilt -= self.ROT_VEL

    def draw(self):
        # animate the bird by cycling through flap images
        self.img = IMAGES['bird'][NEXT_FRAME]
        # if falling set the picture to the mid-flap image
        if self.tilt <= -80:
            self.img = IMAGES['bird'][1]
        # rotate image around its center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(round(self.x), round(self.y))).center)
        WINDOW.blit(rotated_image, new_rect.topleft)


class Pipe:
    """Represents the pipe image

    Attributes
    ----------
    SPACE : int
        The space in pixels between the pipes
    WIDTH : int
        The pixel width of the pipe's image

    Methods
    -------
    move()
        Moves pipe images left
    draw()
        Draws pipes to screen
    set_height()
        Sets height of upper and lower pipe with space between them
    """
    SPACE = 100
    WIDTH = IMAGES['pipe'][0].get_width()

    def __init__(self, x):
        """
        Parameters
        ----------
        x : int
            Horizontal position of the pipe

        Attributes
        ----------
        height : int
            The random height to place pipes
        lower : int
            The height of the lower pipe
        upper : int
            The height of the upper pipe
        passed : Bool
            The condition based on if the pipe has passed the bird
        """
        self.x = x

        self.height = 0
        self.lower = 0
        self.upper = 0

        self.passed = False

        self.set_height()

    def draw(self):
        WINDOW.blit(IMAGES['pipe'][0], (self.x, self.upper))
        WINDOW.blit(IMAGES['pipe'][1], (self.x, self.lower))

    def move(self):
        self.x -= VELOCITY

    def set_height(self):
        self.height = random.randrange(50, 320)
        self.lower = self.height + self.SPACE
        self.upper = self.height - IMAGES['pipe'][0].get_height()


def collide(pipe, bird):
    """Determines collision between pipe and bird using hitmasks

    Parameters
    ----------
    pipe : Pipe
        Pipe object
    bird : Bird
        Bird object

    Returns
    -------
    bool
        True if collision, False otherwise.
    """
    bird_mask = HITMASKS['bird'][NEXT_FRAME]
    upper_mask = HITMASKS['pipe'][0]
    lower_mask = HITMASKS['pipe'][1]

    upper_offset = (pipe.x - bird.x, pipe.upper - round(bird.y))
    lower_offset = (pipe.x - bird.x, pipe.lower - round(bird.y))

    lower_collision = bird_mask.overlap(lower_mask, lower_offset)
    upper_collision = bird_mask.overlap(upper_mask, upper_offset)

    if upper_collision or lower_collision:
        return True

    return False


def distribute_frames():
    """Distributes frames for use amongst 4 images based on FPS

    Parameters
    ----------
    pipe : Pipe
        Pipe object
    bird : Bird
        Bird object

    Returns
    -------
    itertools.cycle
        List of indices for bird animation
    """
    # round-robin distribute frames into 4 ~equal parts
    frames = [x % 4 for x in range(FPS)]
    frames.sort()
    # replace 3's with 1's to allow for smooth image cycle
    return itertools.cycle([1 if n == 3 else n for n in frames])


def draw_window(birds, pipes, base, score):
    """Draws all images and text to the screen

    Parameters
    ----------
    pipe : Pipe
        Pipe object
    bird : Bird
        Bird object
    base : Base
        Base object
    score : int
        Number of pipes bird has successfully passed

    """
    WINDOW.blit(IMAGES['background'], (0, 0))
    for pipe in pipes:
        pipe.draw()
    base.draw()
    for bird in birds:
        bird.draw()
    stats = FONT.render("Score: " + str(score), 1, (255, 255, 255))
    WINDOW.blit(stats, (WINDOW_WIDTH - stats.get_width() - 15, 10))
    pygame.display.update()


def get_mask(img):
    """Provides a hitmask for an image for use in collision

    Parameters
    ----------
    img : Surface
        Image to base mask on

    Returns
    -------
    Mask
        Mask of the image
    """
    return pygame.mask.from_surface(img)


def fitness(genome_tuples, config):
    """Sets each bird's fitness in the population based on distance

    Parameters
    ----------
    genome_tuples : list
        List of genome tuples
    config : Config
        Config object

    """
    global WINDOW, CLOCK, FONT, FRAMES, NEXT_FRAME
    pygame.init()
    WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Flappy Bird AI')
    FONT = pygame.font.SysFont('agencyfb', 25)
    CLOCK = pygame.time.Clock()
    FRAMES = distribute_frames()
    floor = 475
    ceiling = 50

    HITMASKS['bird'] = (
        get_mask(IMAGES['bird'][0]),
        get_mask(IMAGES['bird'][1]),
        get_mask(IMAGES['bird'][2]),
    )
    HITMASKS['pipe'] = (
        get_mask(IMAGES['pipe'][0]),
        get_mask(IMAGES['pipe'][1]),
    )

    neural_nets = []
    genomes = []
    birds = []
    # Set fitness to 0 and split genome object into separate lists
    for _, genome in genome_tuples:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        neural_nets.append(net)
        birds.append(Bird(144, 256))
        genomes.append(genome)

    base = Base(floor)
    pipes = [Pipe(350)]
    score = 0

    while True and len(birds) > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                break

        # select pipe to base neural net input
        sel_pipe = 0
        if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].WIDTH:
            sel_pipe = 1
        # increase fitness based on how far bird gets
        for bird in birds:
            genomes[birds.index(bird)].fitness += 0.1
            bird.move()
            # output neuron makes decision to flap based on input
            output = neural_nets[birds.index(bird)].activate(
                (
                 bird.y,
                 abs(bird.y - pipes[sel_pipe].height),
                 abs(bird.y - pipes[sel_pipe].lower)
                 )
            )
            # tanh activation function determines to flap or not
            if output[0] > 0.5:
                bird.flap()

        base.move()
        # next frame in bird animation
        NEXT_FRAME = next(FRAMES)
        for pipe in pipes:
            pipe.move()
            for bird in birds:
                # Decrease fitness of birds that hit pipe to discourage behavior
                if collide(pipe, bird):
                    genomes[birds.index(bird)].fitness -= 1
                    neural_nets.pop(birds.index(bird))
                    genomes.pop(birds.index(bird))
                    birds.pop(birds.index(bird))
                # Don't consider birds that hit floor or ceiling
                if bird.y >= floor - bird.HEIGHT or bird.y < ceiling:
                    neural_nets.pop(birds.index(bird))
                    genomes.pop(birds.index(bird))
                    birds.pop(birds.index(bird))
                # Once bird passes pipe change boolean, add new pipe, & increase score
                if pipes[0].x < bird.x and not pipes[0].passed:
                    pipes[0].passed = True  # limits pipe creation to 1
                    pipes.append(Pipe(350))
                    score += 1
        # removes pipe once it leaves the screen
        if pipes[0].x < -pipes[0].WIDTH:
            pipes.pop(0)
        draw_window(birds, pipes, base, score)
        CLOCK.tick(FPS)


# run the fitness function only if this module is executed as the main script
# (if this module is imported then nothing is executed)
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    # Load configuration
    load_config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                     config_path)
    # Create the population
    population = neat.Population(load_config)
    # Add a stdout reporter to show progress in the terminal
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())
    # Run for up to 50 generations
    winner = population.run(fitness, 50)
    # Display the winning genome
    print('\nBest genome:\n{!s}'.format(winner))
