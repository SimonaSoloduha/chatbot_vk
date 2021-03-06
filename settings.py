GROUP_ID = 198185838
TOKEN = ''
INTENTS = [
    {
        "name": "Дата проведения",
        "tokens": ("когда", "сколько", "дата", "дату"),
        "scenario": None,
        "answer": "Конференция проводится 15-го апреля, регистрация начнется в 10 утра"
    },
    {
        "name": "Место проведения",
        "tokens": ("где", "Где", "место", "локация", "адрес", "метро"),
        "scenario": None,
        "answer": "Конференция пройдет в павильоне 18Г в экспоцентре"
    },
    {
        "name": "Регистрация",
        "tokens": ("регист", "добав"),
        "scenario": "registration",
        "answer": None
    },
]
SCENARIOS = {
    "registration": {
        "first_step": "step1",
        "steps": {
            "step1": {
                "text": "Чтобы зарегистрироваться введите ваше имя. оно будет написано на бейдже",
                "failure_text": "Имя может состоять из 3-30 букв и дефиса. Попробуйте еще раз",
                "handler": "handler_name",
                "next_step": "step2"
            },
            "step2": {
                "text": "Введите email. мы отправим на него все данные",
                "failure_text": "В веденном адресе ошибка. Попробуйте еще раз",
                "handler": "handler_email",
                "next_step": "step3"
            },
            "step3": {
                "text": "Спасибо за регистрацию",
                "image": "handler_generate_ticket",
                "failure_text": None,
                "handler": None,
                "next_step": None
            }
        }
    }
}
DEFAULT_ANSWER = "Не знаю как на это ответить. Могу сказать когд аи где пройдет конференция, " \
                 "а также зарегистрировать вас. Просто спросите"

DB_CONFIG = dict(
    provider='postgres',
    user='postgres',
    password='212121',
    host='localhost',
    database='vk_chat_bot'
)