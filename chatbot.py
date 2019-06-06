import re
from collections import Counter
import string
from string import punctuation
from math import sqrt
import hashlib
import sys
import utils
import pymysql

weight = 0
chat_state = 0
status = False

# Based on a blog-post Here: http://rodic.fr/blog/python-chatbot-1/

import utils  # General utils including config params and database connection

conf = utils.get_config()

ACCURACY_THRESHOLD = 0.03
NO_DATA = "Sorry I don't know what to say"

toBool = lambda str: True if str == "True" else False  # str 변수값이 t면 t반환, f면 f반환
# 람다식 https://offbyone.tistory.com/73 참조

DEBUG_ASSOC = toBool(conf["DEBUG"]["assoc"])
DEBUG_WEIGHT = toBool(conf["DEBUG"]["weight"])
DEBUG_ITEMID = toBool(conf["DEBUG"]["itemid"])
DEBUG_MATCH = toBool(conf["DEBUG"]["match"])  # 각각의 변수에 저 boolean값들을 셋팅한듯.

DBHOST = conf["MySQL"]["server"]
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]

connection = utils.db_connection(DBHOST, DBUSER, DBNAME)
cursor = connection.cursor()
connectionID = utils.db_connectionID(cursor)


# Strip non-alpha chars out - basic protection for SQL strings built out of concat ops
##clean = lambda str: ''.join(ch for ch in str if ch.isalnum())

#
# def train_me(inputSentence, responseSentence, cursor):
#     print("질문 : ",inputSentence)
#     print("대답 : ",responseSentence)
def search_title_ingredient(humanIngredient, IngredientSelect_sub, cursor):

    IngredientScore = "("  # 이 변수는 select 문에 재료일치도 뽑아주기위해서 따로 만들어준것.
    IngredientSelect = "SELECT cooking_title,recipe_url,"

    for i in humanIngredient:
        IngredientScore += "(ingredient LIKE '%" + i.strip() + "%')+"  #
    IngredientScore = IngredientScore.rstrip('+')  # 맨마지막 재료뒤에도 붙어버린 +제거
    IngredientScore += ")/ingredient_num"
    IngredientSelect_sub += IngredientScore + ">=0.3  ORDER BY importance DESC"

    IngredientSelect += IngredientScore + " as ingredient_score" + IngredientSelect_sub  # 제목, 링크, 일치도 셀렉해줌
    #print('쿼리부분~~~~',IngredientSelect)

    cursor.execute(IngredientSelect)  # 여기서 실제로 쿼리문 실행
    result = cursor.fetchall()  # 이게 결과를 다 받는건강
    #print(result)

    return result, True, True  ##########################이부분도 해결해야됨. 전체 흐름도 좀 해결해야되고


