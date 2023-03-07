from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import requests
import sqlite3 as sq
import re
import json
import time
import shutil

import pandas
import os


class DataBase:

    def __init__(self, derectory: str):
        self.derectory = derectory
        self.dict_country = '\n'.join([f"{key}  -----  {value}" for key, value in self.make_BD().items()])

    def make_BD(self) -> dict:
        req_areas = requests.get('https://api.hh.ru/areas')
        req_Json = req_areas.json()
        dict_country = {}
        try:
            os.remove(f"{self.derectory}/areas.db")
        except:
            pass

        with sq.connect(f"{self.derectory}/areas.db") as base:
            cur = base.cursor()
            for x in req_Json:
                cur.execute(f'''CREATE TABLE IF NOT EXISTS {'reg_' + x['id']}
                                (name_area VARCHAR(200),
                                 id_area VARCHAR(5) PRIMARY KEY)
                            ''')
                for j in x['areas']:
                    cur.execute(f'''INSERT INTO  {'reg_' + x['id']}(name_area, id_area)
                                                    VALUES (?,?)''', (j['name'].replace(' ', '_'), str(j['id'])))
                dict_country[x['name']] = x['id']
        print('DataBase connect')
        return dict_country

    def request_BD(self, country_id: int) -> str:
        with sq.connect(f"{self.derectory}/areas.db") as base:
            cur = base.cursor()
            a = cur.execute(f'''SELECT * FROM {'reg_' + str(country_id)}
            ''').fetchall()
        return ''.join([' ----- '.join(x) + '\n' for x in a])


class Reseption:

    def __init__(self, name_request: str, derectory: str, area=None, user_id='id12'):
        self.name_request = name_request
        self.area = area
        self.user_id = user_id
        self.derectory = derectory
        self.a = Save_cart(20, self.area, self.name_request, self.derectory, self.user_id)
        try:
            os.mkdir(f'{derectory}/{user_id}')
        except FileExistsError:
            print(FileExistsError)
            # shutil.rmtree(f"{derectory}/{user_id}")
            # os.mkdir(f'{derectory}/{user_id}')

    def save_str(self):
        self.a()

    def kurs_USD_EUR(self, currency: str, salary: str):
        kurs_USD = 70
        kurs_EUR = 76
        if currency == "USD":
            return int(salary) * kurs_USD
        if currency == "EUR":
            return int(salary) * kurs_EUR
        if currency == 'RUR':
            return int(salary)
        return None

    def get_salary(self):
        salary_from = []
        salary_to = []
        for fl in os.listdir(f'{self.derectory}/{self.user_id}/str'):
            with open(f'{self.derectory}/{self.user_id}/str/{fl}', encoding='utf-8') as file:
                jsonText = file.read()
                jsonObj = json.loads(jsonText)
                for v in jsonObj['items']:
                    if v['salary']:
                        if v['salary']['currency'] in ['USD', 'EUR', 'RUR'] and v['salary']['from']:
                            salary_from.append(self.kurs_USD_EUR(v['salary']['currency'], v['salary']['from']))
                        if v['salary']['currency'] in ['USD', 'EUR', 'RUR'] and v['salary']['to']:
                            salary_to.append(self.kurs_USD_EUR(v['salary']['currency'], v['salary']['to']))
        a = 'Не указывают ЗП' if not len(salary_from) else int((sum(salary_from) / len(salary_from)))
        b = 'Не указывают ЗП' if not len(salary_to) else int((sum(salary_to) / len(salary_to)))
        return f'Cредняя ЗП От {a} рублей.\n \t\t   До {b} рублей'

    def save_vakancy(self):
        self.a.request_vacancy()

    def get_key_skill(self):
        skill_list = SkillCount()  # Обьект посчетов определенных скилов
        for art in os.listdir(f"{derectory}/{self.user_id}/vacancy/"):
            with open(f"{derectory}/{self.user_id}/vacancy/{art}", "r", encoding="utf-8") as file:
                jsonObj = json.loads(file.read())
                try:
                    key_skills = [x['name'].lower() for x in jsonObj['key_skills']]
                    #############  Выдрать скилы из текста с помощью регулярных выражений ######################
                except:
                    key_skills = [None]
                skill_list(key_skills)
        skill_list.skills = {x: skill_list.skills[x] for x in skill_list.skills if skill_list.skills[x] > 1}
        return skill_list

    def get_data_file(self):
        dat = MakeFile()
        dat.make_doc(self.derectory, self.user_id)

    def clear(self):
        pass


