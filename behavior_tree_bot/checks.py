import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)


# check if the planet is being attacked without reinforcement
def if_been_attacked_without_reinforcement(state):
    enemy_targets = [fleet.destination_planet for fleet in state.enemy_fleets()]
    if not enemy_targets:
        return False

    def strength(p):
        return p.num_ships \
               + sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == p.ID) \
               - sum(fleet.num_ships for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID)

    for p in state.my_planets():
        # check if enemy targeted this planet
        if p.ID in enemy_targets:
            # check if can survive attack
            if strength(p) <= 0:
                return True

    return False


def if_possible_victory(state):
    attack_unit = max(state.my_planets(), key=lambda x: x.num_ships, default=None)
    enemy_weakest = min(state.enemy_planets(), key=lambda x: x.num_ships, default=None)

    if attack_unit == None or enemy_weakest == None:
        return False
    
    return attack_unit.num_ships > enemy_weakest.num_ships


def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def if_enemy_planet_available(state):
    return any(state.enemy_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())