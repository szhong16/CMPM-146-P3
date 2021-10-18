import sys
sys.path.insert(0, '../')

import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)

from planet_wars import issue_order
from math import inf


def attack_weakest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_weakest_neutral_planet(state):
    # (1) If we currently have a fleet in flight, just do nothing.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)

# attack from aggressive_bot.py
def attack(state):
    my_planets = iter(sorted(state.my_planets(), key=lambda p: p.num_ships))

    enemy_planets = [planet for planet in state.enemy_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
    enemy_planets.sort(key=lambda p: p.num_ships)

    target_planets = iter(enemy_planets)

    try:
        my_planet = next(my_planets)
        target_planet = next(target_planets)
        while True:
            required_ships = target_planet.num_ships + \
                                 state.distance(my_planet.ID, target_planet.ID) * target_planet.growth_rate + 1

            if my_planet.num_ships > required_ships:
                issue_order(state, my_planet.ID, target_planet.ID, required_ships)
                my_planet = next(my_planets)
                target_planet = next(target_planets)
            else:
                my_planet = next(my_planets)

    except StopIteration:
        return

# spread from aggressive_bot.py
def spread(state):
    my_planets = iter(sorted(state.my_planets(), key=lambda p: p.num_ships))

    neutral_planets = [planet for planet in state.neutral_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
    neutral_planets.sort(key=lambda p: p.num_ships)

    target_planets = iter(neutral_planets)

    try:
        my_planet = next(my_planets)
        target_planet = next(target_planets)
        while True:
            required_ships = target_planet.num_ships + 1

            if my_planet.num_ships > required_ships:
                issue_order(state, my_planet.ID, target_planet.ID, required_ships)
                my_planet = next(my_planets)
                target_planet = next(target_planets)
            else:
                my_planet = next(my_planets)

    except StopIteration:
        return

# defend our planets from incoming attacks
def defend_incoming_attacks(state):
    # helper functions
    # calculate the current strength of planet (account for growth rate)
    def strength(p):
        return p.num_ships \
               + sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == p.ID) \
               - sum(fleet.num_ships for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID) \
               + min(fleet.turns_remaining  for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID) * p.growth_rate
                   
    def distance(p):
        return state.distance(p.ID, protect_planet.ID)

    enemy_targets = [fleet.destination_planet for fleet in state.enemy_fleets()]
    
    # find the planets that are been attacked
    # [WIP] find the priority planet to protect
    protect_planets = []
    for planet in state.my_planets():
        if planet.ID in enemy_targets:
            # check if can survive attack
            if strength(planet) <= 0:
                protect_planets.append(planet)

    if not protect_planets:
        return False

    protect_planet = min(protect_planets, key=strength)
    enemy_incoming = max((fleet for fleet in state.enemy_fleets() if fleet.destination_planet == protect_planet.ID), key=lambda x: x.num_ships)

    # sort our planets with distance to current planet
    combat_units = state.my_planets()
    combat_units.remove(protect_planet)
    combat_units = iter(sorted(combat_units, key=distance))

    try:
        unit = next(combat_units)
        
        while True:
            # calculate how many ship needed for reinforcement
            ships_required = 1 - strength(protect_planet)
            if ships_required <= 0:
                return False

            # so if there're need to defense, find the planet to send defense
            if unit.num_ships > ships_required:
                return issue_order(state, unit.ID, protect_planet.ID, ships_required)
            else:
                unit = next(combat_units)

    except StopIteration:
        return False



# From defensive_bot.py
def defensive_defend(state):
    my_planets = [planet for planet in state.my_planets()]
    if not my_planets:
        return

    def strength(p):
        return p.num_ships \
               + sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == p.ID) \
               - sum(fleet.num_ships for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID)

    avg = sum(strength(planet) for planet in my_planets) / len(my_planets)

    weak_planets = [planet for planet in my_planets if strength(planet) < avg]
    strong_planets = [planet for planet in my_planets if strength(planet) > avg]

    if (not weak_planets) or (not strong_planets):
        return

    weak_planets = iter(sorted(weak_planets, key=strength))
    strong_planets = iter(sorted(strong_planets, key=strength, reverse=True))

    try:
        weak_planet = next(weak_planets)
        strong_planet = next(strong_planets)
        while True:
            need = int(avg - strength(weak_planet))
            have = int(strength(strong_planet) - avg)

            if have >= need > 0:
                issue_order(state, strong_planet.ID, weak_planet.ID, need)
                weak_planet = next(weak_planets)
            elif have > 0:
                issue_order(state, strong_planet.ID, weak_planet.ID, have)
                strong_planet = next(strong_planets)
            else:
                strong_planet = next(strong_planets)

    except StopIteration:
        return

