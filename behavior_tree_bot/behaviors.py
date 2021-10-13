import sys
sys.path.insert(0, '../')
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

# From defensive_bot.py
def defend(state):
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
def attack_nearest_target(state):
    my_planets = [planet for planet in state.my_planets()] # getting one of my planets
    distance = inf # Set a distance for compare
    nearest_target = None
    for target in state.neutral_planets():
        target_distance = state.distance(my_planets.ID, target.ID)
        if target_distance < distance:
            # attack it.
            shipWeNeed = target.num_ships + 1;
            if my_planets.num_ships > shipWeNeed:
                distance = target_distance
                nearest_target = target
    if not nearest_target:
        return False
    else:
        return issue_order(state, my_planets.ID, nearest_target.ID, shipWeNeed)

