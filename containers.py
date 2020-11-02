from __future__ import annotations

from words import EventMessages, Format
from things import Object, Weapon
from core import Attack, Action, Defense, Modifier
from life import States
from things import Dress

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain

class ObjectGroup:
	
	def __init__(self, elements=()):
		self.d = defaultdict(list)
		self.all = list(elements)
		for element in elements:
			self.d[element.description.identifier].append(element)
	
	def add(self, obj):
		self.all.append(obj)
		self.d[obj.description.identifier].append(obj)
	
	def remove(self, obj):
		self.all.remove(obj)
		self.d[obj.description.identifier].remove(obj)
	
	def count(self, obj):
		return len(self.d[obj.description.identifier])
	
	def __iter__(self):
		for key, value in self.d.items():
			if value:
				value[0].description.grouped = len(value) > 1
		return(iter([value[0] for value in self.d.values() if len(value)]))
	
	@property
	def modifier(self):
		return sum(obj.modifier for obj in self.d) or Modifier()
	
	@property
	def actions(self):
		return [Action(f'Conta {value[0].description.close.plural}',
				EventMessages(subject=f'Conti {value[0].description.close.plural} e sono {len(value)}'),
				lambda player: 0, 0, 0) for key, value in self.d.items() if len(value) > 2]

@dataclass
class Backpack(Object):
	volume: int = 10
	objects: ObjectGroup = field(default_factory=ObjectGroup)

	pick_verb, drop_verb = 'indossa', 'togliti'
	
	def equip(self, obj):
		can_left = lambda player: self.occupied - obj.volume + player.inventory.left_hand.volume > self.volume
		can_right = lambda player: self.occupied - obj.volume + player.inventory.right_hand.volume > self.volume
		
		left_action = Action(f'Prendi nella mano sinistra {obj.description.close}',
					EventMessages(
						subject=f'prendi nella mano sinistra {obj.description.close}',
						close=f'{{subject}} afferra in mano {obj.description.close}'),
					lambda player: actual_equip(player, 'left_hand'), 0, 0,
					condition=can_left)
		right_action = Action(f'Prendi nella mano destra {obj.description.close}',
					EventMessages(
						subject=f'prendi nella mano destra {obj.description.close}',
						close=f'{{subject}} afferra in mano {obj.description.close}'),
					lambda player: actual_equip(player, 'right_hand'), 0, 0,
					condition=can_right)
		choose_action = Action(f'Prendi in mano {obj.description.close}',
					EventMessages(subject='si, ma in che mano?'),
					lambda p: [left_action, right_action], 0, 0,
					condition=lambda p: can_left(p) and can_right(p))
		
		def actual_equip(player, hand):
			if getattr(player.inventory, hand):
				self.objects.add(getattr(player.inventory, hand))
			self.objects.remove(obj)
			setattr(player.inventory, hand, obj)
		
		return [left_action, right_action, choose_action]
	
	def check_backpack(self, player):
		actions = []
		for obj in self.objects.all:
			player.events.append(Format('nello zaino hai {obj}', obj=obj.description.close))
		for obj in self.objects:
			actions.append(obj.drop_action)
			actions.extend(self.equip(obj))
			actions.extend(obj.picked_actions)
		actions.extend(self.objects.actions)
		if not self.objects:
			player.events.append('...è vuoto')
		actions.append(Action('Indietro', EventMessages(), lambda p: None, 0, 0))
		actions = [a for a in actions if a.condition(player)]
		return actions
	
	@property
	def occupied(self):
		return sum(o.volume for o in self.objects.all)
	
	@property
	def picked_actions(self) -> List[Action]:
		return [Action(f'Guarda cosa hai dentro {self.description.close}',
				 EventMessages(), self.check_backpack, 0, 0)]
	
	@picked_actions.setter
	def picked_actions(self, x): pass
	def __hash__(self): return id(self)
	def __eq__(self, other): return self is other