# From production_bot.py
def production(state):
    my_planets = iter(sorted(state.my_planets(), key=lambda p: p.num_ships, reverse=True))

    target_planets = [planet for planet in state.not_my_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
    target_planets = iter(sorted(target_planets, key=lambda p: p.num_ships, reverse=True))

    try:
        my_planet = next(my_planets)
        target_planet = next(target_planets)
        while True:
            if target_planet.owner == 0:
                required_ships = target_planet.num_ships + 1
            else:
                required_ships = target_planet.num_ships + \
                                 state.distance(my_planet.ID, target_planet.ID) * target_planet.growth_rate + 1

            if my_planet.num_ships > required_ships:
                issue_order(state, my_planet.ID, target_planet.ID, required_ships)
                my_planet = next(my_planets)
                target_planet = next(target_planets)
            else:
                target_planet = next(target_planets)

    except StopIteration:
        return

# Find the nearest one
def attack_nearest_neutral(state):
    enemy_targets = [fleet.destination_planet for fleet in state.enemy_fleets()]

    # calculate the strength of neutral planet
    def neutral_strength(p):
        return -p.num_ships \
               + sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == p.ID) \
               - sum(fleet.num_ships for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID)

    neutral_planets = [p for p in state.neutral_planets() if neutral_strength(p) <= 0]
    if not neutral_planets:
        return False

    neutral_planets = sorted(neutral_planets, key=neutral_strength)

    check = 0
    for my_planet in state.my_planets():

        # make sure current planet is not under attack
        if my_planet.ID in enemy_targets:
            continue

        # for every planet find the nearest neutral which can be taken [find one]
        distance = inf # Set a distance for compare
        nearest_target = None
        for target in neutral_planets:
            target_distance = state.distance(my_planet.ID, target.ID)
            if target_distance < distance:
                # attack it.
                shipWeNeed = target.num_ships + 1
                if my_planet.num_ships > shipWeNeed:
                    distance = target_distance
                    nearest_target = target

        if nearest_target:
            check += 1
            issue_order(state, my_planet.ID, nearest_target.ID, shipWeNeed)

    if check is not 0:
        return True
    else:
        return False


# Find the nearest and cheapest neutral planet
def attack_cheapest_neutral(state):

    def strength(p):
        return p.num_ships \
               + sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == p.ID) \
               - sum(fleet.num_ships for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID)

    # calculate the strength of neutral planet
    def neutral_strength(p):
        return p.num_ships \
               - sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == p.ID) \
               + sum(fleet.num_ships for fleet in state.enemy_fleets() if fleet.destination_planet == p.ID)
    
    neutral_planets = [p for p in state.neutral_planets() if neutral_strength(p) > 0]
    if not neutral_planets:
        return False

    # sort our planets with power
    enemy_targets = [fleet.destination_planet for fleet in state.enemy_fleets()]
    combat_units = [p for p in state.my_planets() if p.ID not in enemy_targets]
    if not combat_units:
        return False

    combat_unit = max(combat_units, key=strength)
    
    # sort by both cost and distance
    target_planet = min(neutral_planets, key=lambda x: (neutral_strength(x) * state.distance(combat_unit.ID, x.ID)))

    # find cost
    ships_required = neutral_strength(target_planet) + 1

    # send ships
    if combat_unit.num_ships > ships_required:
        return issue_order(state, combat_unit.ID, target_planet.ID, ships_required)
    else:
        return False