class Save_cart:

    def __init__(self, page: int, area: int, text: str, derectory: str, user_id: str):
        self.page = page
        self.area = area
        self.text = text
        self.derectory = derectory
        self.user_id = user_id

    def request_str(self, text: str, page: int, area: int):  # Запрашивает одну страницу с данными по фильтрам
        params = {
            'text': text,  # текст запроса
            'area': area,  # Поиск в зоне
            'page': page,  # Номер страницы
            'per_page': 100,  # Кол-во вакансий на 1 странице
        }
        req = requests.get('https://api.hh.ru/vacancies', params)
        if not req.status_code:
            print(f'Ошибка сервера. ошибка:{req.status_code}')
        data = req.json()
        req.close()
        return data  # Возвращает json файл с вакансиями одной страницы

    def Sbor_str(self, page: int, area: int, text: str, derectory: str, user_id: str):  # запускает getPage в цикле для запроса страниц с карточками
        os.mkdir(f'{derectory}/{user_id}/str')
        for i in range(
                page):  # делает запрос на 'page' страниц поочередно перебирая их range(n) где n - число нужных страниц
            try:
                data = self.request_str(text, i, area)
                if int(data['pages']) == i:
                    raise StopIteration
                time.sleep(0.5)
                with open(f'{derectory}/{user_id}/str/result{i}.json', 'w', encoding='utf-8') as json_file:
                    json.dump(data,
                              json_file)  # Сохраняет в выбранную директорию страницы поиска (20 файлов по 100 вакансий)
                print(f"страница {i + 1} загруженна user : {user_id}")
            except:
                print(
                    'Я сохранил все которые нашел, (Ну или которые позволил скачать Head Hanter у него ограничение на 2 000 вакансий по одному запросу)')
                break

    def __call__(self):
        self.Sbor_str(self.page, self.area, self.text, self.derectory, self.user_id)

    def request_vacancy(self):  # пробегается по страницам с вакансиями и сохряняет на pc сами вакансии (1 файл- 1 карточка вакансии)
        os.mkdir(f'{self.derectory}/{self.user_id}/vacancy')
        try:
            i = 0
            for fl in os.listdir(f"{self.derectory}/{self.user_id}/str"):
                with open(f'{self.derectory}/{self.user_id}/str/{fl}', encoding='utf-8') as file:
                    jsonText = file.read()
                    jsonObj = json.loads(jsonText)
                    for v in jsonObj['items']:
                        req = requests.get(v['url'])
                        data = req.json()
                        req.close()
                        i += 1
                        with open(f'{self.derectory}/{self.user_id}/vacancy/vacancy{i}.json', 'w',
                                  encoding="utf-8") as json_file:
                            json.dump(data, json_file)
                        time.sleep(0.25)
                        print(f'все идет по плану, сохранен файл : {i} ')
        except:
            print(f'Все имеющиеся файлы обработаны')


class SkillCount:  # Класс для подсчета скилов
    def __init__(self):
        self.skills = {}

    def clear_slills(self):  # очистить список скилов
        self.skills = {}

    def __call__(self, skill_list: list[str]):
        for skill in skill_list:
            if skill not in self.skills:  # Если скила нет в списке то он добавляется со значением 1
                self.skills[skill] = 1
            else:
                self.skills[skill] = self.skills.get(skill) + 1  # Если скил есть в списке то он увеличивает значение на 1

    def __str__(self):
        lst = tuple([x for x in self.skills.items()])  # Создаем кортеж из нашего словаря
        ret = [':'.join(list(map(str, x))) + '\n' for x in
               sorted(lst, key=lambda x: x[1], reverse=True)]  # преобразуем в текст и сортируем по убыванию значения
        return f"{''.join(ret)}"  # сращиваем все в одну строку и возвращаем чтобы выглядело не в строчку


