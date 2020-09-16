from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
# import re
import sqlite3
from scraping import get_product_info_flipkart
import telegram.ext
from datetime import timedelta
import logging
from time import sleep


def gather_name_list(chat_id):
    logging.info("Gathering list of items for "+str(chat_id))
    conn = sqlite3.connect("telegram_database.db")
    c = conn.cursor()

    table_name = "_" + str(chat_id)

    c.execute(
        'create table if not exists ' + table_name + ' (link text,name text,price_with_currency text,price real,in_stock text)')
    c.execute('SELECT * FROM ' + table_name)
    lis = c.fetchall()
    product_names = []
    for j in lis:
        product_names.append(j[1])
    # print(product_names)
    product_names.sort()
    list_message = "<i>You are tracking the following products:</i>\n\n<b>"
    for i in enumerate(product_names):
        list_message += str(i[0] + 1) + ". " + i[1] + "\n\n"
    list_message = list_message.strip() + "</b>"
    conn.commit()
    conn.close()
    return (list_message, product_names)


def add(bot, update):
    chat_id = update.message.chat_id
    logging.info(str(chat_id)+" is trying add a product.")
    # print(chat_id)
    try:
        link = str(update.message.text).strip().split()[1]
        # print(link)
    except IndexError:
        logging.info(str(chat_id)+" didn't enter any product link.")
        bot.send_message(
            chat_id=chat_id, text="<b>Please enter a flipkart product link.</b>", parse_mode="html")
        return
    if "flipkart.com" not in link:
        logging.info(str(chat_id)+" didn't enter a valid product link")
        bot.send_message(chat_id=chat_id, text="<i>"+link +
                         "</i><b> Doesn't seem to be a valid flipkart link.</b>", parse_mode="html")
        return
    conn = sqlite3.connect("telegram_database.db")
    c = conn.cursor()
    table_name = "_"+str(chat_id)
    c.execute(
        'create table if not exists ' + table_name + ' (link text,name text,price_with_currency text,price real,in_stock text)')
    conn.commit()
    conn.close()
    try:
        product_info = get_product_info_flipkart(link)
    except IndexError:
        logging.info(str(chat_id)+" didn't enter a valid product link")
        bot.send_message(chat_id=chat_id, text=link +
                         " is not a link to product on flipkart.\nEnter / help commands to view all commands and their formats")
    if product_info:
        conn = sqlite3.connect("telegram_database.db")
        c = conn.cursor()
        c.execute('SELECT * FROM ' + table_name +
              ' WHERE name=?', (product_info["name"],))
        match = c.fetchone()
        if match:
            logging.info(str(chat_id)+" entered an already present link.")
            bot.send_message(chat_id=chat_id, text='You are already tracking <b>'+match[1]+'</b>')
        else:
            logging.info("Product addition was a success")
            c.execute('INSERT INTO ' + table_name + ' values (?,?,?,?,?)', (link,product_info['name'], product_info["price_with_currency"], product_info["price_in_num"], product_info['availability']))
            bot.send_message(chat_id=chat_id, text="You just added <b>" + product_info["name"] + "</b> for tracking.\nCurrently:\n   Price:" +product_info["price_with_currency"].rjust(10) + "\nIn Stock:" + product_info["availability"].rjust(10), parse_mode='html')
        
        conn.commit()
        conn.close()
    else:
        bot.send_message(chat_id=chat_id,text="Something didn't work there!! Try again after a minute or so.")


def list_names(bot, update):
    chat_id = update.message.chat_id
    logging.info("Listing "+str(chat_id)+"'s Products")
    list_message, product_names = gather_name_list(chat_id)
    if len(product_names) == 0:
        bot.send_message(
            chat_id=chat_id, text="<b>You are not tracking any items.</b>", parse_mode='html')
        return
    bot.send_message(chat_id=chat_id, text=list_message, parse_mode='html')


