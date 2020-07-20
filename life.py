from __future__ import annotations

from core import Modifier, Action, Defense
from words import Ending, EventMessages

from dataclasses import dataclass, field
from copy import copy
from typing import List, Optional

@dataclass
class VitalParameter:
	
	low_up_message: str
	medium_up_message: str
	high_up_message: str
	low_down_message: str
	medium_down_message: str
	high_down_message: str
	
	die_event: EventMessages
	modifier: Optional[Callable[Int, Modifier]] = None
	action: Optional[Action] = None
	wound: Optional[Wound] = None
	
	value: int = 0
	parent: Optional[Character] = None
	
	@property
	def actions(self) -> List[Action]:
		return [self.action] if self.value > 25 and self.action else []
	
	@property
	def modifier(self) -> Modifier:
		return self.__mod(self.value)
	
	@modifier.setter
	def modifier(self, value):
		if not isinstance(value, type(lambda: 0)):
			value = lambda x: Modifier()
		self.__mod = value
	
	def __sub__(self, value): return self + (-value)
	
	def __add__(self, other):
		if self.value + other > 120 and self.value <= 120:
			self.parent.state = States.Normal #TODO add a "fucking dead" state
			self.parent.send_event(self.die_event)
			self.parent.die()
		elif self.value + other > 105 and self.value <= 105:
			self.parent.send_event(EventMessages(
				subject='senti le tue forze venirti a meno e ti accasci sul suolo',
				close='{subject} sviene',
				far='{subject} si accascia a terra'))
			self.parent.state = States.Unconscious
		elif self.value + other < 90 and self.value >= 90:
			self.parent.state = States.Lying
			self.parent.send_event(EventMessages(
				subject='ti senti meglio, e torni in te',
				close='{subject} riprende i sensi'))
		elif self.value + other < 0:
			other = 0 - self.value
		elif self.value + other >= 30 and self.value < 30:
			self.parent.send_event(EventMessages(self.low_up_message))
		elif self.value + other >= 60 and self.value < 60:
			self.parent.wakeup()
			self.parent.send_event(EventMessages(self.medium_up_message))
		elif self.value + other >= 80 and self.value < 80:
			self.parent.wakeup()
			self.parent.send_event(EventMessages(self.high_up_message))
			if self.wound and not self.wound in self.parent.wounds:
				self.wound.affect(self.parent)
		elif self.value + other < 30 and self.value > 30:
			self.parent.send_event(EventMessages(self.low_down_message))
		elif self.value + other < 60 and self.value > 60:
			self.parent.send_event(EventMessages(self.medium_down_message))
		elif self.value + other < 80 and self.value > 80:
			self.parent.send_event(EventMessages(self.high_down_message))
		new = copy(self)
		new.value = self.value + other
		return new
	
	def __str__(self): return str(self.value)

class VitalParameters:
	thirst = lambda: VitalParameter(
		'inizi ad avere sete', 'hai molta sete, ti senti più debole', 'stai morendo di sete, ti senti debolissimo',
		'non hai più sete', 'hai meno sete di prima', '', EventMessages(
			subject='muori di sete', close='{subject} muore di sete', far='{subject} crolla a terra'),
		modifier=lambda p: Modifier(strenght=-.4*p), wound=Wounds.Nausea)
	hunger = lambda: VitalParameter(
		'inizi ad avere fame', 'hai molta fame, ti senti più debole', 'stai morendo di fame, ti senti debolissimo',
		'non hai più fame', 'hai meno fame di prima', '', EventMessages(
			subject='muori di fame', close='{subject} muore di fame', far='{subject} crolla a terra'),
		modifier=lambda p: Modifier(strenght=-.4*p), wound=Wounds.Febbre)
	sleepiness = lambda: VitalParameter(
		'inizi ad avere sonno', 'hai molto sonno', 'stai morendo di sonno',
		'non hai più sonno', 'hai meno sonno di prima', '', EventMessages(
			subject='muori di sonno', close='{subject} muore di sonno', far='{subject} crolla a terra'),
		modifier=lambda p: Modifier(strenght=-.35*p, agility=-.35*p),
		wound=Wounds.Febbre,
		action=Action('Mettiti a dormire per terra',
			event=EventMessages(
				subject='ti addormenti velocemente',
				close='{subject} si mette a dormire a terra',
				far='{subject} si sdraia a terra'),
			do=lambda char: char.sleep(),
			condition=lambda char: char.world.hour > 22 or char.world.hour < 4))
	fatigue = lambda: VitalParameter(
		'inizi a essere stanco', 'sei molto stanco', 'stai morendo di stanchezza',
		'non sei più stanco', 'sei meno stanco di prima', '', EventMessages(
			subject='muori di stanchezza', close='{subject} muore di stanchezza', far='{subject} crolla a terra'),
		modifier=lambda p: Modifier(strenght=-.35*p, agility=-.35*p),
		action=Action('Riposati qui qualche minuto', time=7, fatigue=-30,
			event=EventMessages(
				subject='riposi qualche minuto',
				close='{subject} si ferma per riposarsi',
				far='{subject} si siede brevemente'),
			do=lambda char: None,
			condition=lambda char: char.world.hour > 22 or char.world.hour < 4))
	bloodlost = lambda: VitalParameter(
		'stai perdendo sangue', 'inizi a impallidire da quanto sangue perdi', 'sei praticamente dissanguato',
		'senti di essere di nuovo in forze', 'inizi a sentirti meglio', 'non stai più perdendo sangue', EventMessages(
			subject='muori dissanguato', close='{subject} muore dissanguato', far='{subject} crolla a terra in una pozza di sangue'),
		modifier=lambda p: Modifier(strenght=-.5*p))
	cold = lambda: VitalParameter(
		'inizi ad avere freddo', 'hai molto freddo ora', 'stai gelando',
		'non hai più freddo', 'inizi a scaldarti', 'la temperatura sembra aumentare', EventMessages(
			subject='muori di freddo', close='{subject} muore di freddo', far='{subject} crolla a terra congelato'),
		wound=Wounds.Ipotermia)
	hot = lambda: VitalParameter(
		'inizi ad avere caldo', 'hai molto caldo ora', 'stai evaporando',
		'non hai più caldo', 'inizi a stare meglio', 'la temperatura sembra diminuire', EventMessages(
			subject='muori di caldo', close='{subject} muore di caldo', far='{subject} crolla a terra'),
		modifier=lambda p: Modifier(thrist=-.4*p,),
		wound=Wounds.HeatStroke)