def chat_flow(cursor, humanSentence):
    status = False
    if (humanSentence == '1'):  ########################### 1. 이런식으로 다양하게 쓸 수도 있으니까 정규식으로 숫자만 거르게해야함.
        #print("음식명으로 레시피 찾아줌")  ####################3여기에 재료명으로 레시피 찾는 메소드 호출. 즉 만들어뒀던걸 메소드화시키기
        ##재료도 입력할지 여부를 받고
        print("bot> 어떤 레시피가 궁금해? ")
        humanRecipe = input("you> 레시피 명 : ").strip('')
        print("bot> 재료도 입력할래?    [y/n]")
        humanRecipe2 = input("you> ").strip()  # 전처리

        if (humanRecipe2 == 'y' or humanRecipe2 == 'yes'):
            #search_ingredient(humanRecipe2,cursor)
            humanIngredient = input("bot> ,를 기준으로 재료 입력해줘 ex) 소고기,당근,배추,양파 ").strip()
            humanIngredient = humanIngredient.split(',')  # 문자 ,를 기준으로 리스트로 변경시킴.
            IngredientSelect_sub = " FROM mainrecipe m, title t WHERE " \
                                   " m.recipe_id = t.recipe_id " \
                                   "and searching_title like '%" + humanRecipe + "%' and"

            return search_title_ingredient(humanIngredient, IngredientSelect_sub, cursor)
                                # 찾는 레시피 제목, 사용자가 작성한 재료들, 제목+재료찾기용 쿼리문,  이걸 바로 리턴해버림

            # # 완성된 쿼리문 예시
            # # SELECT cooking_title,recipe_url
            # # FROM mainrecipe
            # # WHERE ((ingredient LIKE '%gredient LIKE '%식초%')+(ingredient LIKE '%물%')
            # # +(ingredient LIKE '%설탕%')+(ingredient LIKE '%올리고당%')+(ingredient LIKE '%다시마%')
            # # +(ingredient LIKE '%멸치가루%')+(ingredient LIKE '%양파%')+(ingredient LIKE '%대파%'))/ingredient_num >=0.8
            # # 작은 관호들의 결과는 재료가 있을경우 1, 없을 경우 0을 반환하여 최종적으로 나오는 결과는 db에서 재료문자열내에 존재하는
            # # 사용자입력재료들의 개수
            # # 저 식이 근데 잘못된거같으니 수정해야돼... 재료가 깻잎밖에 없는것도 뽑혀버렸어..ㅠㅠ
            #
            # #print(IngredientSelect)
            # cursor.execute(IngredientSelect)  # 여기서 실제로 쿼리문 실행
            # result = cursor.fetchall()  # 이게 결과를 다 받는건강
            # print(result)
            # return result, True  ##########################이부분도 해결해야됨. 전체 흐름도 좀 해결해야되고

        elif (humanRecipe2 == 'n' or humanRecipe2 == 'no'):
            print("bot> 선택하신 레시피 명은 ",humanRecipe," 입니다.")  # humanRecipe는 레시피 제목
            titleSelect = "select cooking_title, recipe_url from mainrecipe m, title t " \
                          "where m.recipe_id = t.recipe_id " \
                          "and searching_title like '%" + humanRecipe + "%'  ORDER BY importance DESC"

            # 니가 정리했떤 가중치를 db에서 나열을 해서가져오기,
            #print(titleSelect)
            cursor.execute(titleSelect)
            # 받아오기
            a = cursor.fetchone()
            #print(a)
            # 레시피명과 일치하는 칼럼들중에, 만약 사용자가 재료도 입력했다면
            # 재료도 데이터베이스에 넘겨주고, 재료 테이블에서 재료들과 비교하여 사용자가 넘겨준 재료의 80 %이상인 재료를 가진 레시피 정보를
            # 모두 모아서  재료와 레시피명이 가장 일치하는것들을 기준으로 정렬하고,
            # 만약 같은 정확도라면 별점.댓글수를 기준으로 높은것들을 정렬하여 쳇봇에게 넘겨주기

            # 이걸 sql 로 전부 해서 줘야겠지..
            status = True
            return a, status, True
    elif (humanSentence == '2'):

        print("bot> ,를 기준으로 재료 입력해줘 ex) 소고기,당근,배추,양파 ")
        humanIngredient = input("you> ")
        humanIngredient = humanIngredient.split(',')  # 문자 ,를 기준으로 리스트로 변경시킴.
        IngredientSelect_sub = " FROM mainrecipe WHERE " \

        return search_title_ingredient(humanIngredient, IngredientSelect_sub, cursor)


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

    info = False
    status = False #True 일 때 더 물어볼게 있니 라고 물어본다.
    botSentence = '안녕 나는 냠냠봇이야!^^ 찾는 레시피 있니?\n ' \
                  '1. 찾는 레시피명\n ' \
                  '2. 가지고 있는 재료' \
                  # 처음 챗봇이 할 말.
    while True:

        if info:
            if(len(botSentence)>5):
                for i in range(5):
                    print(" 제목 :", botSentence[i]['cooking_title'],"\n","링크 :", botSentence[i]['recipe_url'], "\n","일치도 :", botSentence[i]['ingredient_score'])

                print("bot> 원하는 번호를 입력해줘 \n 1. 레시피 더보기  2. 다른 레시피 찾아보기  3. 종료하기 ")
                humanSentence = input('you> ').strip()

                if(humanSentence == '1'):
                    for i in range(5, len(botSentence)):
                        print(" 제목 :", botSentence[i]['cooking_title'], "\n", "링크 :", botSentence[i]['recipe_url'],
                              "\n", "일치도 :", botSentence[i]['ingredient_score'])

                elif(humanSentence == '3'):
                    print("bot> 종료합니다")
                    break

            else:
                for i in range(len(botSentence)):
                    print(" 제목 :", botSentence[i]['cooking_title'], "\n","링크 :", botSentence[i]['recipe_url'], "\n",
                          "일치도 :", botSentence[i]['ingredient_score'], "\n")
        else:
            print('bot> ', botSentence)
        if status:
            print("bot> 더 물어볼게 있니? [y/n]")

            humanSentence = input('you> ').strip()
            if (humanSentence == 'y'):
                print('bot> 안녕 나는 냠냠봇이야!^^ 찾는 레시피 있니?\n'\
                      '1. 찾는 레시피명\n' \
                      '2. 가지고 있는 재료')
            elif (humanSentence == 'n'):
                print("bot> 챗봇을 종료합니다.")
                break #챗봇을 종료한다.

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
        humanSentence = input('you> ').strip()  # .strip()양쪽 공백을 없애는것 #사용자가 질문함.
        # if humanSentence == '' or humanSentence.strip(punctuation).lower() == 'quit' or humanSentence.strip(punctuation).lower() == 'exit': #punctuation = 특수문자들
        #     break #사용자가 그냥 엔터치거나 quit나 exit를 치면 채팅이 종료됨.

        # 1번, 1  / 2번 2 이렇게오면 정규식을 사용하여 숫자만 받기, 만약 그 외의 숫자나, 문자를 사용하면 다시 입력 하도록 요청하기

        botSentence, status, info = chat_flow(cursor, humanSentence)  # chat_flow에 cursor와 사용자가 입력한 값을 넘겨줌
                                                                # 그리고 챗봇이 대답할 말과 상태를 반환해줌.

        connection.commit()
