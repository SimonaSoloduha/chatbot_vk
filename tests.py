from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent, VkBotEvent

from bot import Bot
import vk_api

from chatbot import settings
from generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


class Test1(TestCase):
    RAW_EVENT = {'type': 'message_new',
                 'object':
                     {'message':
                          {'date': 1599218795, 'from_id': 611951744, 'id': 231, 'out': 0, 'peer_id': 611951744,
                           'text': 'апрпапрапр', 'conversation_message_id': 231, 'fwd_messages': [],
                           'important': False, 'random_id': 0, 'attachments': [], 'is_hidden': False},
                      'client_info':
                          {'button_actions':
                               ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                           'keyboard': True, 'inline_keyboard': True, 'carousel': False, 'lang_id': 0}},
                 'group_id': 198185838,
                 'event_id': '5376db84c410d30b499a884ee6bae005cdbe7952'}


    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot("", "")
                bot.on_event = Mock()
                bot.run()
                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    INPUTS = [
        'Привет',
        'А когда?',
        'Где будет конференция?',
        'Зарегистрируй меня',
        'Вениамин',
        # 'мой адрес email@',
        'мой адрес email@email.ru',
    ]
    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.SCENARIOS['registration']['steps']['step1']['text'],
        settings.SCENARIOS['registration']['steps']['step2']['text'],
        # settings.SCENARIOS['registration']['steps']['step2']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step3']['text'].format(name='Вениамин', email='email@email.ru')
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock


        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()
        assert send_mock.call_count == len(self.INPUTS)

        real_uotputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            print('kwargs[message]', kwargs['message'])
            real_uotputs.append(kwargs['message'])

        assert real_uotputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        with open('files/avatar_for_test.png', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket('name', 'email')

        with open('files/ticket_example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes




    # def test_on_event(self):
    #     event = VkBotMessageEvent(raw=self.RAW_EVENT)
    #     send_mock = Mock()
    #
    #     with patch('bot.vk_api.VkApi'):
    #         with patch('bot.VkBotLongPoll'):
    #             bot = Bot("", "")
    #             bot.api = Mock()
    #             bot.send_image = Mock()
    #             bot.api.messages.send = send_mock
    #             bot.on_event(event)
    #
    #     send_mock.assert_called_once_with(
    #         message=self.RAW_EVENT['object']['message']['text'],
    #         random_id=ANY,
    #         peer_id=str(self.RAW_EVENT['object']['message']['peer_id']))