@dataclass
class State:
	
	ending: Ending = field(default_factory=Ending)
	actions: List[Action] = field(default_factory=list)
	defenses: List[Defense] = field(default_factory=list)
	modifier: Optional[Modifier]= None
	can_act: bool = True
	can_see: bool = True
	
class States:
	
	Normal = State(
		modifier = Modifier(thirst=95 / 1440, hunger=50 / 1440, 
		sleepiness = 105 / 1440, fatigue=250/1440, bloodlost=-70/1440, 
		each_tick=True)
		)
	Sleeping = State(
		ending=Ending('che dorme', 'che dormono', 'che dormono'), 
		can_see=False, can_act=False,
		modifier = Modifier(thirst=100 / 1440, hunger=50 / 1440, fatigue=-250/1440,
			sleepiness = -400 / 1440, bloodlost=-70/1440, each_tick=True))
	Unconscious = State(
		ending=Ending('che ha perso i sensi', 'che ha perso i sensi', 'che ha perso i sensi'), 
		can_act=False, can_see=False,
		modifier = Modifier(thirst=100 / 1440, hunger=50 / 1440, fatigue=-300/1440,
			sleepiness = -400 / 1440, bloodlost=-70/1440, each_tick=True))
	Lying = State(
		ending=Ending('a terra', 'a terra', 'a terra'),
		actions=[Action(
			'Alzati', EventMessages(
				subject='ti alzi',
				close='{subject} si alza da terra',
				far='{subject} si alza da terra'
				),
			do=lambda char: setattr(char, 'state', States.Normal),
			time=2, fatigue=0.5
			)],
		defenses=[Defense(
			name='Rotola a terra',
			tags={'arretra'},
			chances=15,
			success_event=EventMessages(
				subject='riesci a rotolare via',
				object='{subject} riesce a rotolare di lato',
				close='{subject} rotola via da {object}',
				far='vedi {subject} rotolare a terra in lontananza'),
			fail_event=EventMessages(
				subject='non riesci a rotolare via',
				object='{subject} prova a rotolare via ma non ci riesce',
				close='{subject} cerca di rotolare via da {object} ma fallisce'
			))],
		modifier = Modifier(thirst=95 / 1440, hunger=50 / 1440, 
		sleepiness = 105 / 1440, bloodlost=-70/1440, each_tick=True) + Modifier(agility=-30)
		)

@dataclass
class Wound:
	name: str
	start_event: EventMessages
	during_event: EventMessages
	worsen_event: EventMessages
	stop_event: EventMessages
	modifier: Optional[Modifier] = None
	duration: Optional[int] = None
	until: Optional[Callable[Character, bool]] = None
	
	end_time: int = 0
	
	def affect(self, character):
		if not self in character.wounds:
			character.send_event(self.start_event)
			character.wounds.append(self)
			self.end_time = character.world.time + (self.duration or 0)
		elif self.modifier:
			character.send_event(self.worsen_event)
			character.apply_modifier(100, self.modifier)
	
	def unaffect(self, character):
		character.wounds.remove(self)
		character.send_event(self.stop_event)

