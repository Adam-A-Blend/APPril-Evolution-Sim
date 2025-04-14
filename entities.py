import random
import math
import config
from dataclasses import dataclass, field

@dataclass
class BaseEntity:
    x: float
    y: float
    genes: dict

    def can_see(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.hypot(dx, dy)

        if distance > self.genes["vision_distance"]:
            return False

        angle_to_other = math.degrees(math.atan2(dy, dx))
        angle_diff = (angle_to_other - self.direction + 360) % 360
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        return angle_diff <= self.genes["vision_width"] / 2

    def wander(self):
        # Randomly rotate slightly left or right
        rotation = random.uniform(-10, 10)  # degrees
        self.direction = (self.direction + rotation) % 360

        # Move forward in the current direction
        angle_rad = math.radians(self.direction)
        dx = math.cos(angle_rad) * self.genes["speed"]
        dy = math.sin(angle_rad) * self.genes["speed"]

        new_x = self.x + dx
        new_y = self.y + dy

        if new_x < 0 or new_x > 800:
            self.direction = (180 - self.direction) % 360
            dx = -dx

        if new_y < 0 or new_y > 600:
            self.direction = (-self.direction) % 360
            dy = -dy

        self.x = max(0, min(self.x + dx, 800))
        self.y = max(0, min(self.y + dy, 600))

    def steer_away_from(self, neighbors, min_distance=10):
        move_x = 0
        move_y = 0
        count = 0
        for other in neighbors:
            if other is self:
                continue
            dist = math.hypot(self.x - other.x, self.y - other.y)
            if dist < min_distance and dist > 0:
                # Vector pointing away from neighbor
                dx = self.x - other.x
                dy = self.y - other.y
                factor = 1 / dist
                move_x += dx * factor
                move_y += dy * factor
                count += 1

        if count > 0:
            angle = math.atan2(move_y, move_x)
            self.direction = math.degrees(angle)  # Point away

    def move_towards(self, target_x, target_y):
        angle_to_target = math.degrees(math.atan2(target_y - self.y, target_x - self.x))
        angle_diff = (angle_to_target - self.direction + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360

        # Rotate toward target (max 15 degrees per tick)
        rotation_step = max(-15, min(15, angle_diff))
        self.direction = (self.direction + rotation_step) % 360

        # Move forward in the updated direction
        angle_rad = math.radians(self.direction)
        dx = math.cos(angle_rad) * self.genes["speed"]
        dy = math.sin(angle_rad) * self.genes["speed"]

        new_x = self.x + dx
        new_y = self.y + dy

        if new_x < 0 or new_x > 800:
            self.direction = (180 - self.direction) % 360
            dx = -dx

        if new_y < 0 or new_y > 600:
            self.direction = (-self.direction) % 360
            dy = -dy

        self.x = max(0, min(self.x + dx, 800))
        self.y = max(0, min(self.y + dy, 600))



@dataclass
class Predator(BaseEntity):
    hunger: float = 100
    direction: float = field(default_factory=lambda: random.uniform(0, 360))

    def update(self, prey_list, all_predators=None):
        self.hunger -= config.HUNGER_DEPLETION_RATE
        self.just_fed = False
        visible_prey = [p for p in prey_list if self.can_see(p)]

        if all_predators is not None:
            self.steer_away_from(all_predators, min_distance=15)

        if visible_prey:
            closest = min(visible_prey, key=lambda p: math.hypot(self.x - p.x, self.y - p.y))
            self.move_towards(closest.x, closest.y)
        else:
            self.wander()


@dataclass
class Prey(BaseEntity):
    reproduction_timer: float = 100
    direction: float = field(default_factory=lambda: random.uniform(0, 360))

    def update(self, predator_list, all_prey=None):
        self.reproduction_timer -= 1
        reproduced = False

        if all_prey is not None:
            self.steer_away_from(all_prey, min_distance=10)

        visible_predators = [p for p in predator_list if self.can_see(p)]
        
        if visible_predators:
            threat = min(visible_predators, key=lambda p: math.hypot(self.x - p.x, self.y - p.y))
            flee_angle = math.atan2(self.y - threat.y, self.x - threat.x)
            dx = math.cos(flee_angle) * self.genes["speed"]
            dy = math.sin(flee_angle) * self.genes["speed"]
            self.x = max(0, min(self.x + dx, 800))
            self.y = max(0, min(self.y + dy, 600))
            self.direction = math.degrees(flee_angle)
        else:
            self.wander()

        if self.reproduction_timer <= 0:
            reproduced = True

        return reproduced
