'''Difficulty Settings'''
DIFFICULTIES = {

    'easy': {
        'starting_enemies': 1,
        'max_enemies': 6,

        'single_interval': 2.3,
        'double_interval': 3.5,
        'spawn_weights': [90, 10],

        'min_single_interval': 1.9,
        'min_double_interval': 2.9,
        'difficulty_increase': 0.05,

        'player_health': 7,
        'starting_ammo': 20,
        'max_ammo': 20,
        'ammo_per_kill': 5,
        'damage_cooldown': 1.5,

        'thruster_multiplier': 0.80,
        'cooling_rate': 14,

        'tank_cooldown': 60,
        'tank_chance': 0.20
    },

    'medium': {
        'starting_enemies': 2,
        'max_enemies': 7,

        'single_interval': 2.0,
        'double_interval': 3.2,
        'spawn_weights': [85, 15],

        'min_single_interval': 1.6,
        'min_double_interval': 2.6,
        'difficulty_increase': 0.05,

        'player_health': 6,
        'starting_ammo': 18,
        'max_ammo': 18,
        'ammo_per_kill': 4,
        'damage_cooldown': 1.2,

        'thruster_multiplier': 0.70,
        'cooling_rate': 12,

        'tank_cooldown': 50,
        'tank_chance': 0.25
    },

    'hard': {
        'starting_enemies': 3,
        'max_enemies': 8,

        'single_interval': 1.8,
        'double_interval': 3.0,
        'spawn_weights': [85, 15],

        'min_single_interval': 1.4,
        'min_double_interval': 2.4,
        'difficulty_increase': 0.05,

        'player_health': 5,
        'starting_ammo': 16,
        'max_ammo': 16,
        'ammo_per_kill': 4,
        'damage_cooldown': 1.0,

        'thruster_multiplier': 0.65,
        'cooling_rate': 10,

        'tank_cooldown': 40,
        'tank_chance': 0.30
    }
}

DEFAULT_DIFFICULTY = 'medium'