class Wounds:
	
	TaglioBraccia = Wound(
		'il taglio al braccio',
		start_event = EventMessages(
			subject='senti una fitta di dolore e vedi un taglio lungo e profondo sul braccio da cui inizia subito a colare sangue',
			close='{subject} inizia a perdere sangue dal braccio'),
		during_event = EventMessages(
			subject='continui a perdere sangue dal braccio',
			close='{subject} sta visibilmente sanguinando dal braccio'),
		worsen_event = EventMessages(
			subject='il sangue schizza ovunque',
			close='{subject} schizza sangue ovunque'),
		stop_event = EventMessages(
			subject='il taglio al braccio sembra essersi rimarginato, non stai più perdendo sangue',
			close='{subject} sembra di non star più sanguinando dal braccio'),
		modifier= Modifier(bloodlost=65/240, each_tick=True) + Modifier(agility=-10),
		duration=240
		)
	TaglioBusto = Wound(
		'la ferita al petto',
		start_event = EventMessages(
			subject='senti una fitta di dolore e vedi un taglio profondo sul petto da cui cola sangue',
			close='{subject} inizia a perdere sangue dal petto'),
		during_event = EventMessages(
			subject='continui a perdere sangue dal taglio al petto',
			close='{subject} sta visibilmente sanguinando da un taglio al petto'),
		worsen_event = EventMessages(
			subject='il sangue schizza ovunque',
			close='{subject} schizza sangue ovunque'),
		stop_event = EventMessages(
			subject='il taglio al petto sembra essersi rimarginato, non stai più perdendo sangue',
			close='{subject} sembra di non star più sanguinando dal petto'),
		modifier= Modifier(bloodlost=110/240, each_tick=True) + Modifier(agility=-20),
		duration=240
		)
	TaglioGambe = Wound(
		'il taglio alle gambe',
		start_event = EventMessages(
			subject='senti una fitta di dolore e vedi un taglio lungo e profondo su una gamba da cui inizia subito a colare sangue e che ti fa zoppicare',
			close='{subject} inizia a perdere sangue da un taglio alle gambe'),
		during_event = EventMessages(
			subject='continui a perdere sangue dal taglio alle gambe, e non riesci ancora a camminare correttamente',
			close='{subject} sta visibilmente sanguinando da un taglio alle gambe'),
		worsen_event = EventMessages(
			subject='il sangue schizza ovunque',
			close='{subject} schizza sangue ovunque'),
		stop_event = EventMessages(
			subject='il taglio al braccio sembra essersi rimarginato, non stai più perdendo sangue',
			close='{subject} sembra di non star più sanguinando dal braccio'),
		modifier= Modifier(bloodlost=75/24, each_tick=True) + Modifier(agility=-30),
		duration=240
		)
	Nausea = Wound(
		'la nausea',
		start_event = EventMessages(
			subject='inizi a sentire un forte senso di nausea'),
		during_event = EventMessages(
			subject='improvvisamente hai un rigurgito e vomiti per terra',
			close='improvvisamente {subject} si mette a vomitare'),
		worsen_event = EventMessages(),
		stop_event = EventMessages(
			subject='la sgradevole sensazione di nausea termina'),
		modifier= Modifier(hunger=50 / 1440, each_tick=True),
		duration=550
		)
	Febbre = Wound(
		'la febbre',
		start_event = EventMessages(
			subject='inizi a sentirti una forte febbre'),
		during_event = EventMessages(
			subject='la febbre ti da i brividi'),
		worsen_event = EventMessages(),
		stop_event = EventMessages(
			subject='la sensazione di febbre lentamente termina, e ti senti meglio'),
		modifier= Modifier(fatigue=150/1440, hunger=30 / 1440, thirst=50 / 1440, each_tick=True) + 
                  Modifier(agility=-10, strenght=-15),
		duration=1500
		)
	Frattura = Wound(
		'la frattura',
		start_event = EventMessages(
			subject='con grande dolore ti rendi conto di esserti fratturato un osso della gamba'),
		during_event = EventMessages(
			subject='la frattura ti fa un male terribile, zoppichi'),
		stop_event = EventMessages(
			subject='riesci di nuovo, bene o male, a camminare'),
		worsen_event = EventMessages(),
		modifier= Modifier(agility=-50),
		duration=14400
		)
	Ipotermia = Wound(
		'l\'ipotermia',
		start_event = EventMessages(
			subject='ti rendi conto di star andando in ipotermia dal freddo'),
		during_event = EventMessages(
			subject='inizia a non riuscire a muoverti dal freddo'),
		stop_event = EventMessages(
			subject='il sangue inizia a tornare a circolare negli arti, e senti il calore tornare'),
		worsen_event = EventMessages(),
		modifier= Modifier(agility=-40),
		until=lambda char: char.cold < 50
		)
	HeatStroke = Wound(
		'il colpo di sole',
		start_event = EventMessages(
			subject='il caldo inizia a farsi insopportabile, la tua testa inizia a girare'),
		during_event = EventMessages(
			subject='la testa continua a girarti dal caldo'),
		stop_event = EventMessages(
			subject='inizi a sentirti meglio, il sole non è più così intenso'),
		worsen_event = EventMessages(),
		modifier= Modifier(agility=-40),
		until=lambda char: char.hot < 50
		)
	
