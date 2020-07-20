from __future__ import annotations

from words import Description, EventMessages
from core import Action, Modifier
from life import Wounds

from dataclasses import dataclass, field

@dataclass
class Object:
	
	description: Description
	volume: int = 5
	visible: bool = False
	picked_actions: List[Action] = field(default_factory=list)
	ground_actions: List[Action] = field(default_factory=list)
	modifier: Modifier = field(default_factory=Modifier)
	
	pick_verb, drop_verb = 'prendi', 'lascia'
	
	@property
	def drop_action(self):
		return Action(
				f'{self.drop_verb} {self.description.close}'.capitalize(),
				EventMessages(
					subject=f'posi a terra {self.description.close}',
					close=f'{{subject}} posa a terra {self.description.nclose}',
					far=f'{{subject}} posa a terra qualcosa'),
				lambda player: player.inventory.drop(self, player))
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other
	def __str__(self): return str(self.description)

@dataclass
class Dress(Object):
	type: str = 'shirt'
	pick_verb, drop_verb = 'indossa', 'togliti'
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other

@dataclass
class HealWound(Object):
	wound: Wound = Wounds.TaglioBraccia
	
	@property
	def picked_actions(self):
		return [Action(
			f'Cura {self.wound.name} con {self.description.oneof}',
			EventMessages(
				subject=f'Curi {self.wound.name}',
				close=f'{{subject}} cura {self.wound.name} con {self.description.oneof}'
				),
			lambda char: self.wound.unaffect(char) or char.inventory.remove(self),
			condition=lambda char: self.wound in char.wounds
			)]
	
	@picked_actions.setter
	def picked_actions(self, value): return
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other

@dataclass
class Food(Object):
	nutrition: int = 20
	
	@property
	def picked_actions(self):
		return [Action(
			f'Mangia {self.description}',
			EventMessages(
				subject=f'mangi {self.description}',
				close=f'{{subject}} mangia {self.description}',
				far=f'{{subject}} mangia qualcosa'
				),
			lambda char: setattr(char, 'hunger', char.hunger - self.nutrition) or \
				char.inventory.remove(self)
			)]
	
	@picked_actions.setter
	def picked_actions(self, value): return
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other

@dataclass
class WaterContainer(Object):
	water: int = 20
	volume: int = 10
	
	@property
	def picked_actions(self):
		return [Action(
			f'Bevi {self.description}',
			EventMessages(
				subject=f'bevi {self.description}',
				close=f'{{subject}} beve {self.description}',
				far=f'{{subject}} beve qualcosa'
				),
			lambda char: setattr(char, 'thirst', char.thirst - self.water) or \
				setattr(self, 'water', 0) or \
				char.inventory.contained.remove(self)
			)]
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other

@dataclass
class Weapon(Object):
	attacks: List[attack] = field(default_factory=list)
	defenses: List[defense] = field(default_factory=list)
	
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other
