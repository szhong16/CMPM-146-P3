import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)


# check if the planet is being attacked without reinforcement
def if_been_attacked_without_reinforcement(state):
    enemy_targets = [fleet.destination_planet for fleet in state.enemy_fleets()]
    
    logging.debug('Compare Attacks') 
    logging.debug(state.my_planets()) 
    logging.debug(enemy_targets) 

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


def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())
