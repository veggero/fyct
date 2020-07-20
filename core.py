from __future__ import annotations

from words import EventMessages, Format
from gram import Telegram

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Callable, Set
from random import randint

class Modifier:
	
	def __init__(self, each_tick: bool = False, **kwargs):
		self.permanent = defaultdict(int, {} if each_tick else kwargs)
		self.each_tick = defaultdict(int, kwargs if each_tick else {})
	
	def __add__(self: Modifier, other: Modifier):
		if isinstance(other, int): return self
		for key in other.permanent: self.permanent[key] += other.permanent[key]
		for key in other.each_tick: self.each_tick[key] += other.each_tick[key]
		return self
	
	def __radd__(self, other): return self.__add__(other)

@dataclass
class Action:
	name: str
	event: EventMessages
	do: Callable[Character, Optional[List[Action]]]
	time: int = 1
	fatigue: int = 1
	sound: Optional[Sound] = None
	condition: Callable[Character, bool] = lambda c: True
	visibility_event: Optional[EventMessages] = None
	post_event: Optional[EventMessages] = None
	target: Optional[Character] = None
	
	def execute(self, char: Character):
		before = {c: c.place.objects_around(c.visibility) for c in char.instances}
		char.send_event(self.event, sound=self.sound, target=self.target)
		output = self.do(char)
		if self.post_event:
			char.send_event(self.post_event, before=before, target=self.target)
		if self.visibility_event:
			char.send_visibility_event(self.visibility_event, before)
		char.busy_until += self.time / ((char.agility+50)/100)
		char.fatigue += self.fatigue
		if output:
			Telegram.instance.tick()
			return Telegram.instance.ask(char, output)
		char.world.turn = None

@dataclass
class Sound:
	event: EventMessages
	strenght: int = 4

@dataclass
class Dodge:
	name: str
	def do(self, char, target): return

@dataclass
class Attack:
	name: str
	success: Callable[[Character, Character]]
	event: EventMessages
	success_event: Optional[EventMessages] = None
	fail_event: Optional[EventMessages] = None
	tags: Set[str] = field(default_factory=set)
	range: int = 0
	difficulty: int = 0
	condition: Callable[[Character, Character], bool] = lambda c, t: True
	
	def do(self, char: Character, target: Character):
		target.wakeup()
		char.send_event(self.event, target=target)
		defense = Telegram.instance.chooseDefense(target, [d for d in target.defenses if d.tags & self.tags], 'Difenditi!')
		if randint(-50, 150) + char.agility < defense.chances + target.agility + self.difficulty:
			target.send_event(defense.success_event, target=char)
			if self.fail_event: char.send_event(self.fail_event, target=target)
			if defense.reply:
				#TODO chooseDefense is misleading
				Telegram.instance.chooseDefense(target,
					defense.reply,
					"Rispondi all'attacco...").do(target, char)
		else:
			target.send_event(defense.fail_event, target=char)
			if self.success_event: char.send_event(self.success_event, target=target)
			self.success(char, target)

@dataclass
class Defense:
	name: str
	tags: Set[str]
	chances: Callable[[Character, Character], int]
	success_event: EventMessages
	fail_event: EventMessages
	condition: Callable[Character, bool] = lambda t: True
	reply: List[Attack] = field(default_factory=list)