@dataclass
class Inventory:
	
	left_hand: Optional[Object] = None
	right_hand: Optional[Object] = None
	
	pants: Optional[Dress] = None #optional? 😏
	shirt: Optional[Dress] = None
	hoodie: Optional[Dress] = None
	
	backpack: Optional[Backpack] = None
	
	@property
	def objects(self) -> ObjectGroup:
		return ObjectGroup(filter(bool, [self.left_hand, self.right_hand, self.pants, self.shirt, self.hoodie, self.backpack]))
	
	@property
	def all_objects(self):
		"This also accounts for objects in the backpack"
		return chain(self.objects, self.backpack.objects) if self.backpack else self.objects
	
	@property
	def modifier(self) -> Modifier:
		return sum(a.modifier for a in self.objects) or Modifier()
	
	@property
	def actions(self) -> List[Action]:
		return [Action('Controlla cosa hai', EventMessages(), self.check_inventory, 0, 0)] * bool(self.objects)
	
	@property
	def weapons(self) -> List[Object]:
		return [w for w in (self.left_hand, self.right_hand) if isinstance(w, Weapon)]
	
	@property
	def attacks(self) -> List[Attack]:
		return [a for w in self.weapons for a in w.attacks] + [Attack(
			'cerca di spingere {target} a terra',
			lambda subject, target: setattr(target, 'state', States.Lying),
			EventMessages(
				subject='cerchi di spingere {subject} a terra',
				object='{subject} cerca di spingerti a terra',
				close='{subject} cerca di spingere {object} a terra',
				far='{subject} cerca di spingere {object} a terra'
				),
			EventMessages(
				subject='{subject} cade a terra',
				object='cadi a terra',
				close='{object} cade a terra',
				far='{object} cade a terra'
				),
			EventMessages(
				subject='rimane in piedi',
				object='rimani in piedi',
				close='{object} rimane in piedi',
				far='{object} rimane in piedi'
				),
			{'arretra'},
			difficulty=25,
			condition=lambda p, t: t.state is States.Normal
			)]
	
	@property
	def defenses(self) -> List[Defense]:
		return [d for w in self.weapons for d in w.defenses] + [Defense(
		'Arretra', {'arretra'}, 25,
		success_event = EventMessages(
			subject='riesci ad arretrare',
			object='{subject} riesce ad arretrare',
			close='{subject} riesce ad arretrare'),
		fail_event = EventMessages(
			subject='non riesci ad arretrare',
			object='{subject} non riesce ad arretrare',
			close='{subject} non riesce ad arretrare'))]
	
	def check_inventory(self, player) -> List[Action]:
		actions = []
		for obj in self.objects.all:
			player.events.append(Format('hai {obj}', obj=obj.description.close))
		for obj in self.objects:
			actions.append(obj.drop_action)
			actions.extend(obj.picked_actions)
		actions.extend(self.objects.actions)
		if self.left_hand and self.backpack and self.backpack.occupied + self.left_hand.volume <= self.backpack.volume:
			actions.append(Action(
				f'Metti {self.left_hand.description.close} nello zaino',
				EventMessages(
					subject=f'Metti {self.left_hand.description.close} nello zaino',
					close=f'{{subject}} mette {self.left_hand.description.close} nello zaino'),
				lambda player: self.backpack.objects.add(self.left_hand) or setattr(self, 'left_hand', None)))
		if self.right_hand and self.backpack and \
			self.backpack.occupied + self.right_hand.volume <= self.backpack.volume and \
			not self.right_hand.description.grouped:
			actions.append(Action(
				f'Metti {self.right_hand.description.close} nello zaino',
				EventMessages(
					subject=f'Metti {self.right_hand.description.close} nello zaino',
					close=f'{{subject}} mette {self.right_hand.description.close} nello zaino'),
				lambda player: self.backpack.objects.add(self.right_hand) or setattr(self, 'right_hand', None)))
		actions.append(Action('Indietro', EventMessages(), lambda player: '', 0, 0))
		actions = [a for a in actions if a.condition(player)]
		return actions
	
	def raid(self, character) -> List[Action]:
		for obj in self.objects.all:
			character.events.append(Format('vedi {obj}', obj=obj.description.close))
		return [Action(
				(f'{obj.pick_verb} {obj.description.oneof}').capitalize(),
				EventMessages(
					subject=f'{obj.pick_verb} {obj.description.oneof} dal cadavere',
					close=f'{{subject}} prende {obj.description.oneof} dal cadavere',
					far=f'{{subject}} prende in mano qualcosa dal cadavere',
					),
				(lambda obj: lambda char: char.inventory.pick(obj, char, self.contained))(obj),
				condition=(lambda obj: lambda char: char.inventory.pick_message(obj))(obj)
			) for obj in self.objects]
	
	def remove(self, obj):
		for prop in ('left_hand', 'right_hand', 'pants', 'shirt', 'hoodie', 'backpack'):
			if getattr(self, prop) is obj:
				setattr(self, prop, None)
				return
		if self.backpack:
			self.backpack.objects.remove(obj)
		assert 0, obj.description
	
	def drop(self, obj, player):
		self.remove(obj)
		player.place.contained.add(obj)
	
	def pick_message(self, obj):
		if isinstance(obj, Dress):
			if not getattr(self, obj.type): return True
		elif isinstance(obj, Backpack):
			if not self.backpack: return True
		elif isinstance(obj, Object):
			if not self.left_hand: return True
			elif not self.right_hand: return True
			elif self.backpack and obj.volume + self.backpack.occupied <= self.backpack.volume: return True
	
	def add(self, obj, player):
		if isinstance(obj, Dress):
			setattr(self, obj.type, obj)
		elif isinstance(obj, Backpack):
			self.backpack = obj
			for bkobj in obj.objects:
				player.events.append(Format("dando un'occhiata vedi che contiene {bkobj}", bkobj=bkobj.description.nclose))
		elif isinstance(obj, Object):
			if not self.left_hand: self.left_hand = obj
			elif not self.right_hand: self.right_hand = obj
			else: self.backpack.objects.add(obj)
			if self.left_hand and self.right_hand and not self.backpack:
				player.send_event(EventMessages('hai le mani piene'))
	
	def pick(self, obj, player, container):
		self.add(obj, player)
		container.remove(obj)
		if container.count(obj) > 1:
			player.events.append('vedi che ce ne sono ancora')
		elif container.count(obj) == 1:
			self.parent.events.append(Format("vedi che rimane solo {obj}", obj=obj.description.nclose))
