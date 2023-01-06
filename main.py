import pymongo
import os
from telethon import TelegramClient, events, Button
import random
import asyncio

URL = os.environ['MONGO_URL']
client = pymongo.MongoClient(URL)

mydb = client["omegal2"]
mycol = mydb["omgbot2"]
print("Succesfully connected to database")


def adduser(user):
  data = {"me": str(user), "online": False, "room": None, "searching": False}
  mycol.insert_one(data)


def online(user):
  qury = {"me": str(user)}
  newdata = {"$set": {"online": True}}
  mycol.update_one(qury, newdata)


def offline(user):
  qury = {"me": str(user)}
  newdata = {"$set": {"online": False}}
  mycol.update_one(qury, newdata)

def search(user, state):
  qury = {"me": str(user)}
  newdata = {"$set": {"searching": state}}
  mycol.update_one(qury, newdata)

def getroom(user):
  partner = mycol.find_one({"me": str(user)})["room"]
  return partner


def createroom(user, partner):
  qury1 = {"me": str(user)}
  querry2 = {"me": str(partner)}
  newdat1 = {"$set": {"room": str(partner)}}
  newdat2 = {"$set": {"room": str(user)}}
  mycol.update_one(qury1, newdat1)
  mycol.update_one(querry2, newdat2)


def delroom(user):
  parter = mycol.find_one({"me": str(user)})["room"]
  qury1 = {"me": str(user)}
  newdata1 = {"$set": {"room": None}}
  mycol.update_one(qury1, newdata1)
  qury2 = {"me": parter}
  newdata2 = {"$set": {"room": None}}
  mycol.update_one(qury2, newdata2)


async def findPartner(user):
  #print("fiind partner")
  partner = None
  offline(user)
  qury = {"online": True, "room": None}
  try:
    partner = mycol.aggregate([{
      "$match": qury
    }, {
      "$sample": {
        "size": 1
      }
    }]).next()["me"]
    offline(partner)
  except:
    await asyncio.sleep(0.5)
  if partner == str(user):
    partner = None
  return partner


async def getPartner(user):
  #print("getPartner")
  partner = None
  online(user)
  await asyncio.sleep(0.5)
  if not mycol.find_one({"me": str(user)})["online"]:
    partner = "found"
  else:
    offline(user)
  if partner == str(user):
    partner = None
  return partner


#Bot body
ID = os.environ['ID']
HASH = os.environ['HASH']
TOKEN = os.environ['TOKEN']
keyboard = [
  [Button.text('M or F?', resize=True, single_use=True)],
  [Button.text('DISCONECT', resize=True, single_use=True)],
  [Button.request_phone('SHARE CONTACT')],
  [Button.request_location('SHARE LOCATION')],
]
ME = os.environ['ME']

bot = TelegramClient('bot', ID, HASH).start(bot_token=TOKEN)
bot.parse_mode = 'html'
print("Bot started ! please visit the bot link given below.")
print("LINK: https://t.me/officialomegalbot")


@bot.on(events.NewMessage)
async def my_handler(event):
  msg = event.message.message
  id = event.chat_id
  markup = event.client.build_reply_markup(keyboard)
  exist = mycol.find_one({"me": str(id)})
  if exist == None:
    adduser(id)

  if str(id) == ME:
    if msg.startswith("UPDATE"):
      data2 = mycol.find()
      for user in data2:
        uid = int(user["me"])
        try:
          await bot.send_message(uid, msg)
        except:
          print("chat deleted, id: ", str(uid))

  if msg == "/self":
    await event.respond(str(id))
  elif msg == "/num":
    num_docs = mycol.count_documents({})
    await event.respond(str(num_docs))


  room = not (getroom(id) == None)
  try:
    searching = mycol.find_one({"me": str(id)})["searching"]
  except:
    search(id, False)
    searching = False

  if searching == True:
    work = await event.respond("Please wait..")
    await asyncio.sleep(1)
    await work.delete()
    return
    
  if room:
    partner = getroom(id)
    if msg == "/start":
      await bot.send_message(
      id, "Welcome back to Omegal Bot 🐤 !\nNOTE: You are in a room", buttons=markup)
      return
      
    elif msg == "DISCONECT":
      delroom(id)
      await event.respond(
        "🚫 Disconnected \nMENU\n/search - 🔎 to search a partner",
        buttons=Button.clear())
      await bot.send_message(
        int(partner),
        "🚫 Disconnected \nMENU\n/search - 🔎 to search a partner",
        buttons=Button.clear())

    elif msg == "/search":
      await event.respond("🚫 You are already in a room")
    else:
      await bot.send_message(int(partner), event.message)
  else:
    if msg == "/start":
      await bot.send_message(
      id, "Welcome to Omegal Bot 🐤 ! \nMENU\n/search - 🔎 to search a partner")
      return
      
    if msg == "/search":
      i = 0
      search(id, True)
      edmsg = await event.respond("🔎 Searchiing..")
      while i < 5:
        selector = random.choice(range(0, 2))
        if selector:
          offline(str(id))
          partner = await findPartner(id)
          if not (partner == None):
            createroom(id, partner)
            await event.respond("👩‍❤️‍👨 Partner found 😁", buttons=markup)
            return
        else:
          offline(str(id))
          partner = await getPartner(id)
          if not partner == None:
            await event.respond("👩‍❤️‍👨 Partner found 😁", buttons=markup)
            return
        i += 1
      await bot.edit_message(edmsg, "☹ No one is online")
      search(id, False)
      #await event.respond("☹ No one is online")


if __name__ == "__main__":
  bot.run_until_disconnected()
  
