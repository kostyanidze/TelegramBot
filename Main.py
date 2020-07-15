import telebot
from telebot.types import Message
from telebot import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
import requests
import pyowm
from datetime import datetime
from pyowm.utils.config import get_default_config
from pyowm.owm import OWM

bot = telebot.TeleBot(config.TOKEN)
appid = config.appid
s_city = ""
city_id = 0
config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM(appid,config_dict)

def get_wind_direction(deg):
    l = ['Север ','Северо-Восток',' Восток','Юго-Восток','Юг ','Юго-Запад',' Запад','Северо-Запад']
    for i in range(0,8):
        step = 45.
        min = i*step - 45/2.
        max = i*step + 45/2.
        if i == 0 and deg > 360-45/2.:
            deg = deg - 360
        if deg >= min and deg <= max:
            res = l[i]
            break
    return res

@bot.message_handler(commands=['start'])
def start(message: Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = types.KeyboardButton('Погода')
    btn2 = types.KeyboardButton('Прогноз')
    btn3 = types.KeyboardButton('Восход и закат')
    markup.add(btn1, btn2, btn3)
    send_mess = f"<b>Привет {message.from_user.first_name}</b>! \nПривет! Это бот который показывает некоторые данные о погоде в выбранном городе! Введи команду /help чтобы узнать больше!"
    bot.send_message(message.chat.id, send_mess,parse_mode='html',reply_markup=markup)


@bot.message_handler(commands=['help'])
def command_handler(message: Message):
    bot.send_message(message.chat.id, 'Чтобы выбрать город напиши его название и страну, например Ульяновск,РФ.\nНапиши Погода,Прогноз или Восходизакат(или же воспользуйся кнопками), чтобы узнать информацию о погоде!\nТакже доступны команды: /weather, /forecast и /sunriseandsunset')



@bot.message_handler(commands=['weather'])
def weather(message: Message):
    try:
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(s_city)
        weather = observation.weather
        temp_dict_celsius = weather.temperature('celsius')
        wind_dict_in_meters_per_sec = observation.weather.wind()
        send_mess = f"Выбранный город : {s_city}\n" \
                    f"<b>Текущая погода:</b>\n" \
                    f"<b>Состояние неба:</b> {weather.detailed_status}\n" \
                    f"<b>Температура сейчас:</b> {'{0:+3.0f}'.format(temp_dict_celsius['temp'])}°C\n" \
                    f"<b>Ощущается как:</b> {'{0:+3.0f}'.format(temp_dict_celsius['feels_like'])}°C\n" \
                    f"<b>Минимальная температура сегодня:</b> {'{0:+3.0f}'.format(temp_dict_celsius['temp_min'])}°C\n" \
                    f"<b>Максимальная температура сегодня:</b> {'{0:+3.0f}'.format(temp_dict_celsius['temp_max'])}°C\n" \
                    f"<b>Скорость ветра:</b> {wind_dict_in_meters_per_sec['speed']}м/с, направление: {get_wind_direction(wind_dict_in_meters_per_sec['deg'])}"
        bot.send_message(message.chat.id, send_mess, parse_mode='html')
    except Exception as e:
        print("Exception (weather):", e)
        bot.send_message(message.chat.id, text="<b>Выберите город!</b>", parse_mode='html')
        pass

@bot.message_handler(commands=['sunriseandsunset'])
def sunrise_and_sunset(message: Message):
    try:
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(s_city)
        weather = observation.weather
        sunrise_unix = datetime.fromtimestamp(weather.sunrise_time())
        sunset_unix = datetime.fromtimestamp(weather.sunset_time())
        send_mess = f"<b>Время восхода:</b> {sunrise_unix.hour}:{sunrise_unix.minute}\n" \
                    f"<b>Время заката:</b> {sunset_unix.hour}:{sunset_unix.minute}"
        bot.send_message(message.chat.id, send_mess, parse_mode='html')
    except Exception as e:
        print("Exception (sunriseandsunset):", e)
        bot.send_message(message.chat.id, text="<b>Выберите город!</b>", parse_mode='html')
        pass

@bot.message_handler(commands=['forecast'])
def prognoz(message: Message):
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        str='city:', data['city']['name'], data['city']['country']
        for i in data['list']:
            str = ""
            if '15:00' in (i['dt_txt'])[:16]:
                str ="<b>Дата:</b> "+ (i['dt_txt'])[:16] + "\n<b>Температура:</b> " + '{0:+3.0f}'.format(i['main']['temp'])+ "°C\n<b>Скорость ветра:</b> " \
                                                                                                                             '{0:2.0f}'.format(i['wind']['speed']) + "м/с\n<b>Направление:</b> "+ \
                     get_wind_direction(i['wind']['deg']) + "\n<b>Состояние неба:</b> " + \
                     i['weather'][0]['description']
                bot.send_message(message.chat.id, str , parse_mode='html')
    except Exception as e:
        print("Exception (forecast):", e)
        bot.send_message(message.chat.id, text="<b>Выберите город!</b>", parse_mode='html')
        pass


@bot.message_handler(content_types=['text'])
@bot.edited_message_handler(content_types=['text'])
def text_handler(message: Message):
    if 'Погода' in message.text:
        weather(message)
    elif 'Прогноз' in message.text:
        prognoz(message)
    elif 'Восход и закат' in message.text:
        sunrise_and_sunset(message)
    else:
        try:
            global s_city
            s_city = message.text
            global city_id
            city_id = get_city_id(s_city)
            bot.send_message(message.chat.id, "Выбранный город: " + s_city, parse_mode='html')
        except Exception as e:
            print("Exception (find):", e)
            bot.send_message(message.chat.id, text="<b>Такой город не найден. Попробуйте еще раз.</b>", parse_mode='html')
            pass


def get_city_id(s_city):
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/find",
                           params={'q': s_city, 'type': 'like', 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        cities = ["{} ({})".format(d['name'], d['sys']['country'])
                  for d in data['list']]
        print("city:", cities)
        city_id = data['list'][0]['id']
        print('city_id=', city_id)
    except Exception as e:
        print("Exception (find):", e)
        pass
    assert isinstance(city_id, int)
    return city_id


bot.polling(none_stop=True)