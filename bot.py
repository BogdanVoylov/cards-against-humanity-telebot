import random
import threading
import time
import json

import telebot


last_message = {}
game_password = {}
game_numOfRounds = {}
game_chatId = {}
game_admin = {}
game_cards = {}
chatId_score = {}
chatId_userName = {}
wcards = []
bcards = []
bot = telebot.TeleBot('910878205:AAEFZrgTK5bwUEv8BrX0-fW0aweJ86sgzbw')

@bot.message_handler(commands=['start', 'help'])
def start(message):
    chatId = message.chat.id
    if chatId in last_message:
        num_of_players = 0
        if chatId in game_chatId:
            num_of_players = len(game_chatId[last_message[chatId]])
            game_chatId[last_message[chatId]].remove(chatId)

        if num_of_players == 1:
            del game_password[last_message[chatId]]
            del game_chatId[last_message[chatId]]

        del chatId_score[chatId]
        del last_message[chatId]

    chatId_userName[chatId] = message.from_user.username
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Create new  game', 'Connect to existing game')
    msg = bot.send_message(chatId, "You were moved to start. Choose the option", reply_markup=keyboard)
    bot.register_next_step_handler(msg, game_handler)


@bot.message_handler(content_types=['text'])
def game_handler(message):
    if message.text == "Create new  game":
        msg = bot.reply_to(message, "Set game name")
        bot.register_next_step_handler(msg, set_password)

    elif message.text == "Connect to existing game":
        msg = bot.reply_to(message, "Enter game name")
        bot.register_next_step_handler(msg, check_game_name)


@bot.message_handler(content_types=['text'])
def check_game_name(message):
    if message.text in game_password:
        last_message[message.chat.id] = message.text
        msg = bot.reply_to(message, "Enter password")
        bot.register_next_step_handler(msg, check_password)
    else:
        msg = bot.reply_to(message, "Wrong game name")
        bot.register_next_step_handler(msg, start)


@bot.message_handler(content_types=['text'])
def check_password(message):
    if game_password[last_message[message.chat.id]] == message.text:
        if last_message[message.chat.id] in game_chatId:
            game_chatId[last_message[message.chat.id]].append(message.chat.id)
        else:
            game_chatId[last_message[message.chat.id]] = [message.chat.id]
        chatId_score[message.chat.id] = 0
        bot.send_message(message.chat.id, "Connected to the game")
    else:
        msg = bot.reply_to(message, "Wrong password")
        bot.register_next_step_handler(msg, start)


@bot.message_handler(content_types=['text'])
def set_password(message):
    games = game_password.keys()
    if message.text in games:
        msg = bot.reply_to(message, "game with such name is already created")
        bot.register_next_step_handler(msg, start)
    else:
        last_message[message.chat.id] = message.text
        msg = bot.reply_to(message, "Enter password")
        bot.register_next_step_handler(msg, add_game)


@bot.message_handler(content_types=['text'])
def add_game(message):
    game_password[last_message[message.chat.id]] = message.text
    game_chatId[last_message[message.chat.id]] = []
    game_chatId[last_message[message.chat.id]].append(message.chat.id)
    chatId_score[message.chat.id] = 0
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Set the number of rounds', 'Leave')
    msg = bot.reply_to(message,
                       "Choose the option (you should start the game when all people you need are connected)",
                       reply_markup=keyboard)
    bot.register_next_step_handler(msg, start_game)


@bot.message_handler(content_types=['text'])
def start_game(message):
    if message.text == 'Set the number of rounds':
        msg = bot.reply_to(message, 'Enter number of rounds')
        bot.register_next_step_handler(msg, get_num_of_rounds)
    else:
        del game_password[last_message[message.chat.id]]
        del game_chatId[last_message[message.chat.id]]
        msg = bot.send_message(message.chat.id,'You were moved to waiting mod. Send any message and you will be moved to start')
        bot.register_next_step_handler(msg, start)


@bot.message_handler(content_types=['text'])
def get_num_of_rounds(message):
    game_numOfRounds[last_message[message.chat.id]] = int(message.text)
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Start the game', 'Leave')
    msg = bot.reply_to(message, 'Rounds left' + str(game_numOfRounds[last_message[message.chat.id]]),
                       reply_markup=keyboard)
    bot.register_next_step_handler(msg, run_game_handler)


@bot.message_handler(content_types=['text'])
def run_game_handler(message):
    gameName = last_message[message.chat.id]
    if game_numOfRounds[last_message[message.chat.id]] > 0:
        game_numOfRounds[last_message[message.chat.id]] -= 1
        game_cards[gameName] = []
        user_list = game_chatId[gameName]

        admin = game_chatId[gameName][random.randint(0, len(game_chatId[gameName]) - 1)]
        game_admin[gameName] = admin
        sentence = bcards[random.randint(0, len(bcards) - 1)]
        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        for user in user_list:
            if user != admin:
                for i in range(1, 10):
                    keyboard.row(wcards[random.randint(0, len(wcards) - 1)])
                bot.send_message(user, "You are to choose the card")
                msg = bot.send_message(user,
                                       sentence,
                                       reply_markup=keyboard)
            else:
                bot.send_message(user, "You are to choose the winner")
                msg = bot.send_message(user,
                                       sentence)
                t1 = threading.Thread(target=send_with_delay, args=(user, 10, gameName))
                t1.start()

            bot.register_next_step_handler(msg, get_choice)
    else:
        for chatId in game_chatId[gameName]:
            msg = bot.send_message(chatId,
                                   'You were moved to waiting mod. Send any message and you will be moved to start')
            bot.register_next_step_handler(msg, start)


@bot.message_handler(content_types=['text'])
def get_choice(message):
    gameName = last_message[message.chat.id]
    if message.chat.id == game_admin[gameName]:
        for sentence in game_cards[gameName]:
            chatId_score[sentence[message.text]] += 1
        adresses = []
        chatIds = chatId_score.keys()
        object_to_send = {}
        for chatId in chatIds:
            if chatId in game_chatId[gameName]:
                adresses.append(chatId)
                object_to_send[chatId_userName[chatId]] = chatId_score[chatId]
        for adress in adresses:
            msg = bot.send_message(adress, str(json.dumps(object_to_send)))
        bot.register_next_step_handler(msg, run_game_handler)
    else:
        game_cards[gameName].append({message.text: message.chat.id})
        bot.send_message(message.chat.id, "Wait till admin will chose winner")


def send_with_delay(user, delay, gameName):
    time.sleep(delay)
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    for sentence in game_cards[gameName]:
        for text in sentence.keys():
            keyboard.row(text)
            for chatId in game_chatId[gameName]:
                bot.send_message(chatId, text)

    bot.send_message(user, "You are to choose", reply_markup=keyboard)


def read_bcards():
    f = open("cards/bcards", "r")
    string = f.read()
    string = string[10:]
    counter = 0
    i = 0
    bcards.append(" ")
    while i < len(string):
        if string[i] != '<' and string[i] != '>':
            bcards[counter] += str(string[i])
        elif string[i] == '>':
            bcards.append(" ")
            counter += 1
        i += 1

    print(bcards)


def read_wcards():
    f = open("cards/wcards", "r")
    string = f.read()
    string = string[8:]
    counter = 0
    i = 0
    wcards.append(" ")
    while i < len(string):
        if string[i] != '<' and string[i] != '>':
            wcards[counter] += str(string[i])
        elif string[i] == '>':
            wcards.append(" ")
            counter += 1

        i += 1

    print(wcards)


read_bcards()
read_wcards()  # dfbdbf
bot.delete_webhook()

bot.polling(none_stop=True)