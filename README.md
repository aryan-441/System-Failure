# System-Failure
System-Failure is a unique space-shooter game produced for the Haven Pune GameJam. 

It is a 2D arcade game where the player controls a spaceship and has to defeat increasingly difficult waves of enemies. The user is constrained by 5 health points and limited ammunition.

As time progresses, the spaceship encounters a plethora of random malfunctions, including reversed system controls, overheating weapons, or a weakened shield. The player must adapt to these challenges and 'bounce back', trying to achieve the highest possible score.

**FEATURES:**

**1. Random Malfunctions:**

   (I) Reversed Controls: The players' movement binds are reversed in function.
   (II)Recoil: The spaceship experiences recoil after shooting.
   (III) Damaged Thrusters: Movement speed is halved.
   (IV) Shield Malfunction: The player is twice as susceptible to enemy attacks.
   (V) Weapon Overheating: The weapon accumulates heat and temporarily stops working.
   (VI) Engine Stalling: The spaceship's engine stops working temporarily.
   (VII) Targeting Glitch: Bullets deviate from their original trajectory.
   (VIII) Engine Drift: The spaceship drifts arbitrarily.
   (IX) Reactor Instability: Random bursts of energy push the ship off course.

**2. Controls:**

   (I) W A S D / ARROW KEYS: Spaceship movement.
   (II) Left Click: Shooting.
   (III) Mouse: Aiming.
   (IV) R: Restarting the game once over.

**3. Limited Ammunition:**

  The player begins with 16 bullets. They earn a bonus of 4 bullets per kill, and the bullet cap is 24. One bullet is consumed per shot. An additional recovery mechanism prevents the player from becoming inherently defenceless. They are granted 3 extra bullets- just enough to defeat one more enemy, granting them bonus ammo for killing said enemy.

**4. Progressing Enemy Difficulty:**

  The game uses a dynamic enemy spawning system- enemies spawn at different edges of the map and move towards the player's spaceship. The spawn rate of enemies increases linearly as the game goes on. Each enemy can be defeated with 3 shots. A health bar reflects how many shots are required to defeat them. There is a 50% chance that a boss spawns, with a cap of 1 boss per 20 seconds. Unlike regular enemies, a boss has 5 health points. The maximum number of enemies at a given point of time is limited to 9.
   

**5. Player Health**

   The player's spaceship begins with 5 health points. Whenever an enemy collides with the spaceship, the player loses one health point. A short cooldown prevents enemies from inflicting repeated damage every frame.
   However, during a Shield Malfunction, collisions inflict two points of damage instead. When damage occurs, visual effects indicate the impact, including red particles, screen shake and a floating damage indicator displaying the amount of health lost.
   Once the player's health reaches zero, the game ends.

**6. Audio and Visual Effects:**

   A plethora of audio-visual effects have been integrated with this project to create an immersive, arcade-type experience, including the following:

  (I) Continuously scrolling space backgrounds with smooth fading transitions.

  (II) Animated stars creating a sense of depth.
  
  (III) Spaceship sprites for players, enemies and bosses.
  
  (IV) Laser bullets and muzzle flashes.
  
  (V) Enemy hit flashes and explosion particles.
  
  (VI) Smoke effects when weapons overheat.
  
  (VII) Screen shake and floating damage indicators.
  
  (VIII) Animated warnings when system malfunctions occur.
  
  (IX) Arcade sound effects for shooting, collisions, explosions, overheating, system warnings and game over.


***How to Run***

1. Install Python and Pygame.

2. Clone or download this repository.

3. Ensure the required game assets and Python modules are present.

4. Run python main.py from the project directory.

**Install Pygame using:**

pip install pygame

**Technologies Used**

Python — Main programming language

Pygame — Game development, movement, collision detection, graphics and audio

Object-Oriented Programming — Classes for players, enemies, bullets and other game systems

Authored by: Aryan Arora
