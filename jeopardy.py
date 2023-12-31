import json as j
import random
import time

from gtts import gTTS
import vlc
import speech_recognition as sr

from transformers import AutoModel, AutoTokenizer
import torch


# allow rewritting over lines instead of making new lines
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

#disables tts
DEBUG = True

PLAYER_TOTAL = 0
QUESTION_WORDS = set(["what", "who", "where", "when", "why", "how"])
ARTICLES = set(["is", "are", "were", "was"])

nlp_model = 'bert-base-uncased'

TOKENIZER = AutoTokenizer.from_pretrained(nlp_model)
MODEL = AutoModel.from_pretrained(nlp_model)
ANSWER_THRESHOLD = 0.8


class Question:

    def __init__(self, question, answer, value, category, round):
        self.question = question
        self.answer = answer
        self.value = value
        self.category = category
        self.daily_double = False
        self.round = round

    def __str__(self):
        return self.value


def generate_categories(round, num=5):
    with open(round+"jeopardy_cats.txt", "r", encoding="utf-8") as file:
        cats = file.readlines()
        chosen = random.sample(cats, num)

        for x in range(len(chosen)):
            chosen[x] = chosen[x].replace("\n", "")

    return chosen


def generate_questions(categories, num=5):
    with open("Questions.json", "r", encoding="utf-8") as json:
        all_questions = j.load(json)

        selected_questions = []

        for cat in categories:
            cat_questions = list(
                filter(lambda x: x["category"] == cat, all_questions))
            
            if round == "final":
                cat_questions = list(
                filter(lambda x: x["round"] == "Final Jeopardy!", cat_questions))
                
            try:
                json_questions = random.sample(cat_questions, num)

                cat_questions = []

                for quest in json_questions:
                    question = Question(
                        quest["question"], quest["answer"], quest["value"], quest["category"], quest["round"])
                    cat_questions.append(question)

            except ValueError:
                print("Error: too few questions for category: " + cat)

            if len(selected_questions) > 1:
                selected_questions.append(
                    sorted(cat_questions, key=lambda x: x.value))
            else:
                selected_questions.append(cat_questions)

        return selected_questions


def get_selection(board, categories):
    while True:
        selection = input("Please select the next question: ").split(",")

        if len(selection) != 2:
            clear_line(1)
            continue

        elif not (selection[0].isdigit() and selection[1].isdigit()):
            clear_line(1)
            continue

        elif board[int(selection[1]) - 1][int(selection[0]) - 1] == "X":
            clear_line(1)
            continue

        else:
            if board[0] != "FINAL JEOPARDY!":
                player = tts_speak(categories[int(selection[0]) - 1] + " for "
                                   + str(board[int(selection[0]) - 1][int(selection[1]) - 1]) + ", please.", "selection", "com")
                wait_for_tts(player)

            return selection


def display_question(question, value):
    clear_line(8)

    if question.daily_double:
        player = vlc.MediaPlayer("audio/daily_double.mp3")
        player.play()

        time.sleep(3)

        player = tts_speak(
            "   You have found a Daily Double. How much would you like to wager?", "wager", "co.uk")
        wait_for_tts(player)

        question.value = get_wager()
    
    elif question.round == "Final Jeopardy!":
        
        question.value = get_wager()

    print(question.category)
    print(question.question)

    player = tts_speak(question.question, "question", "co.uk")
    wait_for_tts(player)

    get_player_input(question)
    clear_line(4)


def get_wager():
    counter = 0
    
    while True:
        counter += 1
        wager = input("Enter your wager: ")
        
        if not wager.isdigit() or int(wager) < 0:
            print("Error: Please enter a positive integer!")
        elif int(wager) > PLAYER_TOTAL:
            max_wager = min(PLAYER_TOTAL, 1000)
            print(f"Error: Please enter a wager less than or equal to {max_wager}!")
        else:
            clear_line(counter)
            player = tts_speak(str(wager), "wager_amount", "com")
            wait_for_tts(player)

            return int(wager)  


def get_player_input(question):
    
    # player_answer = get_voice_answer()
    player_answer = input("Please enter your answer: ")
    
    player = tts_speak(player_answer, "player_answer", "com")
    wait_for_tts(player)
    
    correct_answer = question.answer

    if check_answer(player_answer, correct_answer):
        response = "That is correct!"
        response_type = "correct"
        PLAYER_TOTAL += int(question.value)
    else:
        response = f"Sorry, that is incorrect. The correct answer was: {question.answer}"
        response_type = "incorrect"
        PLAYER_TOTAL -= int(question.value)

    print(response)
    player = tts_speak(response, response_type, "co.uk")
    wait_for_tts(player)
    

