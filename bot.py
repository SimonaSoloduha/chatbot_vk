#!/usr/bin/env python3

import random
import logging
import handlers
import requests

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from pony.orm import db_session

from models import UserState, Registration

try:
    import settings
except ImportError:
    exit('Do cp settings.py default settings.py and set token!!!')

log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)


def configure_logging():

    steam_handler = logging.StreamHandler()
    steam_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    steam_handler.setLevel(logging.DEBUG)
    log.addHandler(steam_handler)

    file_handler = logging.FileHandler("bot.log")
    format_file_handler = '%(asctime)-15s %(levelname)-6s %(message)s'
    date_format_file_handler = '%d-%m-%Y %H:%M'
    formatter_file = logging.Formatter(fmt=format_file_handler, datefmt=date_format_file_handler)
    file_handler.setFormatter(formatter_file)
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)



class Bot:

    """
    Use python3.8
    Сценарий регистрации на конференцию "SkillBox Conf" через vk.com.
    Поддерживает ответы на вопросы про дату, место проведения и сценарий регистрации:
    - спрашивет имя,
    - спрашиваем email,
    - говорим об успешной регистрации

    Если шаг не пройден задаем уточняющие вопросы пока шаг не будет пройден.
    """

    def __init__(self, group_id, token):
        """

        :param group_id: group_id из группы vk
        :param token: секретный токен
        """
        self.token = token
        self.group_id = group_id
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()


    def run(self):
        """
        Запуск бота
        """

        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception("ошибка в обработке события")

    @db_session
    def on_event(self, event):
        """
        Отправляем сообщение назад, если это текст
        :param event: VkBotMessageEvent object
        :return None
        """
        if event.type != vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            log.info("Увы увы... пока мы не знаем что творят на странице, но это что-то типа:%s", event.type)
            return

        user_id = event.object.message["peer_id"]
        text = event.object.message["text"]

        state = UserState.get(user_id=str(user_id))

        if state is not None:
            self.continue_scenario(text, state, user_id)
        else:
            for intent in settings.INTENTS:
                log.debug(f'User gets {intent}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                        self.send_text(text_to_send, user_id)
                    else:
                        self.start_scenario(user_id, intent['scenario'], text)
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER
                self.send_text(text_to_send, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        # print('upload_url', upload_url)
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        # print('upload_data', upload_data)
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        # print('image_data', image_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        #<type><owner_id>_<media_id>
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )



    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_text(step['text'], user_id)
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})


    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        # print('2', state.context, type(state.context))
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            # text_to_send = next_step['text'].format(**state.context)
            # self.send_text(text_to_send, user_id)
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                # log.debug(f'Зарегистрирован {name} {email}'.format(**state.context))
                Registration(name=state.context['name'], email=state.context['email'])
                state.delete()
        else:
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)


if __name__ == "__main__":
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()

# попробуйте прописать
#
# postgres -U postgres -d vk_chat_bot
#
# -U это название юзера, по умолчанию создаётся postgres при установке
#
# -d vk_chat_bot - название базы для бота, можно заменить на своё
# source venv/bin/activate
# /Users/soloduha/scripts/runpsql.sh; exit
# psql -d vk_chat_bot

# postgres=# psql
# postgres-# create database vk_chat_bot
