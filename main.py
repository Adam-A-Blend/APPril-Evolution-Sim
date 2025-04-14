import pygame
import math
import config
import time
from simulation import Simulation
import random

class Slider:
    def __init__(self, x, y, w, label, min_val, max_val, start_val, step=1):
        self.rect = pygame.Rect(x, y, w, 20)
        self.label = label
        self.min = min_val
        self.max = max_val
        self.value = start_val
        self.step = step
        self.dragging = False

    def draw(self, surf, font):
        pygame.draw.rect(surf, (100, 100, 100), self.rect)
        pos = int(((self.value - self.min) / (self.max - self.min)) * self.rect.width)
        pygame.draw.rect(surf, (200, 200, 200), (self.rect.x + pos - 2, self.rect.y, 4, self.rect.height))
        label = font.render(f"{self.label}: {self.value:.2f}", True, (255, 255, 255))
        surf.blit(label, (self.rect.x, self.rect.y - 18))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = event.pos[0] - self.rect.x
            pct = max(0, min(1, rel_x / self.rect.width))
            raw = self.min + (self.max - self.min) * pct
            self.value = round(raw / self.step) * self.step


class ToggleButton:
    def __init__(self, x, y, label, state=False):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.label = label
        self.state = state

    def draw(self, surf, font):
        color = (0, 200, 0) if self.state else (80, 80, 80)
        pygame.draw.rect(surf, color, self.rect)
        label = font.render(self.label, True, (255, 255, 255))
        surf.blit(label, (self.rect.x + 30, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.state = not self.state


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.clicked = False

    def draw(self, surf, font):
        color = (50, 120, 200) if not self.clicked else (100, 180, 255)
        pygame.draw.rect(surf, color, self.rect)
        label = font.render(self.text, True, (255, 255, 255))
        surf.blit(label, (self.rect.x + 10, self.rect.y + 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.clicked = True

pygame.init()
screen = pygame.display.set_mode((config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT))
pygame.display.set_caption("Predator-Prey Simulation")
clock = pygame.time.Clock()

# Create a background surface for charts to reduce flickering
chart_surface = pygame.Surface((config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT), pygame.SRCALPHA)
chart_update_counter = 0
CHART_UPDATE_FREQUENCY = 5  # Update charts every 5 frames

font = pygame.font.SysFont(None, 18)

sliders = [
    Slider(220, config.WORLD_HEIGHT + 40, 200, "Initial Predators", 5, 100, 30, step=1),
    Slider(220, config.WORLD_HEIGHT + 80, 200, "Initial Prey", 10, 300, 100, step=1),
    Slider(450, config.WORLD_HEIGHT + 40, 200, "Hunger Depletion / tick", 0.1, 5.0, 1.0, step=0.1),
    Slider(450, config.WORLD_HEIGHT + 80, 200, "Hunger Replenishment / prey", 5, 100, 30, step=1),
    Slider(700, config.WORLD_HEIGHT + 40, 200, "Mutation Rate", 0.0, 1.0, 0.2, step=0.01),
    Slider(700, config.WORLD_HEIGHT + 80, 200, "Mutation Strength", 0.01, 0.5, 0.1, step=0.01),
]

vision_toggle = ToggleButton(950, config.WORLD_HEIGHT + 40, "Show Vision Cones", state=False)
start_button = Button(950, config.WORLD_HEIGHT + 80, 117, 40, "Start Simulation")

simulation_started = False
sim = None
preview_sim = None
last_preview_predators = -1
last_preview_prey = -1
running = True


running = True

while running:
    screen.fill((0, 0, 0))  # Clear screen

    config.SHOW_VISION_CONES = vision_toggle.state
    
    def draw_vision_cone(entity, color):
        if not config.SHOW_VISION_CONES:
            return

        start_angle = math.radians(entity.direction - entity.genes["vision_width"] / 2)
        end_angle = math.radians(entity.direction + entity.genes["vision_width"] / 2)
        radius = entity.genes["vision_distance"]
        center = (int(entity.x + config.CHART_LEFT_WIDTH), int(entity.y))

        points = [center]
        step = math.radians(5)  # Smaller steps = smoother cone
        angle = start_angle
        while angle <= end_angle:
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            points.append((int(x), int(y)))
            angle += step

        pygame.draw.polygon(screen, color, points, width=1)
    
    def draw_population_chart(history):
        chart_width = config.CHART_RIGHT_WIDTH - 40
        chart_height = 100
        chart_x = config.CHART_LEFT_WIDTH + config.WORLD_WIDTH + 20
        chart_y = 20
        spacing = 40  # space between charts
        font = pygame.font.SysFont(None, 16)

        if len(history) < 2:
            return

        def draw_chart(title, index_pred, index_prey, top_y, color_pred, color_prey):
            # Draw background
            pygame.draw.rect(chart_surface, (30, 30, 30), (chart_x, top_y, chart_width, chart_height + 20))

            max_val = max(max(row[index_pred], row[index_prey]) for row in history) + 0.01
            max_ticks = len(history)

            def scale_y(val):
                return chart_height - int((val / max_val) * chart_height)

            def scale_x(i):
                return int((i / max_ticks) * chart_width)

            # Draw lines
            for i in range(1, max_ticks):
                x1 = chart_x + scale_x(i - 1)
                x2 = chart_x + scale_x(i)

                y1_pred = top_y + scale_y(history[i - 1][index_pred])
                y2_pred = top_y + scale_y(history[i][index_pred])
                pygame.draw.line(chart_surface, color_pred, (x1, y1_pred), (x2, y2_pred), 2)

                y1_prey = top_y + scale_y(history[i - 1][index_prey])
                y2_prey = top_y + scale_y(history[i][index_prey])
                pygame.draw.line(chart_surface, color_prey, (x1, y1_prey), (x2, y2_prey), 2)

            # Axes
            pygame.draw.line(chart_surface, (200, 200, 200), (chart_x, top_y), (chart_x, top_y + chart_height), 1)
            pygame.draw.line(chart_surface, (200, 200, 200), (chart_x, top_y + chart_height), (chart_x + chart_width, top_y + chart_height), 1)

            # Title
            label = font.render(title, True, (255, 255, 255))
            chart_surface.blit(label, (chart_x + 10, top_y - 18))

        # Chart 1: Population
        draw_chart("Population", 0, 1, chart_y, (255, 0, 0), (0, 255, 0))

        # Chart 2: Speed
        draw_chart("Average Speed", 2, 3, chart_y + chart_height + spacing, (255, 0, 0), (0, 255, 0))

        # Chart 3: Vision Ratio (distance / width)
        draw_chart("Vision Distance:Width Ratio", 4, 5, chart_y + 2 * (chart_height + spacing), (255, 0, 0), (0, 255, 0))

    def draw_survival_chart(entity_live, entity_dead, gene_fn, chart_title, top_y, color):
        global sim
        chart_x = 20
        chart_width = config.CHART_LEFT_WIDTH - 40
        chart_height = 100
        bin_count = 20
        font = pygame.font.SysFont(None, 16)

        # Draw background
        pygame.draw.rect(chart_surface, (30, 30, 30), (chart_x, top_y, chart_width, chart_height + 30))

        # Build histograms
        def make_hist(data):
            if not data:
                return [0] * bin_count, 0, 1
            values = [gene_fn(e) for e in data]
            min_val, max_val = min(values), max(values)
            bins = [0] * bin_count
            for val in values:
                idx = int((val - min_val) / (max_val - min_val + 1e-6) * (bin_count - 1))
                bins[idx] += 1
            return bins, min_val, max_val

        live_bins, min_val, max_val = make_hist(entity_live)
        dead_bins, _, _ = make_hist(entity_dead)
        total_bins = [live + dead for live, dead in zip(live_bins, dead_bins)]

        bin_width = chart_width // bin_count
        for i in range(bin_count):
            total = total_bins[i]
            survival = live_bins[i] / total if total > 0 else 0
            bar_height = int(survival * chart_height)

            # Draw bar
            x = chart_x + i * bin_width
            y = top_y + chart_height - bar_height
            pygame.draw.rect(chart_surface, color, (x, y, bin_width - 1, bar_height))

        # Axis line and title
        pygame.draw.line(chart_surface, (200, 200, 200), (chart_x, top_y + chart_height), (chart_x + chart_width, top_y + chart_height), 1)
        title = font.render(chart_title, True, (255, 255, 255))
        chart_surface.blit(title, (chart_x + 10, top_y - 18))
    
        if not simulation_started:
            current_pred = int(sliders[0].value)
            current_prey = int(sliders[1].value)
            if sim is None or current_pred != last_preview_predators or current_prey != last_preview_prey:
                last_preview_predators = current_pred
                last_preview_prey = current_prey
                sim = Simulation()
                sim.predators = [
                    Predator(
                        x=random.randint(0, config.WORLD_WIDTH),
                        y=random.randint(0, config.WORLD_HEIGHT),
                        genes=generate_random_genes(),
                    ) for _ in range(current_pred)
                ]
                sim.prey = [
                    Prey(
                        x=random.randint(0, config.WORLD_WIDTH),
                        y=random.randint(0, config.WORLD_HEIGHT),
                        genes=generate_random_genes(),
                    ) for _ in range(current_prey)
                ]
                
                sim.dead_predators = []
                sim.dead_prey = []
                sim.history = [(len(sim.predators), len(sim.prey), 0, 0, 0, 0)]
                
                # Draw charts for preview
                chart_surface.fill((0, 0, 0, 0))
                draw_population_chart(sim.history)
                draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["speed"], "Predator Speed Survival", top_y=20, color=(255, 0, 0))
                draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["speed"], "Prey Speed Survival", top_y=160, color=(0, 255, 0))
                draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Predator Vision Ratio Survival", top_y=300, color=(255, 0, 0))
                draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Prey Vision Ratio Survival", top_y=440, color=(0, 255, 0))

    if sim is not None:
        for predator in sim.predators:
            pygame.draw.circle(screen, (255, 0, 0), (int(predator.x + config.CHART_LEFT_WIDTH), int(predator.y)), 5)
            draw_vision_cone(predator, (255, 0, 0))
        for prey in sim.prey:
            pygame.draw.circle(screen, (0, 255, 0), (int(prey.x + config.CHART_LEFT_WIDTH), int(prey.y)), 4)
            draw_vision_cone(prey, (0, 255, 0))

        # Draw charts on the chart surface (not directly on screen)
        if simulation_started and chart_update_counter >= CHART_UPDATE_FREQUENCY:
            # Clear the chart surface
            chart_surface.fill((0, 0, 0, 0))
            # Draw charts on the chart surface
            draw_population_chart(sim.history)
            draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["speed"], "Predator Speed Survival", top_y=20, color=(255, 0, 0))
            draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["speed"], "Prey Speed Survival", top_y=160, color=(0, 255, 0))
            draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Predator Vision Ratio Survival", top_y=300, color=(255, 0, 0))
            draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Prey Vision Ratio Survival", top_y=440, color=(0, 255, 0))
        
        # Always blit the chart surface onto the main screen
        screen.blit(chart_surface, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not simulation_started:
            for slider in sliders:
                slider.handle_event(event)
            vision_toggle.handle_event(event)
            start_button.handle_event(event)

    if start_button.clicked and not simulation_started:
        config.INITIAL_PREDATORS = int(sliders[0].value)
        config.INITIAL_PREY = int(sliders[1].value)
        config.HUNGER_DEPLETION_RATE = sliders[2].value
        config.HUNGER_REPLENISHMENT = sliders[3].value
        config.MUTATION_RATE = sliders[4].value
        config.MUTATION_STRENGTH = sliders[5].value
        config.SHOW_VISION_CONES = vision_toggle.state

        sim = Simulation()
        simulation_started = True
        
        # Draw charts initially
        chart_surface.fill((0, 0, 0, 0))
        draw_population_chart(sim.history)
        draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["speed"], "Predator Speed Survival", top_y=20, color=(255, 0, 0))
        draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["speed"], "Prey Speed Survival", top_y=160, color=(0, 255, 0))
        draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Predator Vision Ratio Survival", top_y=300, color=(255, 0, 0))
        draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Prey Vision Ratio Survival", top_y=440, color=(0, 255, 0))

    if simulation_started:
        sim.update()
        # Update charts less frequently to reduce flickering
        chart_update_counter += 1
        if chart_update_counter >= CHART_UPDATE_FREQUENCY:
            chart_update_counter = 0
            # Clear the chart surface
            chart_surface.fill((0, 0, 0, 0))
            # Draw charts on the chart surface
            draw_population_chart(sim.history)
            draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["speed"], "Predator Speed Survival", top_y=20, color=(255, 0, 0))
            draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["speed"], "Prey Speed Survival", top_y=160, color=(0, 255, 0))
            draw_survival_chart(sim.predators, sim.dead_predators, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Predator Vision Ratio Survival", top_y=300, color=(255, 0, 0))
            draw_survival_chart(sim.prey, sim.dead_prey, lambda e: e.genes["vision_distance"] / e.genes["vision_width"], "Prey Vision Ratio Survival", top_y=440, color=(0, 255, 0))

    # Always draw UI at bottom
    for slider in sliders:
        slider.draw(screen, font)
    vision_toggle.draw(screen, font)
    start_button.draw(screen, font)

    pygame.display.flip()
    time.sleep(config.TICK_DURATION)

pygame.quit()