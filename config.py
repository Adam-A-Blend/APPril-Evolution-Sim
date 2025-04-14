# World Dimensions
WORLD_HEIGHT = 600
UI_PANEL_HEIGHT = 150
WORLD_WIDTH = 800
CHART_LEFT_WIDTH = 250
CHART_RIGHT_WIDTH = 250

DISPLAY_WIDTH = WORLD_WIDTH + CHART_LEFT_WIDTH + CHART_RIGHT_WIDTH
DISPLAY_HEIGHT = WORLD_HEIGHT + UI_PANEL_HEIGHT

# Population
INITIAL_PREDATORS = 30
INITIAL_PREY = 100
MAX_PREDATORS = 1500    # 25000 is set arbitrarily high
MAX_PREY = 25000        # 25000 is set arbitrarily high
TICK_DURATION = 0.05    # seconds

# Entity & Gene Characteristics
HUNGER_DEPLETION_RATE = 1   # How much predator hunger is depleted per tick
HUNGER_REPLENISHMENT = 30   # How much of a predators hunger is replenished after eating
MUTATION_RATE = 0.2         # Chance of mutation when reproducing
MUTATION_STRENGTH = 0.1     # +/- % change from current gene value
GENE_RANGES = {
    "speed": (1.0, 3.0),              # min, max
    "vision_distance": (20, 400),
    "vision_width": (40, 360)
}

# Visualizations
SHOW_VISION_CONES = False
STATS_UPDATE_INTERVAL = 10  # Update chart every 20 ticks
MAX_DATA_POINTS = 200       # How many past ticks to show in chart
