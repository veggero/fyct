from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set, Optional
from random import choice, shuffle, random, choices
from collections import Counter
from copy import copy
from itertools import combinations

from characters import Character
from map import Place, Exit
from gram import Telegram
from words import EventMessages

@dataclass
class World:
	
	weathers: Set[Weather]
	day_times: Set[DayTime]
	
	template_places: Set[Place]
	time: int = 0
	places: Set[Place] = field(default_factory=set)
	world_size: int = 10
	
	changeWeatherChance = 1 / 14400
	duringWeatherChance = 1 / 1200
	maxSize = 200
	
	weather: Weather = None
	day_time: DayTime = None
	turn: Optional[Player] = None
	
	def __post_init__(self):
		self.weather = choice([*self.weathers])
		self.day_time = choice([*self.day_times])
		self.generate_map(self.world_size)
	
	@property
	def hour(self) -> int: return (self.time % 60*24) / 60
	
	@property
	def modifier(self) -> Modifier:
		return self.weather.modifier + self.dayTime.modifier
	
	def tick(self):
		for character in Character.instances:
			character.look_around()
		while 1:
			shuffle(Character.instances)
			if (ppl := [c for c in Character.instances if c.state.can_act]):
				character = min(ppl, key=lambda c: (c.busy_until, -c.agility))
				if character.busy_until < self.time:
					character.busy_until = self.time
				self.events(character.busy_until - self.time)
				elapsed = character.busy_until - self.time
				
				self.turn = character
				Telegram.instance.tick()
				character.tick()
				while self.turn is character: pass
			elif Character.instances:
				elapsed = 3
			else:
				return print('THE END') #all dead
			self.time += elapsed
			for character in Character.instances:
				character.work_for(elapsed)
			Telegram.instance.tick()
	
	def events(self, time_delta):
		for i in range(int(time_delta*10)): #this sucks
			if random() <= self.changeWeatherChance:
				for char in Character.instances:
					char.send_event(self.weather.end_event)
				before = {c: c.place.objects_around(c.visibility) for c in Character.instances}
				self.weather = choice([*(self.weathers - {self.weather})])
				for char in Character.instances:
					char.send_event(self.weather.start_event)
					char.send_visibility_event(self.weather.visibility_event, before)
			elif random() <= self.duringWeatherChance:
				for char in Character.instances:
					char.send_event(self.weather.during_event)
		for day_time in self.day_times:
			if int(self.hour) in day_time.range and day_time is not self.day_time:
				before = {c: c.place.objects_around(c.visibility) for c in Character.instances}
				self.day_time = day_time
				for char in Character.instances:
					char.send_event(self.day_time.start_event)
					char.send_visibility_event(self.weather.visibility_event, before)
	
	def spawn(self, character: Character, place: Optional[Place]=None):
		place = place or choice([*self.places])
		place.contained.add(character)
		character.place = place
		character.world = self
	
	def generate_map(self, n):
		# Tries to generate the map for a maximum
		# of 2n times (2n is random)
		for gen_number in range(2*n):
			# Prepares templates
			templates = choices([*self.template_places], weights=[t["chances"] for t in self.template_places.values()], k=n)

			# Saves each place generated
			places_categories = Counter()
			places = []
			for category_name in templates:
				category = self.template_places[category_name].copy()
				places_categories[category_name] += 1

				# Chooses a variant
				variants = list(category["variants"]) + ["classic"]
				weights = [1] * len(variants) + [len(variants)]
				variant = choices(variants + ["classic"], weights=weights, k=1)[0]

				# Selects news descriptions, objects, attacks, actions and defences
				# if a variant has been choosen
				if variant != "classic":
					category.update(category["variants"][variant])

				# Creates the place
				place = Place(tag=f"{category_name} #{places_categories[category_name]}",
						category=category_name,
						variant=variant,
						description=choice(category["descriptions"]),
						exits=set())

				# Adds contained, actions, attacks and defences if there are any
				for field in ("contained", "actions", "attacks", "defences"):
					if value := category.get(field):
						place.__setattr__(field, value)

				# Saves the place
				places.append(place)

			# Creates random commbinations between places
			exits = list(combinations(places, 2))
			shuffle(exits)

			# Trashes the invalid ones
			for a, b in exits:
				# Ensures that the two categories are compatible
				if not b.category in self.template_places[a.category]["exits"]:
					continue
				elif not a.category in self.template_places[b.category]["exits"]:
					continue
				elif any([e.tag == b.tag for e in a.exits]):
					continue

				# Creates the exits
				a.exits.add(Exit(tag=b.tag, description=choice(self.template_places[a.category]["exits"][b.category])))
				b.exits.add(Exit(tag=a.tag, description=choice(self.template_places[b.category]["exits"][a.category])))

				# Immediatly exits the loop if all the places have at least one exit
				if all(p.exits for p in places):
					break

			# Return to the beginning if it couldn't create enough exits
			if not all(p.exits for p in places):
				continue

			# Links exits and places
			joinPlaces(places, [e for p in places for e in p.exits])

			# Ensures all the places are linked
			if not checkMap(places):
				continue

			# Saves the new places
			self.places = places
			return

		# Raise an error if it couldn't generate the exits
		raise RuntimeError("Couldn't create the map")

def checkMap(places):
	todo = places.copy()
	pending = []

	# Picks the starting place
	start = todo.pop()
	
	# Sets its neighbors as pending
	pending.extend([e.direction for e in start.exits])

	# While there are pending places
	while pending:
		# Removes them from the list
		place = pending.pop()
		if place in todo:
			todo.remove(place)

		# Marks as pending its neighbors
		for exit in [e.direction for e in place.exits]:
			if exit in todo:
				pending.append(exit)

	# Return True if the program has gone to all the places
	return not todo

def joinPlaces(places, exits):
	for exit in exits:
		# Sets exit's direction
		directions = [p for p in places if p.tag == exit.tag]
		if len(directions) < 1:
			raise ValueError(f"No places with the #{tag} tag have ben found")
		elif len(directions) > 1:
			raise ValueError(f"Too many places with the #{tag} tag have been found")
		else:
			exit.direction = directions[0]

		# Sets exit's parent
		parents = list(filter(lambda p: exit in p.exits, places))
		if len(parents) < 1:
			raise ValueError(f"No places have an exit to #{tag}")
		elif len(parents) > 1:
			raise ValueError(f"Too many places have an exit to #{tag}")
		else:
			exit.parent = parents[0]

	# Ensures that all the exits have an inverse
	for exit in exits:
		inverses = list(filter(lambda e: [e.direction, e.parent] == [exit.parent, exit.direction], exits))
		if len(inverses) < 1:
			raise ValueError(f"The exit from #{exit.parent} to #{exit.direction} has no reverse")
		elif len(inverses) > 1:
			raise ValueError(f"The exit from #{exit.direction} to #{exit.parent} is duplicated")
		else:
			exit.inverse = inverses[0]


@dataclass(eq=True, frozen=True)
class Weather:
	modifier: Modifier
	start_event: EventMessages
	end_event: EventMessages
	during_event: EventMessages
	visibility_event: EventMessages

@dataclass(eq=True, frozen=True)
class DayTime:
	range: range
	light: int
	temperature: int
	start_event: EventMessages
	during_event: EventMessages

	@property
	def modifier(self) -> Modifier:
		return Modifier(visibility=self.light) + Modifier(temperature=self.temperature, each_tick=True)
