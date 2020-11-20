from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

class Ending(str):
	
	def __new__(cls, singular='', two='', plural=''):
		self = str.__new__(Ending, singular.strip())
		self.two = two.strip()
		self.plural = plural.strip()
		return self
	
	def __add__(self, other):
		return Ending(super().__add__(' ' + other),
				self.two + ' ' + other.two, self.plural + ' ' + other.plural)

@dataclass
class Description:
	
	close_singular: str
	close_plural: str
	far_singular: str
	far_plural: str
	first_seen_adj: str = ''
	singular_undef_article: str = 'un'
	singular_def_article: str = 'il'
	plural_def_article: str = 'i'
	plural_undef_article: str = 'dei'
	two_article: str = 'due'
	
	default_state = Ending('','','')
	
	grouped: bool = False
	parent: Optional[Character] = None
	
	@property
	def identifier(self) -> Ending:
		"This does not change based on the state, so it always identifies the object."
		return Ending(
			f'{self.singular_def_article} {self.close_singular}',
			f'{self.two_article} {self.close_plural}',
			f'{self.plural_def_article} {self.close_plural}')
	
	@property
	def state(self) -> Ending:
		if not self.parent: return Ending('','','')
		return self.parent.state.ending
	
	@property
	def close(self) -> Ending:
		return self.identifier + self.state
	
	@property
	def nclose(self) -> Ending:
		return Ending(
			f'{self.singular_undef_article} {self.close_singular} {self.first_seen_adj}',
			f'{self.two_article} {self.close_plural}',
			f'{self.plural_undef_article} {self.close_plural}') + self.state
	
	@property
	def far(self) -> Ending:
		return Ending(
			f'{self.singular_def_article} {self.far_singular}',
			f'{self.two_article} {self.far_plural}',
			f'{self.plural_def_article} {self.far_plural}') + self.state
	
	@property
	def nfar(self) -> Ending:
		return Ending(
			f'{self.singular_undef_article} {self.far_singular}',
			f'{self.two_article} {self.far_plural}',
			f'{self.plural_undef_article} {self.far_plural}') + self.state
	
	@property
	def oneof(self) -> Ending:
		return self.nclose if self.grouped else self.close
	
	def __str__(self):
		return self.close

@dataclass(eq=True, frozen=True)
class EventMessages:
	
	subject: str = ''
	object: str = ''
	close: str = ''
	far: str = ''
	close_to_far: str = ''
	close_to_none: str = ''
	far_to_close: str = ''
	far_to_closer: str = ''
	far_to_farer: str = ''
	far_to_none: str = ''
	none_to_close: str = ''
	none_to_far: str = ''
	
	what_description = {
		'subject': 'oneof',
		'object': 'oneof',
		'close': 'oneof',
		'far': 'far',
		'close_to_far': 'close',
		'close_to_none': 'close',
		'far_to_close': 'close',
		'far_to_closer': 'far',
		'far_to_farer': 'far',
		'far_to_none': 'far',
		'none_to_close': 'nclose',
		'none_to_far': 'nfar'
		}

class Format:
	
	def __init__(self, msg: str, **kwargs):
		assert isinstance(msg, (str, Format)), msg
		self.kwargs = {key: [value] for key, value in kwargs.items() if value is not None}
		if isinstance(msg, Format):
			self.kwargs.update(msg.kwargs)
			msg = msg.msg
		self.msg = msg
	
	def union(self, other):
		for key in set(self.kwargs) | set(other.kwargs):
			if key in self.kwargs and key in other.kwargs:
				self.kwargs[key].extend(other.kwargs[key])
			elif key in other.kwargs and key not in self.kwargs:
				self.kwargs[key] = other.kwargs[key]
	
	def __str__(self):
		return self.msg.format(**{key: self.quantify(value).strip()
			for key, value in self.kwargs.items()}).strip()
	
	@staticmethod
	def join(objects):
		objects = [*filter(bool, objects)]
		if not objects: return ''
		if len(objects) == 1:
			return objects[0]
		*others, last = objects
		return ', '.join(others) + ' e ' + last
	
	@staticmethod
	def quantify(objects):
		return Format.join([*{x if (objects.count(x) == 1 or not hasattr(x, 'two')) else x.two 
			if objects.count(x) == 2 else x.plural for x in objects}])

class Events(list):
	
	def append(self, obj):
		if not str(obj): return
		if isinstance(obj, Format):
			for message in self:
				if isinstance(message, Format) and message.msg == obj.msg:
					return message.union(obj)
			for oldobj in [oldobj for oldobj in self if isinstance(oldobj, Format)]:
				for key in set(oldobj.kwargs) & set(obj.kwargs):
					if oldobj.kwargs[key] == obj.kwargs[key]:
						obj.kwargs[key] = [] #it's implicit in the sentence
		super().append(obj)
	
	def __str__(self):
		return Format.join([*map(str, self)]).capitalize()

@dataclass
class ExitDescription:
	going_to: str
	coming_from: str
	description: str

	def __str__(self):
		return self.going_to + self.description

	@property
	def inverse(self):
		return self.coming_from + self.description

	def __hash__(self):
		return hash(str(self))
