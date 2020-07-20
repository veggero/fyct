from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set, Optional
from random import choice, shuffle, random
from copy import deepcopy, copy
from time import sleep
from collections import defaultdict

from characters import Character
from gram import Telegram
from words import EventMessages

@dataclass
class World:
	
	weathers: Set[Weather]
	day_times: Set[DayTime]
	
	template_places: Set[Place]
	time: int = 0
	places: Set[Place] = field(default_factory=set)
	
	changeWeatherChance = 1 / 14400
	duringWeatherChance = 1 / 1200
	maxSize = 200
	
	weather: Weather = None
	day_time: DayTime = None
	turn: Optional[Player] = None
	
	def __post_init__(self):
		self.weather = choice([*self.weathers])
		self.day_time = choice([*self.day_times])
		self.generate_map()
	
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
	
	def generate_map(self):
		places_done, exits_pending, current_templates, trash = [], [], [*self.template_places]*2, []
		grade = {1: 0, 2: 0, 3: 0, 4: 0}
		
		# We gotta start somewhere
		start = deepcopy(max(self.template_places, key=lambda x: len(x.exits)))
		places_done.append(start)
		exits_pending.extend(start.exits)
		
		while exits_pending and (len(places_done) <= self.maxSize or len(exits_pending) % 2):
			
			shuffle(exits_pending)
			new, newExit = None, None
			oldExit, *exits_pending = exits_pending
			
			all_places = [*self.template_places]
			shuffle(current_templates)
			shuffle(all_places)
			
			if len(current_templates) < len(all_places):
				current_templates.append(pick := choice(trash))
				trash.remove(pick)
			
			# Perfect fit in current_templates?
			current_templates = sorted(current_templates, key=lambda t: -len(t.tags & oldExit.tags))
			new = deepcopy(choosen := next((t for t in current_templates if len(t.tags & oldExit.tags) +
				max(len(e.tags & oldExit.parent.tags) for e in t.exits) >= 2), None))
			if new:
				current_templates.remove(choosen)
				trash.append(choosen)
				grade[1] += 1
			
			# Otherwise, perfect fit in past ones?
			if not new:
				for possibleExit in exits_pending:
					if possibleExit.parent.tags == oldExit.tags and oldExit.parent.tags == possibleExit.tags:
						newExit = possibleExit
						grade[2] += 1
						break
			
			# Perfect fit in all templates?
			if not new and not newExit:
				new = deepcopy(next((t for t in all_places if t.tags == oldExit.tags), None))
				grade[3] += 1
			
			# UN-Perfect fit if EVERYTHING ELSE FUCKING FAILED
			if not new and not newExit:
				new = deepcopy(sorted(all_places, key=lambda t: (len(t.tags & oldExit.tags), len(t.exits), len(t.tags)))[0])
				grade[4] += 1
			
			if new:
				newExit, *nexExits = sorted(new.exits, key=lambda x: -len(x.tags & oldExit.parent.tags))
				newExit.direction, oldExit.direction = oldExit.parent, newExit.parent
				newExit.inverse, oldExit.inverse = oldExit, newExit
				exits_pending.extend(nexExits)
				places_done.append(new)
			elif newExit:
				newExit.direction, oldExit.direction = oldExit.parent, newExit.parent
				newExit.inverse, oldExit.inverse = oldExit, newExit
				exits_pending.remove(newExit)
			else:
				assert False
		
		while exits_pending:
			newExit, oldExit = exits_pending.pop(), exits_pending.pop()
			newExit.direction, oldExit.direction = oldExit.parent, newExit.parent
			newExit.inverse, oldExit.inverse = oldExit, newExit
		
		self.places = places_done
		
		# MAP VALUTATION
		all_tags = [tag for place in self.places for tag in place.tags]
		count_tags = {tag: all_tags.count(tag) for tag in set(all_tags)}
		print(len(self.places), self.maxSize)
		print(grade)
		print(dict(sorted(count_tags.items(), key=lambda a: a[1], reverse=True)))

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
