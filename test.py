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
		"Canyon": {
			"chances": 5,
			"descriptions": [
				"Un enorme canyon di terra rossa",
				"Un piccolo canyon"
			],
			"exits": {
				"Grotta-outer": [
					"in un buco nella roccia",
					"in una fessura"
				],
				"Foresta-outer": [
					"verso degli alberi",
					"verso la vegetazione"
				]
			},
			"variants": {
				"sassi": {
					"contained": ObjectGroup([
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
				},
				"attacks": {
					"attacks": [spingi_precipizio := Attack(
						'Spingi {target} giù per il precipizio',
						lambda player, target: (setattr(target, 'state', States.Lying) or 
												Wounds.Frattura.affect(target) or
												target.move_to(target.place.get_exit('canyon'))),
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
				}
			}
		},

		"Grotta-outer": {
			"chances": 5,
			"descriptions": [
				"Una piccola entrata per una grotta",
				"L'entrata di una vecchia grotta, forse una miniera"
			],
			"exits": {
				"Canyon": [
					"verso delle rocce enormi",
					"verso della terra rossa"
				],
				"Grotta-inner": [
					"dentro alla grotta",
					"all'interno della grotta"
				],
				"Montagna-outer": [
					"in un sentiero di montagna",
					"verso un sentierino"
				],
				"Foresta-inner": [
					"verso una distesa di alberi enorme",
					"verso degli alberi fittissimi"
				]
			},
			"variants": {}
		},

		"Grotta-inner": {
			"chances": 5,
			"descriptions": [
				"Una grotta enorme, ma molto buia",
				"Una piccola grotta di cui si vedono bene le uscite"
			],
			"exits": {
				"Grotta-outer": [
					"verso un uscita",
					"verso la luce"
				],
				"Grotta-inner": [
					"verso il tunnel a destra",
					"verso il tunnel a sinistra"
				]
			},
			"variants": {
				"acqua": {
					"actions": [Action('Bevi',
						EventMessages(
							subject='bevi un po\' d\'acqua',
							close="{subject} beve un po' d'acqua"),
						lambda player: setattr(player, 'thirst', player.thirst-40),
						2.5, 0,)
					]
				}
			}
		},

		"Montagna-outer": {
			"chances": 5,
			"descriptions": [
				"Un sentiero di montagna",
				"Un piccolo sentierino, attraversato da molti animali"
			],
			"exits": {
				"Grotta-outer": [
					"verso l'entrata di una grotta",
					"in quella che sembra essere una grotta"
				],
				"Montagna-inner": [
					"verso la strada del sentiero",
					"verso la cima"
				],
				"Lago-outer": [
					"verso la riva di un lago",
					"verso uno specchio di luce"
				],
				"Monastero-outer": [
					"all'entrata di un monastero",
					"alla porta di uno strano edificio"
				]
			},
			"variants": {
				"more": {
					"contained": ObjectGroup([Food(Description('mora', 'more', 'mora', 'more', '','una', 'la', 'le', 'delle'), nutrition=5)]*5)
				}
			}
		},

		"Montagna-inner": {
			"chances": 5,
			"descriptions": [
				"La cima di una montagna perennemente innevata",
				"La cima della montagna, da cui si vede il mare"
			],
			"exits": {
				"Montagna-outer": [
					"verso un sentiero di montagna",
					"in un altro sentiero"
				]
			},
			"variants": {}
		},

		"Lago-outer": {
			"chances": 5,
			"descriptions": [
				"La riva di un lago enorme",
				"La riva di un lago pieno di oche"
			],
			"exits": {
				"Montagna-outer": [
					"in un sentiero di montagna",
					"verso un sentiero"
				],
				"Lago-inner": [
					"in un sentiero che passa attraverso il lago",
					"in un sentiero"
				],
				"Foresta-outer": [
					"verso degli alberi",
					"verso un'immensa distesa di alberi"
				]
			},
			"variants": {}
		},

		"Lago-inner": {
			"chances": 5,
			"descriptions": [
				"Un sentierino che taglia a metà il lago",
				"Una stradina sul bordo del lago"
			],
			"exits": {
				"Lago-outer": [
					"verso la riva del lago",
					"alla fine del sentiero"
				]
			},
			"variants": {
				"pugnale": {
					"contained": ObjectGroup([Weapon(
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
				},

				"scudo": {
					"contained": ObjectGroup([Weapon(
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
				},

				"relitto": {
					"contained": ObjectGroup([Weapon(
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
				}
			}
		},

		"Foresta-outer": {
			"chances": 5,
			"descriptions": [
				"Un percorso circondato da alberi. Sembra l'entrata di una foresta",
				"Un sentiero che sembra finire in una foresta"
			],
			"exits": {
				"Canyon": [
					"verso le rocce di un canyon",
					"verso un canyon di terra rossa"
				],
				"Lago-outer": [
					"verso la riva di un lago lucente",
					"verso uno specchio d'acqua"
				],
				"Foresta-inner": [
					"al centro della foresta",
					"in una parte di foresta ancora più fitta"
				]
			},
			"variants": {}
		},

		"Foresta-inner": {
			"chances": 5,
			"descriptions": [
				"Una foresta fittissima",
				"Una foresta che sembra aver ospitato un'antica civiltà"
			],
			"exits": {
				"Grotta-outer": [
					"verso una grotta",
					"verso quella che sembra una miniera abbandonata"
				],
				"Foresta-inner": [
					"dove gli alberi sembrano meno fitti",
					"dove la foresta sembra diradarsi"
				],
				"Monastero-outer": [
					"all'entrata di un monastero abbandonato",
					"davanti alla porta di un palazzo antico"
				],
				"Foresta-outer": [
					"verso dove gli alberi sembrano diradarsi",
					"verso un sentierino"
				]
			},
			"variants": {
				"more": {
					"contained": ObjectGroup([Food(Description('mora', 'more', 'mora', 'more', '','una', 'la', 'le', 'delle'), nutrition=5)]*5)
				},

				"albero": {
					"contained": ObjectGroup([Object(Description('albero maestoso', 'alberi maestosi', 'albero', 'alberi', 'che dalla dimensione ha probabilmente centinaia di anni','un', 'l\'', 'gli', 'degli'), visible=True)])
				},

				"acqua": {
					"actions": [Action('Bevi',
						EventMessages(
							subject='bevi un po\' d\'acqua',
							close="{subject} beve un po' d'acqua"),
						lambda player: setattr(player, 'thirst', player.thirst-40),
						2.5, 0,)
					]
				},
			}
		},

		"Monastero-outer": {
			"chances": 5,
			"descriptions": [
				"L'entrata di un antico monastero",
				"Una porta di quello che sembra un monastero abbandonato"
			],
			"exits": {
				"Montagna-outer": [
					"verso il sentiero da cui sei arrivato",
					"al sentiero di prima"
				],
				"Foresta-inner": [
					"verso la foresta",
					"alla foresta"
				],
				"Monastero-inner-1": [
					"dentro il monastero",
					"all'interno del palazzo"
				]
			},
			"variants": {}
		},

		"Monastero-inner-1": {
			"chances": 5,
			"descriptions": [
				"Il piano terra del monastero. Non sembra esserci nessuno",
				"Un atrio con due rampe di scale"
			],
			"exits": {
				"Monastero-outer": [
					"all'aperto",
					"all'esterno del monastero"
				],
				"Monastero-inner-2": [
					"verso il piano di sopra",
					"di sopra"
				]
			},
			"variants": {}
		},

		"Monastero-inner-2": {
			"chances": 5,
			"descriptions": [
				"Il primo piano del monastero. Si vedono dei letti",
				"Probabilmente la vecchia mensa del monastero"
			],
			"exits": {
				"Monastero-inner-1": [
					"da dove sei arrivato",
					"verso le scale che tornano giù"
				],
				"Monastero-inner-3": [
					"verso il piano superiore",
					"di sopra"
				]
			},
			"variants": {
				"infermeria": {
					"contained": ObjectGroup(
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
				},
				"cucina": {
					"contained": ObjectGroup(
						[Food(Description('mela', 'mele', 'mela', 'mele', '','una', 'la', 'le', 'delle'), nutrition=10) for i in range(10)]+
						[Food(Description('pane', 'pane', 'pane', 'pane', '','del', 'il', 'il', 'del'), nutrition=10) for i in range(10)]+
						[Backpack(Description('zaino', 'zaini', 'zaino', 'zaini', '','uno', 'lo', 'gli', 'degli'), volume=30) for i in range(10)]
					)
				},
			}
		},

		"Monastero-inner-3": {
			"chances": 1,
			"descriptions": [
				"L'ultimo piano del monastero. C'è un balcone, ma è sbarrato",
				"Il terzo piano. Ci sono dei quadri rovinati appesi alle pareti"
			],
			"exits": {
				"Monastero-inner-2": [
					"da dove sei venuto, non c'è nessun altra porta."
				]
			},
			"variants": {}
		}
	},
	world_size=10
)

veggero = Character(
	description=Description('ragazzo carino', 'ragazzi carini', 'ragazzo', 'ragazzi')
)

nicole = Character(
	description=Description('ragazza carina', 'ragazze carine', 'ragazza', 'ragazze', '','una', 'la', 'le', 'delle')
)

world.spawn(veggero, world.places[0])
world.spawn(nicole, world.places[0])

Telegram('508857997:AAGYf6PS09WSZ_mjlOlooj-YtIU4fPlYijs', world, {302001216: veggero})
#302001216: veggero
#186405135: nicole
#1229891893: veggero2
