from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import BaseFilter
from telegram import InputMediaPhoto

import requests


## Code for card call ~~~~~~~~~~~~~~~~~~~~

class StartBrackets(BaseFilter):
    def filter(self, message):
        return '[[' in message.text

class EndBrackets(BaseFilter):
    def filter(self, message):
        return ']]' in message.text

class StartBraces(BaseFilter):
    def filter(self, message):
        return '{{' in message.text

class EndBraces(BaseFilter):
    def filter(self, message):
        return '}}' in message.text

# Initialize the classes
start_brackets = StartBrackets()
end_brackets = EndBrackets()
start_braces = StartBraces()
end_braces = EndBraces()


def name_filter(text,type): #Filter properly enclosed terms from message into a list
    array1 = []
    array2 = []
    i = 0
    
    if type == "bracket":
        while 1:
            pos = text.find('[[',i)
            if pos == -1: #If no more [[ found
                i = 0
                break
            array1.append([pos,'s'])
            i = pos + 1 #Ignore previous sets
        while 1:
            pos = text.find(']]',i)
            if pos == -1: #If no more ]] found
                break
            array1.append([pos,'e'])
            i = pos + 1 #Ignore previous sets
    
    if type == "brace":
        while 1:
            pos = text.find('{{',i)
            if pos == -1: #If no more {{ found
                i = 0
                break
            array1.append([pos,'s'])
            i = pos + 1 #Ignore previous sets
        while 1:
            pos = text.find('}}',i)
            if pos == -1: #If no more }} found
                break
            array1.append([pos,'e'])
            i = pos + 1 #Ignore previous sets
    
    array1.sort() #Arrange bracket groups in order of appearance
    
    for i in range(0,len(array1)-1): #Check each pair of brackets to see if it matches [[ ]]
        x = array1[i][1]
        y = array1[i+1][1]
        if x == 's' and y == 'e':
            name = text[array1[i][0]+2:array1[i+1][0]]
            array2.append(name)
    print(array2)
    return array2

def list_more(times, data, album):
    print(times)
    times = int(times)
    if times > 10:
        times = 10
    for i in range(0,times):
        if data.json()['data'][i] == 'error':
            return album
        album = get_image(data.json()['data'][i], album)
    return album
        
def scryfall(list1): #Search each bracketed term through Scryfall, obtain card images
    album = []
    errors = []
    for name in list1:
        data = requests.get('https://api.scryfall.com/cards/search?q=!'+name) #checks for exact match
        if data.json()['object'] == "error": #if no exact match, check for partial match
            data = requests.get('https://api.scryfall.com/cards/search?q='+ 'name:/\\b('+ name +')\\b/' \
                                +" t:legendary (t:creature or t:planeswalker)") #check for unique
            if data.json()['object'] == "error":
                data = requests.get('https://api.scryfall.com/cards/search?q='+'name:/^('+ name +')/') #match from start
                if data.json()['object'] == "error":
                    data = requests.get('https://api.scryfall.com/cards/search?q='+ name)

        if data.json()['object'] == "error":
            errors.append(name)
            continue
        list_op = name.find('l:')
        #print(list_op)
        if list_op != -1:
            times = name[list_op + 2 : list_op + 4]
            album = list_more(times, data, album) #find several results
        else:
            album = get_image(data.json()['data'][0], album)  #find first result

    return (album, errors)

def get_image(result,album):
    print(result['layout'])
    if result['layout'] == "meld": #Card has half-card on back, 'melds' with another
        related_cards = result['all_parts']
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
        return album
    elif result['layout'] == "transform": #Card has full card on back
        faces = result['card_faces']
        name1 = faces[0]['name']
        name2 = faces[1]['name']
        image1 = faces[0]['image_uris']['normal']
        image2 = faces[1]['image_uris']['normal']
        print(image1)
        print(image2)
        album.append(InputMediaPhoto(image1, caption = name1))
        album.append(InputMediaPhoto(image2, caption = name2))
        return album
    elif result['layout'] == "modal_dfc": #Card has full card on back
        faces = result['card_faces']
        name1 = faces[0]['name']
        name2 = faces[1]['name']
        image1 = faces[0]['image_uris']['normal']
        image2 = faces[1]['image_uris']['normal']
        print(image1)
        print(image2)
        album.append(InputMediaPhoto(image1, caption = name1))
        album.append(InputMediaPhoto(image2, caption = name2))
        return album
    else:
        image = result['image_uris']['normal']
        name = result['name']
        print(name)
        print(image)
        album.append(InputMediaPhoto(image, caption = name))
        return album

