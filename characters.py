from __future__ import annotations

from core import Modifier, Action, Attack, Sound, Defense
from words import Description, EventMessages, Events, Format, Ending
from life import VitalParameter, Wound, State, States, Wounds, VitalParameters
from gram import Telegram
from containers import Inventory
from things import Object
from copy import deepcopy

from dataclasses import dataclass, field
from typing import Optional
from random import random

@dataclass
class Character:
	
	
	description: Description
	
	strenght: int
	agility: int
	visibility: int
	_strenght: int = 50 #avg 50
	_agility: int = 50 #avg 50
	_visibility: int = 3
	
	inventory: Inventory = field(default_factory=Inventory)
	
	place: Optional[Place] = None
	world: Optional[World] = None
	
	thirst: VitalParameter = field(default_factory=VitalParameters.thirst)
	hunger: VitalParameter = field(default_factory=VitalParameters.hunger)
	sleepiness: VitalParameter = field(default_factory=VitalParameters.sleepiness)
	fatigue: VitalParameter = field(default_factory=VitalParameters.fatigue)
	bloodlost: VitalParameter = field(default_factory=VitalParameters.bloodlost)
	cold: VitalParameter = field(default_factory=VitalParameters.cold)
	hot: VitalParameter = field(default_factory=VitalParameters.hot)
	
	vital_names: str = ('thirst', 'hunger', 'sleepiness', 'fatigue', 'bloodlost', 'cold', 'hot')
	
	wounds: List[Wound] = field(default_factory=list)
	state: State = field(default_factory=lambda: States.Normal)
	
	busy_until: int = 0
	events: Events = field(default_factory=Events)
	last_exit: Optional[Exit] = None
	instances = []
	visible: bool = True
	current_actions: List[Action] = field(default_factory=list)
	groundActions: List[Action] = field(default_factory=list)
	
	def __post_init__(self):
		self.vitals = [getattr(self, x) for x in self.vital_names]
		for vital in self.vitals: vital.parent = self
		self.inventory.parent, self.description.parent = self, self
		self.instances.append(self)
	
	@property
	def modifier(self) -> Modifier:
		mod = sum(x.modifier for x in [self.place, self.inventory] + self.wounds + [getattr(self, x) for x in self.vital_names])
		if self.state.modifier: mod += self.state.modifier
		return mod
	
	@property
	def visibility(self):
		return self._visibility + self.modifier.permanent['visibility']
	@visibility.setter
	def visibility(self, value): self._visibility = value
		
	@property
	def agility(self):
		return self._agility + self.modifier.permanent['agility']
	@agility.setter
	def agility(self, value): self._agility = value
		
	@property
	def strenght(self):
		return self._strenght + self.modifier.permanent['strenght']
	@strenght.setter
	def strenght(self, value): self._strenght = value
	
	@property
	def actions(self) -> List[Action]:
		return [a for a in (self.state.actions or [action for x in (self.place, self.inventory, 
			self.thirst, self.hunger, self.sleepiness, self.fatigue, self.bloodlost, 
			self.cold, self.hot) for action in x.actions] + self.social_actions)
			if a.condition(self)]
	
	@property
	def social_actions(self) -> List[Action]:
		return [
			Action(
				f'Interagisci con {person.description.far if direction else person.description.oneof}',
				do=(lambda person: lambda character:
					[Action(
						f'Attacca',
						do=lambda character: character.war_actions(person),
						event=EventMessages(), time=1, fatigue=0
					)] * bool(character.war_actions(person)) +
					[Action(
						f'Dai oggetti',
						do=lambda character: character.give_actions(person),
						event=EventMessages(), time=1, fatigue=0
					)] * bool(self.give_actions(person) and not direction) +
					[Action(
						f'Indietro', do=lambda character: None, 
						event=EventMessages(), time=0, fatigue=0
					)]
				)(person),
				event=EventMessages(), time=0, fatigue=0
			)
			for person, direction in self.place.objects_around(self.visibility, all=False).items()
			if isinstance(person, Character) and (person is not self) and
			(self.war_actions(person) or (self.give_actions(person) and not direction))]
	
	def war_actions(self, target) -> List[Action]:
		return [Action(
			name=attack.name.format(target=target.description.oneof).capitalize(),
			event=EventMessages(),
			time=1, fatigue=1,
			do=(lambda attack: lambda char: attack.do(char, target))(attack))
		  for attack in self.inventory.attacks + self.place.attacks
		  if target in self.place.objects_around(attack.range) and attack.condition(self, target)]
	
	def give_actions(self, target) -> List[Action]:
		return [Action(
			name=f'Dai {obj.description.oneof}',
			event=EventMessages(
				subject=f'Dai {obj.description.oneof} a {{subject}}',
				object=f'{{subject}} ti da {obj.description.oneof}',
				close=f'{{subject}} da {obj.description.oneof} a {{object}}',
				far=f'{{subject}} da qualcosa a {{object}}'),
			time=1, fatigue=0, target=target,
			do=(lambda obj: lambda char: char.inventory.remove(obj) and target.inventory.add(obj, target))(obj),
			condition=(lambda obj: lambda char: char.inventory.pick_message(obj))
			)
		  for obj in self.inventory.all_objects]
	
	@property
	def defenses(self) -> List[Defense]:
		return self.state.defenses or [x for x in self.inventory.defenses if x.condition(self)]
	
	def look_around(self):
		self.send_event(self.world.day_time.during_event)
		self.send_event(self.world.weather.during_event)
		self.events.append(f'Sei {self.place.description}')
		chars = self.place.objects_around(self.visibility)
		del chars[self]
		for char, direction in chars.items():
			self.events.append(Format((f'verso {direction[-1].description} ' if direction else '') +'vedi {object}',
				object=char.description.nfar if direction else char.description.nclose))
	
	def sleep(self):
		self.busy_until = self.world.time + 600
		self.state = States.Sleeping
	
	def wakeup(self):
		if not self.state is States.Sleeping: return
		self.events.append('ti svegli')
		self.state = States.Lying
		self.busy_until = self.world.time + 1
		self.look_around()
	
	def check_wounds(self):
		for wound in [*self.wounds]:
			if (wound.duration and wound.end_time < self.world.time) or (wound.until and wound.until(self)):
				wound.unaffect(self)
			elif random() > .9: self.send_event(wound.during_event)
	
	def tick(self):
		self.wakeup()
		self.check_wounds()
		Telegram.instance.ask(self, self.actions)
	
	def apply_modifier(self, time, modifier):
		for key, value in modifier.each_tick.items():
			setattr(self, key, getattr(self, key) + value * time)
	
	def work_for(self, time):
		self.apply_modifier(time, self.modifier)
	
	def move_to(self, exit):
		self.place.contained.remove(self)
		self.place = exit.direction
		self.last_exit = exit.inverse
		self.place.contained.add(self)
	
	def send_event(self, event: EventMessages, target=None, sound=None, before=None, after=None):
		event = deepcopy(event)
		if (msg := event.subject) and self.state.can_see:
			self.events.append(Format(msg, subject=target and target.description.close))
		if (msg := event.object) and target and target.state.can_see:
			target.events.append(Format(msg, subject=self.description.close))
		for char in self.instances:
			a = (after and after[char]) or char.place.objects_around(char.visibility)
			b = (before and before[char]) or a
			if char is self or (target and char is target): continue
			if (delta := self.place.deltaObject(b, a, self)) and char.state.can_see:
				char.events.append(Format(
					getattr(event, delta[0]),
					subject=getattr(self.description, EventMessages.what_description[delta[0]]),
					object=target and getattr(target.description, EventMessages.what_description[delta[0]]),
					direction=delta[1].description if delta[1] else ''))
			elif sound and self in (around := char.place.objects_around(sound.strenght)):
				if sound.strenght > 4 and char.state is States.Sleeping: char.wakeup()
				if not char.state.can_see: continue
				char.events.append(Format(sound.event.far, direction=around[self][-1].description))
	
	def send_visibility_event(self, event: EventMessages, before):
		if not self.state.can_see: return
		after = {c: c.place.objects_around(c.visibility) for c in Character.instances}
		event = deepcopy(event)
		for obj in set(before[self]) | set(after[self]):
			delta = self.place.deltaObject(before[self], after[self], obj)
			self.events.append(Format(
				getattr(event, delta[0]), 
				object=getattr(obj.description, EventMessages.what_description[delta[0]]),
				direction=delta[1] and delta[1].description))
	
	def die(self):
		self.place.contained.remove(self)
		self.place.contained.append(Object(
			self.description,
			default_state=Ending(*['a terra, cadavere']*3),
			volume=100, visible=True,
			ground_actions=[Action(
				f'Esamina il cadavere di {self.description.nclose}',
				EventMessages(
					subject='esamini il cadavere',
					close=f'{{subject}} esamina il cadavere di {self.description.nclose}',
					far=f'{{subject}} esamina il cadavere di {self.description.nclose}',
					),
				do = lambda character: self.inventory.raid(character), time = 2,
				)]
			))
		self.instances.remove(self)
		return v
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other
	def __str__(self): return str(self.description)
