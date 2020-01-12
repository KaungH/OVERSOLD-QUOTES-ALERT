##USING ALPACA API
##USING TWILIO API
##LIMITATION 200 requests per every minute per API key
##TASKS: SENDS OVERSOLD STOCK LIST TO A PHONE NUMBER
##PURPOSE: ALLOW USERS TO EXPLORE DIFFERENT KIND OF OVERSOLD STOCKS IN REVERSAL OF STOCK PRICE

#https://github.com/alpacahq/alpaca-trade-api-python/#restget_barsetsymbols-timeframe-limit-startnone-endnone-afternone-untilnone

##Ideas for improvements
###FINDING BALANCE IN REQUESTS LIMIT & PERFORMACE SPEED
###DOES NOT REPEAT PREVIOUS SENT STOCK TAGS
###EQUIP MULTIPLE STOCK TECHNICAL INDICATORS
###ALERT SUDDEN DROP IN SPECIFIC STOCK
###CREATING SPREAD SHEET TO KEEP TRACK SMS SENT
###EXPLOR FOR MORE NUMPY OPTIONS
###ALERT FOR STOCKS IN SPECIFIC CATEGORIES



from config import *

import time,json
import requests
import numpy as np
import alpaca_trade_api as tradeapi
from twilio.rest import Client
os.getenv('AccountSid')
os.getenv('AuthToken')
os.getenv('API_KEY ')
os.getenv('SECRET_KEY')
os.getenv('sender_num')
os.getenv('receiv_num')


BASE_URL  = "https://paper-api.alpaca.markets"
# ACC_URL   = "{}/v2/account".format(BASE_URL)
# ORDER_URL = "{}/v2/orders".format(BASE_URL)
ASET_URL  = "{}/v2/assets".format(BASE_URL)
SMS_URL   = "https://api.twilio.com/2010-04-01"

Headers   = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}     ##Alpaca market assets      

api = tradeapi.REST(API_KEY,SECRET_KEY) ##assets data

client = Client(AccountSid, AuthToken) ##Twilio SMS



def get_account():

    resp = requests.get(ACC_URL, headers = Headers)
    return json.loads(resp.content)##load account infos

def get_asset():
    
    resp   = requests.get(ASET_URL, headers = Headers)
    objects = json.loads(resp.content)
    
    
    
    stock = np.array([item["symbol"] for item in objects if 
    item["exchange"] == "NYSE"  and len(item["symbol"]) <=5 ] )
    
    random_stock = np.random.shuffle(stock)
    
    return (stock)  ##loads randomized listed stocks on NYSE  

    
    



def create_order(symbol,qty,side,type,time_in_force,extended_hours = False):
    data = {
        "symbol" : symbol,
        "qty"    : qty,
        "side"   : side,
        "type"   : type,
        "time_in_force": time_in_force,
    }
    order = requests.post(ORDER_URL,json=data, headers = Headers )
    return json.loads(order.content)["symbol"]
    #response = create_order("AAPL",100,"buy","market","gtc")##example

def get_order():
    order = requests.get(ORDER_URL, headers = Headers )
    return json.loads(order.content)
    ##load orders
    
def find_stock(array):
    counter = 0
    
    filtered_dict = {}
    for item in array:

        try:
            barset    = api.get_barset(item, 'day', limit=60)
            ###retrieve stock prices of 60 days
            ticker_close = np.array([barset[item][j].c for j in range(len(barset[item]))])
            ##EVERYDAY PRICE stored in ticker_close
            SMA60 = (round((ticker_close.sum()/60),2))
            ##FIND SIMPLE MOVING AVERAGE of 60 DAYS VALUE
            
            today_close    = barset[item][-1].c
        except IndexError: ##IN CASE OF INVALID TAG NAME
            continue

        percent_change = ((today_close - SMA60) / SMA60 * 100)
            ##FIND PERCENTAGE CHANGE
        if  percent_change < -10: ##FOUND OVERSOLD STOCKS
            
            ##FIND WHICH STOCK IN REVERSAL
            barset_tenDays = api.get_barset(item, 'day', limit=10)
            ##RETREVIE STOCK PRICE 10 DAYS DATA
            close_tenDays = np.array([barset_tenDays[item][i].c for i in range(len(barset_tenDays[item]))])
            ##STROES STOCK PRICE OF TEN DAYS 
            

            SMA10 = (round((close_tenDays.sum()/10),2))
            ##FOUND SIMPLE MOVING AVERAGE OF 10 DAYS
            tenDays_percent = ((today_close - SMA10) / SMA10 * 100)
            if tenDays_percent > 0:
            
                ##IF DISPARANCY IS GREATER THAN 10%, item stored
                if len(filtered_dict.keys()) >5:
                    break
                filtered_dict[item] = round(percent_change,2)
                
        counter +=1
        ##COUNTER ENSURE BREAK FOR A MINUTE
        if (counter % 200 == 0):
            time.sleep(60)
        
    return filtered_dict
        ##RETURN THE DICTIONARY {STOCK NAME : PRICE}

ticker = get_asset()
##ORIGINAL STOCK LIST IS ASSIGNED TO TICKER

##TICKER IS THE PARAMETER FOR FINDING OVERSOLD STOCK

def send_sms(text):
    sorted(text, key=text.get, reverse=True) ##SORT DICT VALUES
    string = ''
    for key, value in text.items():
        string+= "{}:{}%\n".format(key,str(value))
         ##CREATE STR WITH VALUES
    client.messages.create(body=string, 
    ##SENDING STR ON SMS
                     from_= sender_num,
                     to= receiv_num
                 )
    text.clear()
    del string ##RESET THE STRING


send_sms(find_stock(ticker))
##SENDING SMS




