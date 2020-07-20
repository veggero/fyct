from __future__ import annotations

from typing import Optional
from time import sleep
from random import choice
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove

class Telegram:
	
	DEBUGGING = False
	
	instance = None
	waiting_for: Optional[Character] = None
	output: str = ''
	
	def __init__(self, token, world, players={}):
		Telegram.instance = self
		self.world = world
		self.players = players
		self.bot = Bot(token)
		self.chats = {a:b for b,a in players.items()}
		updater = Updater(token=token, use_context=True)
		dispatcher = updater.dispatcher
		echo_handler = MessageHandler(Filters.text, self.receive)
		dispatcher.add_handler(echo_handler)
		updater.start_polling()
		world.tick()
	
	@run_async
	def receive(self, update, context):
		if update.effective_chat.id not in self.players:
			print(update.effective_chat.id)
			return update.message.reply_text('Non sei nel gioco.')
		player = self.players[update.effective_chat.id]
		
		# If waiting for him specifically, output and end
		if self.waiting_for is player:
			self.waiting_for = None
			self.output = update.message.text
			return
		
		# Otherwise, is it his turn?
		if not self.world.turn is player or self.waiting_for is not None:
			return update.message.reply_text('Non è il tuo turno.')
		
		# If so, select the right action
		action = next((a for a in player.current_actions if a.name == update.message.text), None)
		if action is None:
			return update.message.reply_text("Non è un'opzione, usa i bottoni.")
		action.execute(player)
	
	def ask(self, player, actions):
		# If not a player, the turn is over (AI MISSING)
		if not player in self.chats or self.DEBUGGING:
			return choice(actions).execute(player)
		player.current_actions = actions
		
		# Otherwise, ping the user and wait
		id = self.chats[player]
		actions = [a.name for a in actions]
		actions = [actions[n:n+2] for n in range(0, len(actions), 2)]
		keyboard = ReplyKeyboardMarkup(actions)
		self.bot.send_message(id, 'Cosa fai?', reply_markup=keyboard)
	
	def tick(self):
		for player in self.chats:
			if not player in self.chats or not player.events:
				continue
			self.bot.send_message(self.chats[player], f'{player.events}.', reply_markup=ReplyKeyboardRemove())
			player.events.clear()
	
	def chooseDefense(self, target, defenses, message):
		self.tick()
		if not target in self.chats or self.DEBUGGING:
			return choice(defenses)
		actions = [a.name for a in defenses]
		actions = [actions[n:n+2] for n in range(0, len(actions), 2)]
		keyboard = ReplyKeyboardMarkup(actions)
		self.bot.send_message(self.chats[target], message, reply_markup=keyboard)
		self.waiting_for = target
		while self.waiting_for: pass
		return next(defe for defe in defenses if defe.name == self.output)
