'''
Скрипт для проверки новых писем на Яндекс.почте и пересылке оповещений
в телеграм
'''

import os
import imaplib
import email
from email.header import decode_header

import telebot
from dotenv import load_dotenv


load_dotenv()


TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
IMAP_URL = os.environ.get('IMAP_URL')
YANDEX_LOGIN = os.environ.get('YANDEX_LOGIN')
YANDEX_PASSWORD = os.environ.get('YANDEX_PASSWORD')


def main():
    last_id = get_last_id()
    tg_bot = telebot.TeleBot(TG_BOT_TOKEN)
    tg_bot.config['api_key'] = TG_BOT_TOKEN
    list_data, imap = check_yandex_mail(last_id)
    count_new_emails = len(list_data)
    if count_new_emails:
        last_id = list_data[0]
        text_from_emails = make_text_from_emails(list_data, imap)
    if count_new_emails > 0:
        with open('last_id.txt', 'w', encoding='utf-8') as txt_file:
            txt_file.write(last_id)
        tg_bot.send_message(TG_CHAT_ID, text_from_emails)


def get_last_id():
    if os.path.isfile('last_id.txt'):
        with open('last_id.txt', 'r', encoding='utf-8') as txt_file:
            last_id = txt_file.read()
            return int(last_id)
    else:
        with open('last_id.txt', 'w', encoding='utf-8') as txt_file:
            last_id = '0'
            txt_file.write(last_id)
            return 0


def check_yandex_mail(last_id):
    imap = imaplib.IMAP4_SSL(IMAP_URL)
    imap.login(YANDEX_LOGIN, YANDEX_PASSWORD)
    imap.select('INBOX')
    result, data = imap.uid('search', None, 'ALL')
    str_list_data = data[0].decode()
    str_list_data = str_list_data.split()
    list_data = str_list_data[:]
    for num in str_list_data:
        if int(num) <= last_id:
            list_data.remove(num)
    list_data.sort(reverse=True)
    return list_data, imap


def make_text_from_emails(list_data, imap):
    text_from_emails = f'\n# New emails in {YANDEX_LOGIN}\n\n'
    for id_num in list_data:
        bstr = id_num.encode()
        result, data = imap.uid('fetch', bstr, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
        subj = None
        if email_message['Subject']:
            subj = decode_header(email_message['Subject'])
            if subj[0][1]:
                encoding = subj[0][1]
                try:
                    subj = subj[0][0].decode(encoding)
                except LookupError:
                    subj = '(decode error)'
            else:
                subj = subj[0][0]
        mfrom = decode_header(email_message['From'])
        if mfrom[0][1]:
            mencoding = mfrom[0][1]
            try:
                mfrom = mfrom[0][0].decode(mencoding)
            except LookupError:
                mfrom = '(decode error)'
        else:
            mencoding = 'ascii'
            mfrom = mfrom[0][0]
        text_from_emails += f'[From:] {mfrom} \n'
        if subj:
            text_from_emails += f'[Subject:] {subj} \n'
        text_from_emails += ('-' * 80) + '\n'
    return text_from_emails


if __name__ == '__main__':
    main()
