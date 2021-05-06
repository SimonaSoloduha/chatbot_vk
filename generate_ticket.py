from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = "files/ticket_base.png"
FONT_PATH = "files/OpenSans-Regular.ttf"
FONT_SIZE = 26
BLACK = (0, 0, 0, 255)
NAME_OFFSET = (280, 185)
EMAIL_OFFSET = (280, 210)
AVATAR_OFFSET = (170, 180)


def generate_ticket(name, email):
    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw = ImageDraw.Draw(base)
    draw.text(NAME_OFFSET, name, font=font, fill=BLACK)
    draw.text(EMAIL_OFFSET, email, font=font, fill=BLACK)

    # response = requests.get(url=f"https://eu.ui-avatars.com/api/?name={name}")
    response = requests.get(url=f"https://ui-avatars.com/api/?size=96&name={name}&font-size=0.33&background=17bee3"
                                f"&color=fff&rounded=true")

    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)
    # avatar.save('files/avatar_for_test.png', 'png')

    base.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


# print(generate_ticket('name', 'email'))

# def test_image_generation(self):
#     ticket_file = generate_ticket('name', 'email')
#https://ui-avatars.com/api/?size=96&name=name&font-size=0.33&background=17bee3"&color=fff&rounded=true
#     with open('files/ticket_example.png', 'rb') as expected_file:
#         assert ticket_file.read() == expected_file.read()