def remove(bot, update):
    chat_id = update.message.chat_id
    logging.info(str(chat_id)+" is trying to remove a product.")
    # print(chat_id)
    list_message, product_names = gather_name_list(chat_id)
    try:
        num = int(str(update.message.text).strip().split()[1])
        # print(num)
    except IndexError:
        num = 0
    except ValueError:
        num = 0

    if len(product_names) == 0:
        bot.send_message(
            chat_id=chat_id, text="<b>You are not tracking any items.</b>", parse_mode='html')
        return
    if not num:
        bot.send_message(chat_id=chat_id, text=list_message, parse_mode='html')
        bot.send_message(
            chat_id=chat_id, text="\nSelect the product to remove. \n<i>Enter <b>/remove --no. corresponding to the product-- </b> to remove the product</i>", parse_mode='html')
        return
    if num > len(product_names) or num < 0:
        bot.send_message(
            chat_id=chat_id, text="<b>No Product with that number.</b>", parse_mode='html')
        return

    conn = sqlite3.connect("telegram_database.db")
    c = conn.cursor()
    table_name = "_"+str(chat_id)
    c.execute("DELETE FROM "+table_name +
              " WHERE name=?", (product_names[num-1],))
    conn.commit()
    conn.close()
    bot.send_message(chat_id=chat_id, text="You removed <b>" +
                     product_names[num-1]+"</b> from tracking.", parse_mode='html')
    logging.info(str(chat_id)+" removed a product.")


def daily_checker(bot, job):
    conn = sqlite3.connect("telegram_database.db")
    c = conn.cursor()
    c.execute('SELECT name from sqlite_master where type= "table"')
    all_users = c.fetchall()
    conn.close()
    logging.info("There are currently "+str(len(all_users)) +
                 " accounts using the bot.")
    total_products = 0
    for j in all_users:

        conn = sqlite3.connect("telegram_database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM "+j[0])

        all_items = c.fetchall()
        conn.close()

        chat_id = int(j[0][1:])
        # print("Doing "+str(chat_id)+"'s Tracking.")
        # print(dic)
        logging.info("Tracking "+str(chat_id)+"'s products.")
        for i in all_items:
            sleep(2)
            total_products += 1
            dic = get_product_info_flipkart(i[0])
            # print(dic)
            if not dic:
                continue
            current_price = dic['price_in_num']
            current_in_stock = dic['availability']
            price_change = current_price - i[3]
            # price_change= -1000
            # print(dic['name'])
            if price_change > 0:
                bot.send_message(chat_id=chat_id, text="**"+dic['name']+"**:\n\n"+"*6 hours back*:\n```   Price:"+i[2].rjust(10)+"\nIn Stock:"+i[4].rjust(
                    10)+"```\n*Now*:\n```   Price:"+dic["price_with_currency"].rjust(10)+"\nIn Stock:"+dic["availability"].rjust(10)+"```", parse_mode='markdown')

                bot.send_message(chat_id=chat_id, text="```diff\n-Price has increased by " +
                                 dic["price_with_currency"][0]+str(price_change)+"```", parse_mode='markdown')
                logging.info("Price of "+dic['name']+" increased.")

            elif price_change < 0:
                bot.send_message(chat_id=chat_id, text="**"+dic['name']+"**:\n\n"+"*6 hours back*:\n```   Price:"+i[2].rjust(10)+"\nIn Stock:"+i[4].rjust(
                    10)+"```\n*Now*:\n```   Price:"+dic["price_with_currency"].rjust(10)+"\nIn Stock:"+dic["availability"].rjust(10)+"```", parse_mode='markdown')

                bot.send_message(chat_id=chat_id, text="```yaml\nPrice has decreased by " +
                                 dic["price_with_currency"][0]+str(abs(price_change))+"```", parse_mode='markdown')
                logging.info("Price of "+dic['name']+" decreased.")

            else:
                logging.info("No change in price for "+dic['name'])

            if dic['availability'] == 'Yes' and i[4] == 'No':
                if price_change != 0:
                    bot.send_message(
                        chat_id=chat_id, text="```yaml\nProduct is in stock.```", parse_mode='markdown')
                else:
                    bot.send_message(chat_id=chat_id, text="**"+dic['name']+"**:\n"+"*6 hours back*:\n```   Price:"+i[2].rjust(10)+"\nIn Stock:"+i[4].rjust(
                        10)+"```\n*Now*:\n```   Price:"+dic["price_with_currency"].rjust(10)+"\nIn Stock:"+dic["availability"].rjust(10)+"```", parse_mode='markdown')
                    bot.send_message(
                        chat_id=chat_id, text="```yaml\nProduct is in stock.```", parse_mode='markdown')
                    logging.info("Product just came in to stock.")

            if price_change < 0 and dic['availability'] == "No":
                bot.send_message(
                    chat_id=chat_id, text="```diff\n-But the product is out of stock.```", parse_mode='markdown')
                logging.info("Product went out of stock.")
            if price_change != 0:
                bot.send_message(chat_id=chat_id,
                                 text="Link:\n"+i[0])
            # Updating the database with the current values.
            conn = sqlite3.connect("telegram_database.db")
            c = conn.cursor()
            c.execute("UPDATE "+j[0]+" SET price_with_currency='" +
                      dic['price_with_currency']+"' WHERE link=?", (i[0],))
            c.execute("UPDATE "+j[0]+" SET price=" +
                      str(dic["price_in_num"])+" WHERE link=?", (i[0],))
            c.execute("UPDATE "+j[0]+" SET in_stock='" +
                      dic["availability"]+"' WHERE link=?", (i[0],))
            conn.commit()
            conn.close()

    logging.info("Total number of products tracked : "+str(total_products))