class ParsingDescription:

    @staticmethod
    def convertio(text: str):
        sp = ['Обязанности:', 'Требования:', 'Условия:']
        lst = [
            "Обязанн?ости:|Должностные обязанности|Что нужно делать|В ваши обязанности будет входить|Задачи, которые нужно будет|ЗАДАЧИ|Чем Вам предстоит",
            "Требования:|Пожелание к кондидатам|Будет плюсом|Мы ожидаем, что вы|Что нужно знать и уметь|Эта вакансия для Вас, если Вы|ожидания",
            "Условия работы:|Условия:|Что мы предлагаем|Мы предлагаем"]
        wer = {}
        wer['О компании'] = "".join(re.findall(fr"(?i).*(?<={sp[0]})", text))
        for x in range(len(lst)):
            wer[sp[x]] = "".join(re.findall(fr"(?i)(?:{lst[x]})(.*?<)/li> </ul>", text))

        for x in wer:
            wer[x] = re.findall(r"(?<=>)[\w+][^<]*(?=<)", wer[x])
        a, b, c, d = ['|<*>|'.join(x) for x in wer.values()]
        return a, b, c, d


class MakeFile:

    def __init__(self):
        self.dict_paragraph = {'name': ['name'], 'area': ['area', 'name'], 'salary_from': ['salary', 'from'],
                               'salary_to': ['salary', 'to'],
                               'currency': ['salary', 'currency'], 'experience': ['experience', 'name'],
                               'schedule': ['schedule', 'name'],
                               'description': ['description'], 'alternate_url': ['alternate_url']
                               }

    def make_doc(self, derectory: str, user_id: str):  # Проходит по всем карточкам собирая в списки интересеющую нас информацию из карточек для дальнейшей записи в exel файл или посчета скилов
        data = []
        for art in os.listdir(f"{derectory}/{user_id}/vacancy"):
            with open(f"{derectory}/{user_id}/vacancy/{art}", "r", encoding="utf-8") as file:
                jsonObj = json.loads(file.read())
                dict_para = self.dict_paragraph.copy()
                for key, value in dict_para.items():
                    if len(value) == 1:
                        dict_para[key] = jsonObj.get(*value, None)
                    if len(value) == 2:
                        try:
                            dict_para[key] = jsonObj[value[0]].get(value[1], None)
                        except:
                            dict_para[key] = None

                about_company, obligations, requiremeny, condition = ParsingDescription.convertio(
                    dict_para['description'])
                data.append([dict_para['name'], dict_para['area'], dict_para['salary_from'], dict_para['salary_to'],
                             dict_para['currency'],
                             dict_para['experience'], dict_para['schedule'], about_company, obligations, requiremeny,
                             condition, dict_para['alternate_url']])

        self.save_doc(derectory, user_id, data)

    def save_doc(self, derectory: str, user_id: str, data: list[list]):
        header = ['Вакансия', 'Регион', 'ЗП От', 'ЗП До', 'Валюта', 'Опыт работы', 'График работы', 'О компании',
                  'Обязанности', 'Требования', 'Условия', 'ссылка на вакансию']
        df = pandas.DataFrame(data, columns=header)
        df.to_csv(f"{derectory}/{user_id}/data{user_id}.csv", sep=';', encoding="utf-8-sig")
        ####### отправка файла пользователю #############
        # time.sleep(10)
        # shutil.rmtree(f"{derectory}/{user_id}")


##### Необходимые параметры   ########

page = 100  # сколько страниц запрашиваем
text = 'календарно-сетевое планирование'  # текст поиска как в поиске hh
derectory = 'C:/Users/user/Desktop/for parser'  # Дерриктория куда будут сохраняться страницы с карточками
area = 0  # Регион поиска
user_id = None
##### Запуск функций (в общем то управление парсером) #########


