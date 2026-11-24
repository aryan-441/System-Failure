'''Difficulty Settings'''
DIFFICULTIES = {

    'easy': {
        'starting_enemies': 1,
        'max_enemies': 5,

        'single_interval': 2.30,
        'double_interval': 3.50,
        'spawn_weights': [90, 10],

        'min_single_interval': 1.95,
        'min_double_interval': 3.00,
        'difficulty_increase': 0.05,

        'player_health': 7,
        'starting_ammo': 20,
        'max_ammo': 20,
        'ammo_per_kill': 5,
        'damage_cooldown': 1.5,

        'thruster_multiplier': 0.80,
        'cooling_rate': 14,
    },

    'medium': {
        'starting_enemies': 2,
        'max_enemies': 6,

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
    },

    'hard': {
        'starting_enemies': 2,
        'max_enemies': 8,

        'single_interval': 1.50,
        'double_interval': 2.45,
        'spawn_weights': [83, 17],

        'min_single_interval': 1.10,
        'min_double_interval': 1.85,
        'difficulty_increase': 0.08,

        'player_health': 5,
        'starting_ammo': 16,
        'max_ammo': 16,
        'ammo_per_kill': 4,
        'damage_cooldown': 1.0,

        'thruster_multiplier': 0.65,
        'cooling_rate': 10,
    }
}

DEFAULT_DIFFICULTY = 'medium'
ARCADE_TANK_COOLDOWN = 50
ARCADE_TANK_CHANCE = 0.25

STORY_DIFFICULTIES = {
    'easy': {
        'wave_targets': (3, 5, 5, 5, 6, 5),
        'wave_active_limits': (2, 3, 3, 3, 4, 4),
        'wave_spawn_intervals': (1.35, 1.30, 1.25, 1.20, 1.15, 1.10),
        'opening_rapid_shot_interval': 0.65,
        'survival_boss_health': 12,
        'collector_ammo_per_hp': 2,
        'collector_cockpit_health': 5,
        'collector_interval_multiplier': 1.15,
        'collector_aim_lead': 0.29,
        'survival_spawn_interval_multiplier': 1.35,
        'survival_active_limit_reduction': 2,
    },
    'medium': {
        'wave_targets': (4, 6, 6, 7, 8, 9),
        'wave_active_limits': (3, 3, 4, 4, 5, 6),
        'wave_spawn_intervals': (1.10, 1.00, 0.90, 0.85, 0.80, 0.75),
        'opening_rapid_shot_interval': 0.40,
        'survival_boss_health': 14,
        'collector_ammo_per_hp': 1.65,
        'collector_cockpit_health': 5,
        'collector_interval_multiplier': 1,
        'collector_aim_lead': 0.42,
        'survival_spawn_interval_multiplier': 1.15,
        'survival_active_limit_reduction': 1,
    },
    'hard': {
        'wave_targets': (5, 7, 8, 9, 10, 12),
        'wave_active_limits': (3, 4, 5, 5, 6, 7),
        'wave_spawn_intervals': (0.95, 0.85, 0.75, 0.70, 0.65, 0.60),
        'opening_rapid_shot_interval': 0.25,
        'survival_boss_health': 16,
        'collector_ammo_per_hp': 1.4,
        'collector_cockpit_health': 7,
        'collector_interval_multiplier': 0.87,
        'collector_aim_lead': 0.55,
        'survival_spawn_interval_multiplier': 1.12,
        'survival_active_limit_reduction': 1,
    }
}