def check_now(bot, update):
    chat_id = update.message.chat_id
    # print(chat_id)
    list_message, product_names = gather_name_list(chat_id)
    try:
        num = int(str(update.message.text).strip().split()[1])
        print(num)
    except IndexError:
        num = 0
    except ValueError:
        num = 0
    conn = sqlite3.connect("telegram_database.db")
    c = conn.cursor()
    table_name = "_"+str(chat_id)
    c.execute('create table if not exists ' + table_name +
              ' (link text,name text,price_with_currency text,price real,in_stock text)')
    c.execute("SELECT * FROM "+table_name)
    all_items = c.fetchall()
    logging.info("Doing "+str(chat_id)+"'s Tracking.")
    if len(all_items) == 0:
        bot.send_message(
            chat_id=chat_id, text="<b>You are not tracking any items.</b>", parse_mode='html')
        return
    if num == 0:
        message = "__**You are tracking the following items.**__\n"
        for j in enumerate(all_items):
            message += str(j[0]+1)+". "+j[1][1]+"\n\n"
        message += "-1. All Items\n" + \
            "Enter `/check <no. corresponding to product>` to check that product."
        bot.send_message(chat_id=chat_id, text=message, parse_mode='markdown')
    else:
        if num > len(all_items) or num < -2:
            bot.send_message(
                chat_id=chat_id, text="<b>No Product with that number.</b>", parse_mode='html')
            return
        else:
            if num == -1:
                for i in all_items:
                    sleep(2)
                    dic = get_product_info_flipkart(i[0])
                    if not dic:
                        bot.send_message(chat_id=chat_id,text=i[1]+" wasn't tracked due to some error. Try again after a while.")
                        continue
                    current_price = dic['price_in_num']
                    current_in_stock = dic['availability']
                    bot.send_message(chat_id=chat_id, text="<i>"+dic['name']+"</i>:\n"+"<b>Last Time Checked</b>:\n   Price:"+i[2].rjust(10)+"\nIn Stock:"+i[4].rjust(
                        10)+"\n<b>Now</b>:\n   Price:"+dic["price_with_currency"].rjust(10)+"\nIn Stock:"+dic["availability"].rjust(10)+"\n<i>Link:</i>\n"+i[0], parse_mode='html')
                    # await user.send()
            else:
                dic = get_product_info_flipkart(all_items[num-1][0])
                if not dic:
                    bot.send_message(chat_id=chat_id,text=all_items[num-1][0]+" wasn't tracked due to some error. Try again after a while.")
                    return
                current_price = dic['price_in_num']
                current_in_stock = dic['availability']
                bot.send_message(chat_id=chat_id, text="<i>"+dic['name']+"</i>:\n"+"<b>Last Time Checked</b>:\n   Price:"+all_items[num-1][2].rjust(10)+"\nIn Stock:"+all_items[num-1][4].rjust(
                    10)+"\n<b>Now</b>:\n   Price:"+dic["price_with_currency"].rjust(10)+"\nIn Stock:"+dic["availability"].rjust(10)+"\n<i>Link:</i>\n"+all_items[num-1][0], parse_mode='html')


def start(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text="This is a bot to track price and stock status of a product on flipkart.\n<b>Commands:</b>\n\n  /add --link to product--\n  /remove\n  /check: (To check current price and stock.)\n  /list\n<i>The bot will check the product price and stock every 6 hours.</i>\n<i>If some command doesn't work, wait a minute or two and try again.</i> ", parse_mode='html')
    logging.info(str(chat_id)+" started using the bot.")

def main():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%m/%d/%Y %I:%M:%S %p', handlers=[logging.FileHandler("output.log"), logging.StreamHandler()])

    updater = Updater("***TOKEN TO YOUR BOT***")
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('add', add))
    dp.add_handler(CommandHandler('list', list_names))
    dp.add_handler(CommandHandler('remove', remove))
    dp.add_handler(CommandHandler('check', check_now))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', start))
    j = updater.job_queue
    j.run_repeating(daily_checker, interval=timedelta(hours=6), first=0)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
