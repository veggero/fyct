from __future__ import annotations

from core import Modifier, Action, Attack, Defense, Sound
from words import EventMessages, Format
from things import Object
from containers import ObjectGroup

from typing import Set, Dict, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from copy import copy

@dataclass
class Place:
	
	description: str
	exits: Set[Exit]
	tags: Set[str]
	height: int = 0
	soundproof: int = 0
	contained: ObjectGroup = field(default_factory=ObjectGroup)
	actions: List[Action] = field(default_factory=list)
	attacks: List[Attack] = field(default_factory=list)
	defenses: List[Defense] = field(default_factory=list)
	
	def __post_init__(self):
		for exit in self.exits: exit.parent = self
	
	@property
	def objects_description(self) -> str:
		if bigs := [o.description.far for o in self.contained if o.visible]:
			return f', verso {Format.quantify(bigs)}'
		return ''
	
	@property
	def modifier(self) -> Modifier:
		return Modifier(visibility=self.height)
	
	@property
	def actions(self) -> List[Action]:
		return self._user_actions + \
			[a for exit in self.exits for a in exit.actions] + \
			self.contained.actions + \
			[Action(
				(f'{obj.pick_verb} {obj.description.oneof}').capitalize(),
				EventMessages(
					subject=f'{obj.pick_verb} {obj.description.oneof}',
					close=f'{{subject}} prende {obj.description.oneof}',
					far=f'{{subject}} prende in mano qualcosa',
					),
				(lambda obj: lambda char: char.inventory.pick(obj, char, self.contained))(obj),
				condition=(lambda obj: lambda char: char.inventory.pick_message(obj))(obj)
			) for obj in self.contained if isinstance(obj, Object) and not obj.visible] + \
			[a for obj in self.contained for a in obj.ground_actions if isinstance(obj, Object)]
	
	@actions.setter
	def actions(self, user_actions: List[Action]):
		self._user_actions = user_actions if isinstance(user_actions, list) else []
	
	def objects_around(self, visibility: int, done=(), all=True, dirs=(), d=None):
		d = d or {}
		if visibility >= 1:
			for exit in self.exits - set(done):
				exit.direction.objects_around(visibility-1, done + (self,), all, dirs+(exit,), d)
		for obj in (self.contained.all if all else self.contained):
			if obj.visible or not dirs:
				d[obj] = dirs
		return d
	
	"""def objects_around(self, visibility: int, done=(), all=True) -> Dict[Object, Tuple[Place]]:
		around = {}
		if visibility >= 1:
			around.update({obj: loc+(exit,) for exit in self.exits - set(done)
			for obj, loc in exit.direction.objects_around(visibility-1, done + (self,), all).items()
			if obj.visible})
		around.update({obj: () for obj in (self.contained.all if all else self.contained)})
		return around"""
	
	def get_exit(self, tags):
		return next(exit for exit in self.exits if exit.tags == tags)
	
	def deltaObject(self, before, after, obj) -> Dict[str, List[Tuple[Object, Exit]]]:
		if obj in before and obj not in after:
			if before[obj]: return 'far_to_none', before[obj][-1]
			else: return 'close_to_none', None
		elif obj in after and obj not in before:
			if after[obj]: return 'none_to_far', after[obj][-1]
			else: return 'none_to_close', None
		elif obj in after and obj in before:
			if len(before[obj]) > len(after[obj]):
				if after[obj]: return 'far_to_closer', after[obj][-1]
				else: return 'far_to_close', None
			elif len(before[obj]) < len(after[obj]):
				if before[obj]: return 'far_to_farer', after[obj][-1]
				else: return 'close_to_far', after[obj][-1]
			else:
				if before[obj]: return 'far', after[obj][-1]
				else: return 'close', None
	
	def __eq__(self, other): self is other
	def __hash__(self): return id(self)

@dataclass
class Exit:
	
	description: str
	tags: Set[str]
	distance: int = 5
	
	direction: Optional[Place] = None
	parent: Optional[Place] = None
	inverse: Optional[Exit] = None
	
	@property
	def actions(self) -> List[Action]:
		a = Action(
			time = self.distance,
			fatigue = self.distance,
			sound = Sound(event=EventMessages(far='{direction} senti qualcuno che cammina',)),
			name = f'Vai {self.description + self.direction.objects_description}',
			event = EventMessages(),
			visibility_event = EventMessages(
				close_to_far = 'dietro di te vedi ancora {object}',
				close_to_none = 'dietro di te non vedi più {object}',
				far_to_close = 'arrivi da {object}',
				far_to_closer = 'ti avvicini verso {object}, che vedi {direction}',
				far_to_farer = 'dietro di te vedi ancora {object}',
				far_to_none = 'dietro di te non vedi più {object}',
				none_to_close = 'come arrivi vedi {object}',
				none_to_far = 'ora {direction} vedi {object}'),
			post_event = EventMessages(
				subject = f'arrivi {self.direction.description}',
				close=f'{{subject}} si allontana {self.description} ma la strada curva e riporta da te',
				close_to_far = f'{{subject}} si allontana {self.description}',
				close_to_none = f'{{subject}} si allontana {self.description} e scompare dalla tua vista',
				far = 'distante, {direction}, vedi {subject} spostarsi',
				far_to_close = f'{self.inverse.description} da te arriva {{subject}}',
				far_to_closer = 'ancora distante, {direction} vedi avvicinarsi {subject}',
				far_to_farer = 'già distante, {direction} vedi allontanarsi {subject}',
				far_to_none = '{direction} vedi {subject} allontanarsi e scomparire dalla tua vista',
				none_to_close = f'improvvisamente {{subject}} arriva da te {self.inverse.description}',
				none_to_far = 'improvvisamente vedi {subject} {direction}'),
			do = lambda c: c.move_to(self),
			condition = lambda c: c.last_exit is not self)
		b = copy(a) # Same, but with 'Torna verso' instead of 'Vai verso'
		b.name = f'Torna {self.description + self.direction.objects_description}'
		b.condition = lambda c: c.last_exit is self
		return [a, b]
	
	def __eq__(self, other): self is other
	def __hash__(self): return id(self)
