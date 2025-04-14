from entities import Predator, Prey
import random
import math
import config

def generate_random_genes():
    speed = random.uniform(*config.GENE_RANGES["speed"])

    vision_width = random.uniform(*config.GENE_RANGES["vision_width"])  # e.g. 40–120 degrees
    width_ratio = (vision_width - config.GENE_RANGES["vision_width"][0]) / (
        config.GENE_RANGES["vision_width"][1] - config.GENE_RANGES["vision_width"][0]
    )

    # Inverse distance: higher width = lower distance
    max_dist = config.GENE_RANGES["vision_distance"][1]
    min_dist = config.GENE_RANGES["vision_distance"][0]
    vision_distance = max_dist - width_ratio * (max_dist - min_dist)

    return {
        "speed": speed,
        "vision_width": vision_width,
        "vision_distance": vision_distance
    }

def mutate_genes(genes):
    new_genes = {}
    for gene, value in genes.items():
        if random.random() < config.MUTATION_RATE:
            delta = value * config.MUTATION_STRENGTH * random.uniform(-1, 1)
            new_value = value + delta

            # Optional: clamp to allowed ranges
            if gene in config.GENE_RANGES:
                min_val, max_val = config.GENE_RANGES[gene]
                new_value = max(min_val, min(max_val, new_value))

            new_genes[gene] = new_value
        else:
            new_genes[gene] = value
    return new_genes


class Simulation:
    def __init__(self):
        self.predators = []
        self.prey = []
        self.init_population()
        self.tick_count = 0
        self.history = []  # Stores (predators, prey)
        self.dead_predators = []
        self.dead_prey = []

    def init_population(self):
        for _ in range(config.INITIAL_PREDATORS):
            self.predators.append(
                Predator(
                    x=random.randint(0, config.WORLD_WIDTH),
                    y=random.randint(0, config.WORLD_HEIGHT),
                    genes=generate_random_genes(),
                )
            )

        for _ in range(config.INITIAL_PREY):
            self.prey.append(
                Prey(
                    x=random.randint(0, config.WORLD_WIDTH),
                    y=random.randint(0, config.WORLD_HEIGHT),
                    genes=generate_random_genes(),
                )
            )

    def update(self):
        prey_to_remove = []
        new_predators = []
        new_prey = []
        
        # Track which prey have been consumed using a list instead of a set
        consumed_prey = []  # List of prey that have been consumed

        for predator in self.predators:
            predator.update(self.prey, all_predators=self.predators)
            for prey in self.prey:
                distance = math.hypot(predator.x - prey.x, predator.y - prey.y)
                if distance < 5:
                    # Only allow one predator to consume each prey
                    if prey not in consumed_prey:
                        prey_to_remove.append(prey)
                        predator.hunger += config.HUNGER_REPLENISHMENT
                        consumed_prey.append(prey)

                        if predator.hunger > 100 and len(self.predators) + len(new_predators) < config.MAX_PREDATORS:
                            predator.hunger = 100
                            new_predators.append(
                                Predator(
                                    x=predator.x,
                                    y=predator.y,
                                    genes=mutate_genes(predator.genes)
                                )
                            )


        for prey in self.prey:
            if prey in prey_to_remove:
                continue

            reproduced = prey.update(self.predators, all_prey=self.prey)
            if reproduced:
                prey_to_remove.append(prey)  # Dies after reproducing

                for _ in range(2):
                    if len(self.prey) + len(new_prey) < config.MAX_PREY:
                        new_prey.append(
                            Prey(
                                x=prey.x,
                                y=prey.y,
                                genes=mutate_genes(prey.genes),
                                reproduction_timer=50
                            )
                        )


        self.dead_prey += [p for p in self.prey if p in prey_to_remove]
        self.prey = [p for p in self.prey if p not in prey_to_remove] + new_prey

        alive_predators = [p for p in self.predators if p.hunger > 0]
        self.dead_predators += [p for p in self.predators if p.hunger <= 0]
        self.predators = alive_predators + new_predators


        self.tick_count += 1

        if self.tick_count % config.STATS_UPDATE_INTERVAL == 0:
            def avg(lst): return sum(lst) / len(lst) if lst else 0

            avg_speed_pred = avg([p.genes["speed"] for p in self.predators])
            avg_speed_prey = avg([p.genes["speed"] for p in self.prey])

            avg_ratio_pred = avg([p.genes["vision_distance"] / p.genes["vision_width"] for p in self.predators])
            avg_ratio_prey = avg([p.genes["vision_distance"] / p.genes["vision_width"] for p in self.prey])

            self.history.append((
                len(self.predators),
                len(self.prey),
                avg_speed_pred,
                avg_speed_prey,
                avg_ratio_pred,
                avg_ratio_prey
            ))