def display_board(current_board, categories):
    cats = " | ".join(categories)

    print(cats)
    for row in current_board:
        board_row = ""

        if row == "FINAL JEOPARDY!":
            break

        for col, box in enumerate(row):

            # Answered Questions
            if box == "X":

                for x in range(len(categories[col])):
                    board_row += "X"

                board_row += " | "

            # Questions with values greater than 3 digits
            elif box > 999:

                for x in range(len(categories[col]) - 2):
                    if x == (len(categories[col]) // 2) - 1:
                        board_row += str(box)
                        x += 40
                    else:
                        board_row += " "
                board_row += "| "

            # Questions with values equal to 3 digits
            else:
                for x in range(len(categories[col]) - 1):

                    if x == len(categories[col]) // 2:
                        board_row += str(box)
                    else:
                        board_row += " "

                board_row += "| "
        print(board_row)
        
"""

UTILITY FUNCTIONs


"""       

def tokenize_string(string):
    return TOKENIZER(string, return_tensors="pt", padding=True, truncation=True)


def check_answer(player, correct):
    
    player = player.split()
    
    if (player[0] not in QUESTION_WORDS or player[1] not in ARTICLES):
        return False

    player = "".join(player[3:])
    
    player_input = tokenize_string(player)
    correct_answer = tokenize_string(correct)
    
    with torch.no_grad():
        player_embed = MODEL(**player_input).last_hidden_state.mean(dim=1)
        correct_embed = MODEL(**correct_answer).last_hidden_state.mean(dim=1)
        
    similarity = torch.nn.functional.cosine_similarity(player_embed, correct_embed)
    
    return similarity.item() >= ANSWER_THRESHOLD


def get_voice_answer():
    recog = sr.Recognizer()
    
    with sr.Microphone() as source:
        while True:
            answer = recog.listen(source, timeout=5)
            
            try:
                text_answer = recog.recognize_google(answer)
                print(text_answer)
                return text_answer
                
            except sr.UnknownValueError:
                print("Sorry, I couldn't understand what you said.")
          
          
# prints characters which clear previous lines
def clear_line(num):

    for x in range(num):
        print(LINE_UP, end=LINE_CLEAR)

# sleeps for length of tts message to avoid multiple messages speaking at once
def wait_for_tts(player):
    if player:
        time.sleep(0.5)
        duration = player.get_length() / 1000
        time.sleep(duration)
    
    elif DEBUG:
        time.sleep(2)


def tts_speak(text, filename, voice):
    if not DEBUG:
        tts = gTTS(text, lang="en", tld=voice)
        tts.save("audio/" + filename + ".mp3")
        player = vlc.MediaPlayer("audio/" + filename + ".mp3")
        player.play()

        return player
    else:
        return None
"""
ROUNDS

"""       
def single_jeopardy():
    PLAYER_TOTAL = 0
    questions_answered = 0
    
    categories = generate_categories("")
    board = [[200, 200, 200, 200, 200],
            [400, 400, 400, 400, 400],
            [600, 600, 600, 600, 600],
            [800, 800, 800, 800, 800],
            [1000, 1000, 1000, 1000, 1000]]

    questions = generate_questions(categories)

    for category in questions:
        for index, question in enumerate(category):
            question.value = (index + 1) * 200

    dd_question = random.choice(random.choice(questions))
    dd_question.daily_double = True

    player = tts_speak(f"The categories are: {str(categories)}", "categories", "co.uk")
    print(categories)
    wait_for_tts(player)

    clear_line(1)

    while questions_answered < 1:
        display_board(board, categories)
        print("Player Total: " + str(PLAYER_TOTAL))

        selection = get_selection(board, categories)
        selected_question = questions[int(selection[0]) - 1][int(selection[1]) - 1]

        display_question(selected_question, board[int(selection[1]) - 1][int(selection[0]) - 1])

        board[int(selection[1]) - 1][int(selection[0]) - 1] = "X"
        questions_answered += 1

    double_jeopardy()
        
def double_jeopardy():
    questions_answered = 0
    
    print("Double Jeopardy!")
    player = tts_speak("    Welcome to Double Jeopardy! "
                       "In this round, question values are doubled.", "double_jep", "co.uk")
    
    wait_for_tts(player)
    clear_line(2)

    board = [[400, 400, 400, 400, 400],
             [800, 800, 800, 800, 800],
             [1200, 1200, 1200, 1200, 1200],
             [1600, 1600, 1600, 1600, 1600],
             [2000, 2000, 2000, 2000, 2000]]

    categories = generate_categories("double_")
    questions = generate_questions(categories)

    for category in questions:
        for index, question in enumerate(category):
            question.value = (index + 1) * 400

        dd_question = random.choice(random.choice(questions))
        dd_question.daily_double = True

        dd_question_2 = random.choice(random.choice(questions))
                
        while(dd_question_2.daily_double):
            dd_question_2 = random.choice(random.choice(questions))
            dd_question.daily_double = True
            
    player = tts_speak(f"    The categories are: {str(categories)}", "categories", "co.uk")
    print(categories)
    wait_for_tts(player)

    clear_line(1)
        
    while questions_answered < 1:
        display_board(board, categories)

        print("Player Total: " + str(PLAYER_TOTAL))

        selection = get_selection(board, categories)
        selected_question = questions[int(
            selection[0]) - 1][int(selection[1]) - 1]

        display_question(selected_question, board[int(
            selection[1]) - 1][int(selection[0]) - 1])
        
        board[int(selection[1]) - 1][int(selection[0]) - 1] = "X"
        questions_answered += 1
    
    final_jeopardy()
        
def final_jeopardy():
    board = ['FINAL JEOPARDY!']
    
    categories = generate_categories("final_", 1)
    questions = generate_questions(categories, 1)
    
    player = tts_speak(f"    Our Final Jeopardy! category is: {str(categories)}", "categories", "co.uk")
    print(categories)
    wait_for_tts(player)
    
    selection = get_selection(board, categories)
    selected_question = questions[int(
        selection[0]) - 1][int(selection[1]) - 1]

    display_question(selected_question, board[int(
        selection[1]) - 1][int(selection[0]) - 1])
    

single_jeopardy()
print(f"You won ${str(PLAYER_TOTAL)}")
