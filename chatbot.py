import re
from collections import Counter
import string
from string import punctuation
from math import sqrt
import hashlib
import sys

weight = 0
chat_state = 0
status = False

# Based on a blog-post Here: http://rodic.fr/blog/python-chatbot-1/

import utils  # General utils including config params and database connection
conf = utils.get_config()

ACCURACY_THRESHOLD = 0.03
NO_DATA = "Sorry I don't know what to say"

toBool = lambda str: True if str == "True" else False # str 변수값이 t면 t반환, f면 f반환
#람다식 https://offbyone.tistory.com/73 참조

DEBUG_ASSOC = toBool(conf["DEBUG"]["assoc"])
DEBUG_WEIGHT = toBool(conf["DEBUG"]["weight"])
DEBUG_ITEMID = toBool(conf["DEBUG"]["itemid"])
DEBUG_MATCH = toBool(conf["DEBUG"]["match"])#각각의 변수에 저 boolean값들을 셋팅한듯.

#Strip non-alpha chars out - basic protection for SQL strings built out of concat ops
##clean = lambda str: ''.join(ch for ch in str if ch.isalnum())

#
# def train_me(inputSentence, responseSentence, cursor):
#     print("질문 : ",inputSentence)
#     print("대답 : ",responseSentence)

def chat_flow(cursor, humanSentence):
    status = False
    if(humanSentence == '1'): #사용자가 1번 1. 이런식으로 다양하게 쓸 수도 있으니까 정규식으로 숫자만 거르게함
        print("음식명으로 레시피 찾아줌")#여기에 재료명으로 레시피 찾는 메소드 호출
        ##재료도 입력할지 여부를 받고

        #레시피명과 일치하는 칼럼들중에, 만약 사용자가 재료도 입력했다면
        #재료도 데이터베이스에 넘겨주고, 재료 테이블에서 재료들과 비교하여 사용자가 넘겨준 재료의 80 %이상인 재료를 가진 레시피 정보를
        #모두 모아서  재료와 레시피명이 가장 일치하는것들을 기준으로 정렬하고,
        # 만약 같은 정확도라면 별점.댓글수를 기준으로 높은것들을 정렬하여 쳇봇에게 넘겨주기

        #이걸 sql 로 전부 해서 줘야겠지..
        status = True
    elif(humanSentence == '2'):
        print("재료명으로 레시피 찾아줌")
        status = True
    botSentence="크림파스타 url 출력하기 "

    print(status)
    return botSentence, status

if __name__ == "__main__":

    conf = utils.get_config()

    DBHOST = conf["MySQL"]["server"]
    DBUSER = conf["MySQL"]["dbuser"]
    DBNAME = conf["MySQL"]["dbname"]

    print("Starting Bot...")
    # initialize the connection to the database
    print("Connecting to database...")
    connection = utils.db_connection(DBHOST, DBUSER, DBNAME)
    cursor = connection.cursor()
    connectionID = utils.db_connectionID(cursor)
    print("...connected")

    status = False
    botSentence = '안녕 나는 냠냠봇이야!^^ 찾는 레시피 있니?\n' \
                  '1. 찾는 레시피명\n' \
                  '2. 가지고 있는 재료'
    while True:

        print('Bot> ' ,status,botSentence)# 봇 :  안녕 나는 냠냠봇이야
        if status:
            print("더 물어볼게 있니? [y/n]")
            humanSentence = input('>>> ').strip()
            if(humanSentence == 'y' ):
                print('안녕 나는 냠냠봇이야!^^ 찾는 레시피 있니?\n' \
                  '1. 찾는 레시피명\n' \
                  '2. 가지고 있는 재료')
            elif (humanSentence == 'n'):
                break

        # if trainMe:
        #     print('Bot> 나에게 알려줄래?')
        #     previousSentence = humanSentence
        #     humanSentence = input('>>>').strip()
        #
        #     if len(humanSentence) > 0:
        #         train_me(previousSentence, humanSentence, cursor)
        #         print("Bot> 더 찾고싶은 레시피가 있으면 말해줘")
        #     else:
        #         print("Bot> OK, moving on...")
        #         trainMe = False

        # Ask for user input; if blank line, exit the loop
        humanSentence = input('>>> ').strip() #.strip()양쪽 공백을 없애는것 #사용자가 질문함.
        # if humanSentence == '' or humanSentence.strip(punctuation).lower() == 'quit' or humanSentence.strip(punctuation).lower() == 'exit': #punctuation = 특수문자들
        #     break #사용자가 그냥 엔터치거나 quit나 exit를 치면 채팅이 종료됨.

        botSentence, status = chat_flow(cursor, humanSentence) #weight의 처음 값은 0

        connection.commit()
