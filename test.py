import logging
from gram import Telegram
from copy import deepcopy
from random import randint

from characters import Character
from world import World, DayTime, Weather
from core import Modifier, Attack, Defense, Dodge, Action
from things import Object, Food, HealWound
from life import Wounds, States
from containers import ObjectGroup, Backpack, Weapon
from words import EventMessages, Description, Format
from map import Place, Exit

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

world = World(
	weathers = {
		Weather(
			Modifier(),
			EventMessages(Format('Il sole {sole}', sole='inizia a splendere')),
			EventMessages(Format('Il sole {sole}', sole='smette di splendere')),
			EventMessages(Format('Il sole {sole}', sole='splende sempre più intensamente')),
			EventMessages()
			),
		Weather(
			Modifier(),
			EventMessages('le nuvole si addensano sopra di te'),
			EventMessages('le nuvole sopra di te si diradano'),
			EventMessages('le nuvole si fanno sempre più fitte'),
			EventMessages()
			)
		},
	day_times = {
		DayTime(
			range(24), 0, 0,
			EventMessages(Format('Il sole {sole}', sole='appare nel cielo')),
			EventMessages(Format('Il sole {sole}', sole='è fermo nel cielo')),
			)
		},
	template_places = {
		# *-* CANYON *-*
		Place(
			"in un gigantesco canyon di terra rossa che si estende per chilometri; da qui forse riusciresti a scalarne i muri",
			exits={
				Exit('verso la cima, scalando le rocce', {'bordo'}),
				Exit('lungo il canyon', {'canyon'})
				},
			tags={'canyon'},
			contained=ObjectGroup([
				Weapon(
					Description('sasso', 'sassi', 'sasso', 'sassi'),
					attacks=[Attack(
						'Lancia il sasso verso {target}',
						lambda player, target: setattr(target, 'state', States.Unconscious),
						EventMessages(
							subject='lanci il sasso verso {subject}',
							object='{subject} ti lancia un sasso',
							close='{subject} lancia un sasso verso {object}',
							far='{subject} lancia un sasso verso {object}'
							),
						EventMessages(
							subject='colpisci alla tempia {subject}, che sviene',
							object='{subject} ti colpisce alla tempia e svieni',
							close='il sasso colpisce {object} che sviene',
							far='il sasso colpisce {object} che sviene'
							),
						None, {'arretra'}, 3, 35,
						lambda player, target: target.state is States.Normal
						)]
					)
				])
			),
			Place(
				"in un gigantesco canyon di terra rossa che si estende per chilometri; da qui vedi partire una grotta",
				exits={
					Exit('verso l\'entrata della grotta', {'grotta', 'canyon'}),
					Exit('lungo il canyon', {'canyon'})
					},
				tags={'canyon'}
			),
			Place(
				"in un gigantesco canyon di terra rossa che si estende per chilometri",
				exits={
					Exit('lungo il canyon in una direzione', {'canyon'}),
					Exit('lungo il canyon nell\'altra', {'canyon'})
					},
				tags={'canyon'}
			),
			Place(
				"in un gigantesco canyon che termina improvvisamente in una montagna",
				exits={
					Exit('lungo il canyon', {'canyon'}),
					Exit('verso la montagna', {'bordo', 'montagna'})
					},
				tags={'canyon'}
			),
			Place(
				"in una foresta che termina improvvisamente in un precipizio, che vedi essere un gigantesco canyon",
				exits={
					Exit('giù nel canyon', {'canyon'}),
					Exit('dentro la foresta', {'foresta'})
					},
				tags={'bordo', 'foresta'},
				attacks=[spingi_precipizio := Attack(
					'Spingi {target} giù per il precipizio',
					lambda player, target: (setattr(target, 'state', States.Lying) or 
							                Wounds.Frattura.affect(target) or
							                target.move_to(target.place.get_exit({'canyon'}))),
					EventMessages(
						subject='cerchi di spingere {subject} nel precipizio',
						object='{subject} cerca di spingerti nel precipizio',
						close='{subject} cerca di spingere {object} nel precipizio',
						far='{subject} cerca di spingere {object} nel precipizio'
						),
					EventMessages(
						subject='{subject} cade nel precipizio',
						object='cadi nel precipizio',
						close='{subject} cade nel precipizio',
						far='{subject} cade nel precipizio'
						),
					EventMessages(
						subject='rimane in piedi',
						object='rimani in piedi',
						close='{subject} rimane in piedi',
						far='{subject} rimane in piedi'
						),
					{'arretra'},
					difficulty=45,
					condition=lambda p, t: t.state is States.Normal
					)]
			),
			Place(
				"sulla vetta di una montagna che termina improvvisamente in un precipizio, che vedi essere un gigantesco canyon",
				exits={
					Exit('giù nel canyon', {'canyon'}),
					Exit('lungo la montagna', {'montagna'})
					},
				tags={'bordo', 'montagna'},
				attacks=[spingi_precipizio]
			),
			Place(
				"sulla riva di un lago, che molto curiosamente termina in un precipizio che vedi essere un gigantesco canyon",
				exits={
					Exit('giù nel canyon', {'canyon'}),
					Exit('verso il lago', {'lago'})
					},
				tags={'bordo', 'lago'},
				attacks=[spingi_precipizio]
			),
			# *-* GROTTA *-*
			Place(
				"all'entrata di una grotta, all'esterno della quale vedi un grosso canyon",
				exits={
					Exit('verso il canyon', {'canyon'}),
					Exit('nella grotta', {'grotta'})
					},
				tags={'grotta', 'canyon', 'uscita'},
			),
			Place(
				"all'entrata di una grotta, all'esterno della quale vedi una foresta",
				exits={
					Exit('verso la foresta', {'foresta'}),
					Exit('nella grotta', {'grotta'})
					},
				tags={'grotta', 'foresta', 'uscita'},
			),
			Place(
				"all'entrata di una grotta, all'esterno della quale vedi il versante di una montagna",
				exits={
					Exit('verso la montagna', {'montagna'}),
					Exit('nella grotta', {'grotta'})
					},
				tags={'grotta', 'montagna', 'uscita'},
			),
			Place(
				"all'entrata di una grotta, all'esterno della quale vedi un bellissimo lago",
				exits={
					Exit('verso il lago', {'lago'}),
					Exit('nella grotta', {'grotta'})
					},
				tags={'grotta', 'lago', 'uscita'},
			),
			Place(
				"in una grotta che scende rapidamente, accompagnata da qualche piccolo rivolo d'acqua",
				exits={
					Exit('verso la grotta che scende', {'grotta'}),
					Exit('verso la grotta che sale', {'grotta'}),
					},
				tags={'grotta'}
			),
			Place(
				"al centro di un'intersezione fra varie grotte",
				exits={
					Exit('verso la grotta che scende', {'grotta'}),
					Exit('verso la grotta da cui senti un rumore d\'acqua', {'grotta', 'acqua'}),
					Exit('verso la grotta che prosegue orizzontalmente', {'grotta'})
					},
				tags={'grotta'}
			),
			Place(
				"in una grotta che diventa troppo verticale per essere percorsa, alla fine della quale vedi un'uscita irraggingibile",
				exits={
					Exit('indietro', {'grotta'}),
					},
				tags={'grotta'}
			),
			Place(
				"in una grotta che sembra avvicinarsi alla luce",
				exits={
					Exit('verso l\'uscita', {'grotta', 'uscita'}),
					Exit('verso le profondità della grotta', {'grotta'}),
					},
				tags={'grotta'}
			),
			Place(
				"in una grotta che termina in una grande pozza d'acqua",
				exits={
					Exit('indietro', {'grotta'})
					},
				tags={'grotta', 'acqua'},
				actions=[Action('Bevi',
					EventMessages(
						subject='bevi un po\' d\'acqua',
						close="{subject} beve un po' d'acqua"),
					lambda player: setattr(player, 'thirst', player.thirst-40),
					2.5, 0,)]
			),
			# *-* Montagna *-*
			Place(
				"in una stradina in mezzo a un prato sul versante di una montagna",
				exits={
					Exit('a valle', {'montagna'}),
					Exit('a monte', {'montagna'})
					},
				tags = {'montagna', 'mora'},
				contained=ObjectGroup([Food(Description('mora', 'more', 'mora', 'more', '','una', 'la', 'le', 'delle'), nutrition=5)]*5)
			),
			Place(
				"in una stradina tra le rocce sul versante di una montagna",
				exits={
					Exit('a valle', {'montagna'}),
					Exit('a monte', {'montagna'})
					},
				tags = {'montagna'}
			),
			Place(
				"in una stradina tra le rocce sul versante di una montagna",
				exits={
					Exit('a valle', {'montagna'}),
					Exit('a monte', {'montagna'})
					},
				tags = {'montagna'}
			),
			Place(
				"in una stradina davanti a un monastero sul versante di una montagna",
				exits={
					Exit('a valle', {'montagna'}),
					Exit('a monte', {'montagna'}),
					Exit('l\'interno del monastero', {'entrata', 'monastero'}),
					},
				tags = {'montagna'}
			),
			Place(
				"in una stradina sul versante di una montagna che termina in un lago",
				exits={
					Exit('verso il lago', {'lago'}),
					Exit('verso la cima della montagna', {'montagna'})
					},
				tags={'montagna', 'piedi', 'lago'}
			),
			Place(
				"in una stradina sul versante di una montagna che termina in una foresta",
				exits={
					Exit('verso la foresta', {'foresta'}),
					Exit('verso la cima della montagna', {'montagna'})
					},
				tags={'montagna', 'foresta'}
			),
			# *-* Lago *-*
			Place(
				"sulla riva del lago ai piedi di una montagna nel mezzo del quale vedi un relitto",
				exits={
					Exit('verso la montagna', {'montagna', 'piedi', 'lago'}),
					Exit('lungo il lago in senso orario', {'lago'}),
					Exit('lungo il lago in senso antiorario', {'lago'}),
					},
				tags={'lago'},
				contained=ObjectGroup([Weapon(
					description=Description('pugnale arrugginito', 'pugnali arrugginiti', 'pugnale', 'pugnali', 'probabilmente portato dal relitto alla spiaggia grazie alle onde','un', 'il', 'i', 'dei'),
					attacks=[
						Attack(
							'Taglia il braccio di {target} con il pugnale',
							lambda char, target: Wounds.TaglioBraccia.affect(target),
							EventMessages(
								subject='cerchi di pugnalare {subject}',
								object='{subject} cerca di pugnalarti',
								close='{subject} cerca di pugnalare {object}',
								far='distante, {subject} cerca di pugnalare {object}'
								),
							EventMessages(
								subject='fai un taglio sul braccio',
								object='fa un taglio sul tuo braccio',
								close='fa un taglio sul braccio',
								far='fa un taglio sul braccio'
								),
							EventMessages(
								subject='manchi',
								object='ti manca',
								close='manca',
								far='manca'
								),
							{'arretra', 'devia'},
							difficulty=30
							),
						Attack(
							'Pugnala {target} al petto',
							lambda char, target: Wounds.TaglioBusto.affect(target),
							EventMessages(
								subject='cerchi di pugnalare {subject}',
								object='{subject} cerca di pugnalarti',
								close='{subject} cerca di pugnalare {object}',
								far='distante, {subject} cerca di pugnalare {object}'
								),
							EventMessages(
								subject='fai un taglio sul petto',
								object='fa un taglio sul tuo petto',
								close='fa un taglio sul petto',
								far='fa un taglio sul braccio'
								),
							tags={'arretra', 'devia'},
							difficulty=35
							)
						],
					defenses=[Defense(
						'Devia con il pugnale',
						{'devia'}, 15,
						success_event = EventMessages(
							subject='riesci a deviare il colpo',
							object='{subject} devia il colpo con il pugnale',
							close='{subject} devia il colpo con il pugnale'),
						fail_event = EventMessages(
							subject='non riesci a deviare il colpo',
							object='{subject} prova a deviare il colpo con il pugnale ma fallisce',
							close='{subject} prova a deviare il colpo con il pugnale ma fallisce'),
						reply=[
							Attack(
								'Pugnala da vicino',
								lambda char, target: Wounds.TaglioBusto.affect(target),
								EventMessages(
									subject='cerchi di pugnalare {subject}',
									object='ora vicino, {subject} cerca di pugnalarti',
									close='{subject} cerca di pugnalare {object}',
									far='distante, {subject} cerca di pugnalare {object}'
									),
								EventMessages(
									subject='fai un taglio profondo',
									object='fa un taglio profondo',
									close='fa un taglio profondo',
									far='fa un taglio profondo'
									),
								tags={'arretra', 'devia'},
								difficulty=50
								),
								Dodge('Allontanati')
							]
						)]
					)])
			),
			Place(
				"sulla riva del lago vicino a un precipizio nel mezzo del quale vedi un relitto",
				exits={
					Exit('verso il precipizio', {'bordo', 'lago'}),
					Exit('lungo il lago in senso orario', {'lago'}),
					Exit('lungo il lago in senso antiorario', {'lago'}),
					},
				tags={'lago'},
				contained=ObjectGroup([Weapon(
					description=Description('scudo arrugginito', 'scudi arrugginiti', 'scudo', 'scudi', 'probabilmente portato dal relitto alla spiaggia grazie alle onde','uno', 'lo', 'gli', 'degli'),
					defenses=[Defense(
						'Blocca con la scudo',
						{'devia'}, 40,
						success_event = EventMessages(
							subject='riesci a bloccare il colpo',
							object='{subject} blocca il colpo con lo scudo',
							close='{subject} blocca il colpo con lo scudo'),
						fail_event = EventMessages(
							subject='non riesci a deviare il colpo',
							object='{subject} prova a deviare il colpo con lo scudo ma fallisce',
							close='{subject} prova a deviare il colpo con lo scudo ma fallisce')
						)]
					)])
			),
			Place(
				"sulla riva del lago vicino a una foresta nel mezzo del quale vedi un relitto",
				exits={
					Exit('verso la foresta', {'foresta', 'lago'}),
					Exit('lungo il lago in senso orario', {'lago'}),
					Exit('lungo il lago in senso antiorario', {'lago'}),
					},
				tags={'lago'}
			),
			Place(
				"sulla riva del lago al centro del quale, collegato da una passerella, vedi un relitto",
				exits={
					Exit('sulla passerella', {'passerella'}),
					Exit('lungo il lago in senso orario', {'lago'}),
					Exit('lungo il lago in senso antiorario', {'lago'}),
					},
				tags={'lago'}
			),
			Place(
				"sulla passerella che collega spiaggia e relitto",
				exits={
					Exit('verso il relitto', {'relitto'}),
					Exit('verso la spiaggia', {'lago'}),
					},
				tags={'passerella'}
			),
			Place(
				"sei a bordo di un relitto",
				exits={
					Exit('verso la spiaggia', {'passerella'}),
					},
				tags={'relitto'},
				contained=ObjectGroup([Weapon(
					description=Description('scudo arrugginito', 'scudi arrugginiti', 'scudo', 'scudi', '','uno', 'lo', 'gli', 'degli'),
					defenses=[Defense(
						'Blocca con la scudo',
						{'devia'}, 15,
						success_event = EventMessages(
							subject='riesci a bloccare il colpo',
							object='{subject} blocca il colpo con lo scudo',
							close='{subject} blocca il colpo con lo scudo'),
						fail_event = EventMessages(
							subject='non riesci a deviare il colpo',
							object='{subject} prova a deviare il colpo con lo scudo ma fallisce',
							close='{subject} prova a deviare il colpo con lo scudo ma fallisce')
						)]
					) for i in range(5)]+[Weapon(
					description=Description('pugnale arrugginito', 'pugnali arrugginiti', 'pugnale', 'pugnali', '','un', 'il', 'i', 'dei'),
					attacks=[
						Attack(
							'Taglia il braccio di {target} con il pugnale',
							lambda char, target: Wounds.TaglioBraccia.affect(target),
							EventMessages(
								subject='cerchi di pugnalare {subject}',
								object='{subject} cerca di pugnalarti',
								close='{subject} cerca di pugnalare {object}',
								far='{subject} cerca di pugnalare {object}'
								),
							EventMessages(
								subject='fai un taglio sul braccio',
								object='fa un taglio sul tuo braccio',
								close='fa un taglio sul braccio',
								far='fa un taglio sul braccio'
								),
							EventMessages(
								subject='manchi',
								object='ti manca',
								close='manca',
								far='manca'
								),
							{'arretra', 'devia'},
							difficulty=30
							),
						Attack(
							'Pugnala {target} al petto',
							lambda char, target: Wounds.TaglioBusto.affect(target),
							EventMessages(
								subject='cerchi di pugnalare {subject}',
								object='{subject} cerca di pugnalarti',
								close='{subject} cerca di pugnalare {object}',
								far='{subject} cerca di pugnalare {object}'
								),
							EventMessages(
								subject='fai un taglio sul petto',
								object='fa un taglio sul tuo petto',
								close='fa un taglio sul petto',
								far='fa un taglio sul braccio'
								),
							tags={'arretra', 'devia'},
							difficulty=35
							)
						],
					defenses=[Defense(
						'Devia con il pugnale',
						{'devia'}, 15,
						success_event = EventMessages(
							subject='riesci a deviare il colpo',
							object='{subject} devia il colpo con il pugnale',
							close='{subject} devia il colpo con il pugnale'),
						fail_event = EventMessages(
							subject='non riesci a deviare il colpo',
							object='{subject} prova a deviare il colpo con il pugnale ma fallisce',
							close='{subject} prova a deviare il colpo con il pugnale ma fallisce'),
						reply=[
							Attack(
								'Pugnala da vicino',
								lambda char, target: Wounds.TaglioBusto.affect(target),
								EventMessages(
									subject='cerchi di pugnalare {subject}',
									object='ora vicino, {subject} cerca di pugnalarti',
									close='{subject} cerca di pugnalare {object}',
									far='{subject} cerca di pugnalare {object}'
									),
								EventMessages(
									subject='fai un taglio profondo',
									object='fa un taglio profondo',
									close='fa un taglio profondo',
									far='fa un taglio profondo'
									),
								tags={'arretra', 'devia'},
								difficulty=50
								),
								Dodge('Allontanati')
							]
						)]
					) for i in range(15)]+[Object(Description('moneta d\'oro', 'monete d\'oro', 'moneta', 'monete', '', 'una', 'la', 'le', 'delle')) for i in range(15)])
			),
			# *-* FORESTA *-*
			Place(
				"al centro di una enorme foresta",
				exits={
					Exit('verso quello che sembra essere un gigantesco albero', {'foresta', 'bigtree'}),
					Exit('verso quella che sembra essere una radura', {'foresta', 'radura'}),
					Exit('verso quella che sembra essere una montagna', {'foresta', 'montagna'})
					},
				tags={'foresta'},
			),
			Place(
				"al centro di una enorme foresta",
				exits={
					Exit('verso quello che sembra essere un gigantesco albero', {'foresta', 'bigtree'}),
					Exit('verso quella che sembra essere una radura', {'foresta', 'radura'}),
					Exit('verso quella che sembra essere una montagna', {'foresta', 'montagna'})
					},
				tags={'foresta', 'lago'},
			),
			Place(
				"in una stradina al centro di una foresta che sembra diradarsi",
				exits={
					Exit('verso la foresta più diradata', {'foresta'}),
					Exit('verso la foresta più fitta', {'foresta'}),
					},
				tags={'foresta'},
			),
			Place(
				"al centro di una radura piena di cespugli",
				exits={
					Exit('verso un percorso da cui senti un rumore d\'acqua', {'foresta', 'acqua'}),
					Exit('verso una parte particolarmente fitta della foresta', {'foresta'}),
					Exit('verso una stradina in salito nella foresta', {'foresta'})
					},
				tags={'foresta', 'radura'},
				contained=ObjectGroup([Food(Description('mora', 'more', 'mora', 'more', '','una', 'la', 'le', 'delle'), nutrition=5)]*5)
			),
			Place(
				"al centro di una foresta tenebrosa",
				exits={
					Exit('verso un percorso in cui la foresta sembra diradarsi', {'foresta', 'radura'}),
					Exit('verso una parte particolarmente fitta della foresta', {'foresta'}),
					Exit('verso qualcosa che sembra essere uno specchio d\'acqua', {'foresta', 'lago'})
					},
				tags={'foresta', 'bigtree'},
				contained=ObjectGroup([Object(Description('albero maestoso', 'alberi maestosi', 'albero', 'alberi', 'che dalla dimensione ha probabilmente centinaia di anni','un', 'l\'', 'gli', 'degli'), visible=True)])
			),
			Place(
				"ai piedi di un piccolo ruscello al centro di una foresta gigantesca",
				exits={
					Exit('indietro', {'foresta'})
					},
				tags={'foresta', 'acqua'},
				actions=[Action('Bevi',
					EventMessages(
						subject='bevi un po\' d\'acqua',
						close="{subject} beve un po' d'acqua"),
					lambda player: setattr(player, 'thirst', player.thirst-40),
					2.5, 0,)]
			),
			Place(
				"davanti a un monastero eretto al centro di una foresta",
				exits={
					Exit('verso la foresta', {'foresta'}),
					Exit('dentro al monastero', {'monastero', 'entrata'})
					},
				tags={'foresta'}
			),
			# *-* Monastero *-*
			Place(
				"all'entrata di uno scuro monastero che sembra avere più di mille anni",
				exits={
					Exit('l\'uscita', {'foresta'}),
					Exit('un grande portone che sembra condurre alla stanza principale', {'monastero', 'stanza principale'}),
					Exit('al secondo piano, tramite una lunga gradinata di marmo', {'monastero', 'secondo piano'}),
					},
				tags={'monastero', 'entrata'}
			),
			Place(
				"all'entrata di uno scuro monastero che sembra avere più di mille anni",
				exits={
					Exit('l\'uscita', {'montagna'}),
					Exit('un grande portone che sembra condurre alla stanza principale', {'monastero', 'stanza principale'}),
					Exit('al secondo piano, tramite una lunga gradinata di marmo', {'monastero', 'secondo piano'}),
					},
				tags={'monastero', 'entrata'}
			),
			Place(
				"al secondo piano del monastero",
				exits={
					Exit('al primo piano', {'monastero', 'entrata'}),
					Exit('in uno sgabuzzino laterale', {'monastero', 'sgabuzzino'}),
					Exit('al terzo piano, tramite una lunga gradinata di marmo', {'monastero', 'terzo piano'}),
					},
				tags={'monastero', 'secondo piano'}
			),
			Place(
				"al terzo piano del monastero",
				exits={
					Exit('in uno stanzino con dei mobili molto curati', {'monastero', 'stanzino'}),
					Exit('al secondo piano', {'monastero', 'secondo piano'}),
					},
				tags={'monastero', 'terzo piano'}
			),
			Place(
				"nella stanza principale del monastero, con decine di panchine per la preghiera",
				exits={
					Exit('verso l\'entrata del monastero', {'monastero', 'entrata'})
					},
				tags={'monastero', 'stanza principale'}
			),
			Place(
				"in uno sgabuzzino che capisci essere una semplice infermeria",
				exits={
					Exit('indietro', {'monastero', 'secondo piano'})
					},
				tags={'monastero', 'sgabuzzino'},
				contained=ObjectGroup(
					[HealWound(
						Description('cerotto', 'cerotti', 'cerotto', 'cerotti', 'per ferite piccole'),
						wound=Wounds.TaglioBraccia
					) for i in range(2)]+
					[HealWound(
						Description('fascia emostatica', 'fascie emostatiche', 'fascia', 'fascie', 'per ferite grandi','una', 'la', 'le', 'delle'),
						wound=Wounds.TaglioBusto
					) for i in range(2)]+
					[HealWound(
						Description('stecca', 'stecche', 'stecca', 'stecche', 'per gambe rotte','una', 'la', 'le', 'delle'),
						wound=Wounds.Frattura
					) for i in range(2)]+
					[Food(Description('cioccolata', 'cioccolata', 'cioccolata', 'cioccolata', 'per recuperare le energie','della', 'la', 'la', 'della')) for i in range(2)]
					)
			),
			Place(
				"in una stanza che capisci essere la cucina",
				exits={
					Exit('indietro', {'monastero', 'secondo piano'})
					},
				tags={'monastero', 'sgabuzzino'},
				contained=ObjectGroup(
					[Food(Description('mela', 'mele', 'mela', 'mele', '','una', 'la', 'le', 'delle'), nutrition=10) for i in range(10)]+
					[Food(Description('pane', 'pane', 'pane', 'pane', '','del', 'il', 'il', 'del'), nutrition=10) for i in range(10)]+
					[Backpack(Description('zaino', 'zaini', 'zaino', 'zaini', '','uno', 'lo', 'gli', 'degli'), volume=30) for i in range(10)])
			),
		}
	)


veggero = Character(
	description=Description('ragazzo carino', 'ragazzi carini', 'ragazzo', 'ragazzi')
	)

nicole = Character(
	description=Description('ragazza carina', 'ragazze carine', 'ragazza', 'ragazze', '','una', 'la', 'le', 'delle')
	)

#world.spawn(veggero)
for place in world.places:
	if place.tags == {'grotta', 'acqua'}:
		world.spawn(veggero, place)
		break
	if place.tags == {'monastero', 'stanza principale'}:
		for i in range(15):
			world.spawn(
				Character(
					strenght=10, agility=60,
					description=Description('monaco', 'monaci', 'monaco', 'monaci', '', 'un', 'il', 'i', 'dei')
					),
				place)
	if place.tags == {'relitto'}:
		for i in range(15):
			world.spawn(
				Character(
					strenght=100, agility=80,
					description=Description('pirata', 'pirati', 'pirata', 'pirati', '', 'un', 'il', 'i', 'dei')
					),
				place)
world.spawn(nicole, veggero.place)

Telegram('508857997:AAGYf6PS09WSZ_mjlOlooj-YtIU4fPlYijs', world, {302001216: veggero})
#302001216: veggero
#186405135: nicole
#1229891893: veggero2
