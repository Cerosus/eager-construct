from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import BaseFilter
from telegram import InputMediaPhoto

import requests


## Tentative Code for card call ~~~~~~~~~~~~~~~~~~~~

class StartBrackets(BaseFilter):
    def filter(self, message):
        return '[[' in message.text

class EndBrackets(BaseFilter):
    def filter(self, message):
        return ']]' in message.text

# Initialize the classes
start_brackets = StartBrackets()
end_brackets = EndBrackets()

def name_filter(text):
    array1 = []
    array2 = []
    i = 0
    j = 0
    t1 = text
    t2 = text
    while 1:
        i = t1.find('[[',i)
        if i == -1:
            break
        array1.append([i,'s'])
        i = i + 1
    while 1:
        j = t2.find(']]',j)
        if j == -1:
            break
        array1.append([j,'e'])
        j = j + 1
    array1.sort()
    
    for i in range(0,len(array1)-1):
        x = array1[i][1]
        y = array1[i+1][1]
        if array1[i][1] == 's' and array1[i+1][1] == 'e':
            name = text[array1[i][0]+2:array1[i+1][0]]
            array2.append(name)
    print(array2)
    return array2

def scryfall(list1):
    album = []
    errors = []
    for name in list1:
        data = requests.get('https://api.scryfall.com/cards/search?q=!'+name)
        if data.json()['object'] == "error":
            data = requests.get('https://api.scryfall.com/cards/search?q='+name)
        if data.json()['object'] == "error":
            errors.append(name)
            continue
        result1 = data.json()['data'][0]
        print(result1['layout'])
    
        if result1['layout'] == "meld":
            related_cards = result1['all_parts']
            name1 = related_cards[0]['name']
            name2 = related_cards[1]['name']
            name3 = related_cards[2]['name']
            link1 = related_cards[0]['uri']
            page1 = requests.get(link1)
            image1 = page1.json()['image_uris']['normal']
            link2 = related_cards[1]['uri']
            page2 = requests.get(link2)
            image2 = page2.json()['image_uris']['normal']
            link3 = related_cards[2]['uri']
            page3 = requests.get(link3)
            image3 = page3.json()['image_uris']['normal']
            print(image1)
            print(image2)
            print(image3)
            album.append(InputMediaPhoto(image1, caption = name1))
            album.append(InputMediaPhoto(image2, caption = name2))
            album.append(InputMediaPhoto(image3, caption = name3))
            #bot.send_photo(chat_id=chatid, photo = image1, caption = name1)
            #bot.send_photo(chat_id=chatid, photo = image2, caption = name2)
        elif result1['layout'] == "transform":
            faces = result1['card_faces']
            name1 = faces[0]['name']
            name2 = faces[1]['name']
            image1 = faces[0]['image_uris']['normal']
            image2 = faces[1]['image_uris']['normal']
            print(image1)
            print(image2)
            album.append(InputMediaPhoto(image1, caption = name1))
            album.append(InputMediaPhoto(image2, caption = name2))
        else:
            image = result1['image_uris']['normal']
            name = result1['name']
            print(name)
            print(image)
            #album.append(['photo',image,name])
            album.append(InputMediaPhoto(image, caption = name))
            #bot.send_photo(chat_id=chatid, photo = image, caption = name)
    return [album, errors]

def card_image_search(bot, update):
    searches = name_filter(update.message.text)

    results = scryfall(searches)
    album = results[0]
    errors = results[1]
    print(album)
    print(errors)
    if len(errors) != 0:
        reply = "Not found: "
        for x in errors:
            update.message.reply_text(reply+x)
    bot.send_media_group(chat_id = update.message.chat_id, media = album)
    print("done")
    
## End of Tentative Code ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def start(bot, update):
  update.message.reply_text("Search for a Magic card via Scryfall's databse and post the image of the first match to chat.\n\nThis bot is under development and will usually be unavailable.\nI am currently working on deploying it to a server.")

def bot_help(bot, update):
  bot.send_message(chat_id = update.message.chat_id, text = "Help:\nSearch for a card by enclosing its name with [[ ]] in your message.\nExample: [[Brago]]\nYou can also search for other characteristics with Scryfall's search syntax (https://scryfall.com/docs/reference).\nExample: [[o:\"exile all creatures\"]]")
  
def main():
  # Create Updater object and attach dispatcher to it
  updater = Updater('460338069:AAFi4h7SydFGFg7mO5fzDkBKk4uZWvPP-yU')
  dispatcher = updater.dispatcher
  print("Bot started")

  # Add command handler to dispatcher
  start_handler = CommandHandler('start', start)
  help_handler = CommandHandler('help', bot_help)
  card_handler = MessageHandler((start_brackets & end_brackets), card_image_search)
  dispatcher.add_handler(start_handler)
  dispatcher.add_handler(card_handler)
  dispatcher.add_handler(help_handler)
  
  
  # Start the bot
  updater.start_polling()

  # Run the bot until you press Ctrl-C
  updater.idle()

if __name__ == '__main__':
    main()
