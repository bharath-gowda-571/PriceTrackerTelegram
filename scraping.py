import requests
import fake_useragent
from bs4 import BeautifulSoup
import time
import logging
ua = fake_useragent.UserAgent()

logging.basicConfig(filename="logs", filemode='w',
                    format="%(asctime)s-%(levelname)s-%(message)s", datefmt='%m/%d/%Y %I:%M:%S %p')


def price_2_num(p):
    temp_price = ''
    for i in p.text:
        if i.isdigit() or i == '.':
            temp_price += i
    return temp_price


def get_product_info_flipkart(url):
    logging.info("tracking "+url)
    try:
        r = requests.get(url) #, headers={"User-Agent": str(ua.chrome)})
        logging.info("scraping success!!")

    except requests.exceptions.TooManyRedirects:
        logging.error("Too Many redirects error!! Trying again.")
        time.sleep(5)
        try:
            r = requests.get(url)#, headers={"User-Agent": str(ua.chrome)})
        except:
            logging.error("Trying again didn't work.")
            return False

    except requests.exceptions.ConnectionError:
        logging.error("Connection Error!! Trying again.")
        time.sleep(5)
        try:
            r = requests.get(url)#, headers={"User-Agent": str(ua.chrome)})
        except:
            logging.error("Trying again didn't work.")
            return False

    soup = BeautifulSoup(r.text, 'html.parser')
    # Price of the product
    price = soup.find_all('div', {"class": "_1vC4OE _3qQ9m1"})
    price_in_num = price_2_num(price[0])
    # Name of the product
    product_name = soup.find_all('span', {"class": "_35KyD6"})[
        0].get_text(strip=True)

    # Stock status of the product
    sold_out = "Yes"
    sold_out_temp = soup.find_all('div', {"class": "_9-sL7L"})
    if sold_out_temp:
        sold_out = "No"

    return {"name": product_name, "price_with_currency": price[0].text, "price_in_num": float(price_in_num), "availability": sold_out}