bot = Bot(os.getenv("TOKEN"))
dp = Dispatcher(bot)
data_base = None


async def on_startup(_):
    print('online')
    global data_base
    data_base = DataBase(derectory)


msg_start = r'''Привет! Это бот для парсинга Head Hunter!
Он может:
1) Расчитать среднюю ЗП по вакансии (например 'Python разработчик') и пришлет тебе сообщением прям сюда. Чтобы узнать как он это делает отправь команду /Info_zp

2) Собрать из вакансий все ключевые навыки и вывести их по частоте встречаемости. Чтобы подробней узнать как он это делает отправь команду /Info_skill

3) Прислать тебе exel файл со следующими столбцами:
'Вакансия', 'Регион', 'ЗП От', 'ЗП До', 'Валюта', 'Опыт работы', 'График работы', 'О компании', 'Обязанности', 'Требования', 'Условия', 'ссылка на вакансию' 

Чтобы подробней узнать как это выглядит отправь команду /Info_file

Если ты и так знаешь что тебе нужно то можешь нажать '/start_parsing' и получить нужную информацию
                '''
msg_start_parsing = '''Готово! 
Теперь ты можешь выполнить один из предложенных вариантов:
1) Расчитать среднюю ЗП. Команда  /Srednya_zp
2) Собрать из вакансий все ключевые навыки и вывести их по частоте встречаемости. Команда /Spisok_skill
3) Прислать тебе exel файл со всеми найдеными вакансиями. Команда /get_file'''

b1 = KeyboardButton('/Info_zp')
b2 = KeyboardButton('/Info_skill')
b3 = KeyboardButton('/Info_file')
b4 = KeyboardButton('/start_parsing')
b9 = KeyboardButton('/start')

kb_klient = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_klient.row(b1, b2, b3).add(b4).add(b9)

b5 = KeyboardButton('/Srednya_zp')
b6 = KeyboardButton('/Spisok_skill')
b7 = KeyboardButton('/Spisok_stran')
b8 = KeyboardButton('/get_file')
kb_klient_parser = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_klient_parser.add(b7).row(b5, b6).add(b8).add(b9)


@dp.message_handler(commands=['start', 'help'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, msg_start, reply_markup=kb_klient)


@dp.message_handler(commands=['Info_zp'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, msg_start, reply_markup=kb_klient)


@dp.message_handler(commands=['Info_skill'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, msg_start, reply_markup=kb_klient)


@dp.message_handler(commands=['Info_file'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, msg_start, reply_markup=kb_klient)


@dp.message_handler(commands=['start_parsing'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id,
                           "Начал загрузку всех вакансий по указанным параметрам. Это должно занять не более 20 секунд. Как все будет готово я пришлю сообщение")
    user_id = message.from_user.id
    Lex = Reseption(text, derectory, user_id=user_id)  # Создает папку в указанной дериктории
    Lex.save_str()
    await bot.send_message(message.from_user.id, msg_start_parsing, reply_markup=kb_klient_parser)


@dp.message_handler(commands=['Srednya_zp'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, 'Srednya_zp', reply_markup=kb_klient_parser)


@dp.message_handler(commands=['Spisok_skill'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, 'Spisok_skill', reply_markup=kb_klient_parser)


@dp.message_handler(commands=['Spisok_stran'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id,
                           f"{data_base.dict_country}\nДля того чтобы узнать коды регионов нужной страны,"
                           f" отошли сообщение формата /113 . Где 113 номер нужной тебе страны",
                           reply_markup=kb_klient_parser)


@dp.message_handler(commands=['get_file'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, 'get_file', reply_markup=kb_klient_parser)


@dp.message_handler(commands=['113', '5', '40', '9', '16', '28', '1001', '48', '97'])
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, data_base.request_BD(message.text[1:]), reply_markup=kb_klient_parser)


@dp.message_handler()
async def echo_send(message: types.Message):
    await message.answer('могу работать только с определенными командами', reply_markup=kb_klient)
    # await message.reply(message.text)
    # await bot.send_message(message.from_user.id, message.text)


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