def card_image_search(update, context): #Post results in chat
    searches = name_filter(update.message.text,"bracket")

    (album, errors) = scryfall(searches)
    print(album)
    print(errors)
    if len(errors) != 0:
        reply = "Not found: "
        for x in errors:
            update.message.reply_text(reply+x)
    while len(album) > 10:
        context.bot.send_media_group(chat_id = update.message.chat_id, media = album[0:10])
        album = album[10:]
    context.bot.send_media_group(chat_id = update.message.chat_id, media = album)
    print("done")
    
def card_oracle_search(update, context): #Post results in chat
    searches = name_filter(update.message.text,"brace")
    errors = []
    for name in searches:
        data = requests.get('https://api.scryfall.com/cards/search?q=!'+name) #checks for exact match
        if data.json()['object'] == "error": #if no exact match, check for partial match
            data = requests.get('https://api.scryfall.com/cards/search?q='+ 'name:/\\b('+ name +')\\b/' \
                                +" t:legendary (t:creature or t:planeswalker)") #check for unique
            if data.json()['object'] == "error":
                data = requests.get('https://api.scryfall.com/cards/search?q='+'name:/^('+ name +')/') #match from start
                if data.json()['object'] == "error":
                    data = requests.get('https://api.scryfall.com/cards/search?q='+ name)

        if data.json()['object'] == "error":
            errors.append(name)
            continue

        result = data.json()['data'][0]
        name = result['name']
        print(name)
        mana_cost = result['mana_cost']
        type_line = result['type_line']
        oracle = result['oracle_text']
        if 'power' in result:
            powtou = "\n" + result['power']+"/"+result['toughness']
        else:
            powtou = ""
        print(powtou)
        if 'loyalty' in result:
            loyal = "\n" + "Loyalty: " + result['loyalty']
        else:
            loyal = ""
        update.message.reply_text(name + "      " + mana_cost + "\n" + type_line + "\n \n" + oracle + powtou + loyal)#, quote = false)
        print("done")
    print(errors)
    if len(errors) != 0:
        reply = "Not found: "
        for x in errors:
            update.message.reply_text(reply+x)
    print("done")
 
## End of Code for card call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def start(update, context):
  update.message.reply_text("Search for Magic: the Gathering cards via Scryfall's database. The \
bot will check for an exact match first, then look for partial matches and post the image \
of the alphabetically-first match to chat.")

def bot_help(update, context):
  context.bot.send_message(chat_id = update.message.chat_id, text = "<b>Eager Construct Help:</b>\nSearch for a card by \
enclosing its name with [[ ]] in your message. You can search for multiple cards at once, \
in which case the search results will be grouped into an album.\nThe message DOES NOT need \
to only contain bracketed terms: you may mention the card as part of a regular message.\n\
Example: What's so great about [[Saheeli]] and [[Felidar Guardian]]?\n \n\
You can also search for other characteristics using \
<a href='https://scryfall.com/docs/reference'>Scryfall's search syntax.</a> \
Common options include: \n\
 <b>-Oracle text</b> o:\n <b>-Type</b> t:\n <b>-Color</b> c:\n\
 <b>-Color identity</b> id:\n <b>-Cost</b> m: \n \
Example: [[o:\"can't attack you\" t:enchantment c:r]]", parse_mode = "HTML")
  
def main():
  # Create Updater object and attach dispatcher to it
  updater = Updater('460338069:AAFi4h7SydFGFg7mO5fzDkBKk4uZWvPP-yU', use_context=True)
  dispatcher = updater.dispatcher
  print("Bot started")

  # Add command handler to dispatcher
  start_handler = CommandHandler('start', start)
  help_handler = CommandHandler('help', bot_help)
  card_handler = MessageHandler((start_brackets & end_brackets), card_image_search)
  card_handler2 = MessageHandler((start_braces & end_braces), card_oracle_search)
  dispatcher.add_handler(start_handler)
  dispatcher.add_handler(card_handler)
  dispatcher.add_handler(card_handler2)
  dispatcher.add_handler(help_handler)
  
  
  # Start the bot
  updater.start_polling()

  # Run the bot until you press Ctrl-C
  updater.idle()

if __name__ == '__main__':
    main()
