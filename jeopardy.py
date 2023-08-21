import json as j
import random
from gtts import gTTS
from io import BytesIO
import vlc
import time

# allow rewritting over lines instead of making new lines
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

#disables tts
DEBUG = False

PLAYER_TOTAL = 0
QUESTION_WORDS = ["what", "who", "where", "when", "why", "how"]
ARTICLES = ["is", "are", "were", "was"]


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


def generate_questions(categories, num=5, round=""):
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

    print(question.question)

    player = tts_speak(question.question, "question", "co.uk")
    wait_for_tts(player)

    get_player_input(question)
    clear_line(3)


def get_wager():

    counter = 0
    while True:
        counter += 1
        wager = input("Enter your wager: ")

        if not wager.isdigit():
            print("Error: Please enter an integer!")
            continue
        elif int(wager) > PLAYER_TOTAL:
            if PLAYER_TOTAL > 1000:
                print(
                    "Error: Please enter a wager less than your total: " + str(PLAYER_TOTAL))
                continue
            elif int(wager) > 1000:
                print("Error: Please enter a wager less than or equal to 1000! ")
                continue
        elif int(wager) < 0:
            print("Error: Please enter a wager greater than or equal to 0! ")
            continue

        break

    clear_line(counter)
    player = tts_speak(str(wager), "wager_amount", "com")
    wait_for_tts(player)

    return int(wager)


def get_player_input(question):
    global PLAYER_TOTAL

    correct_answer = question.answer

    player_answer = input("Your answer: ")

    player = tts_speak(player_answer, "player_answer", "com")
    wait_for_tts(player)

    # TODO: implement FINAL JEOPARDY! value system
    # checks if players answer is correct and also it is in the form of a question, kinda messy, probably better way to do this
    if (player_answer.lower().split()[0] in QUESTION_WORDS and player_answer.lower().split()[1] in ARTICLES
        and player_answer == player_answer.lower().split()[0] + " " + player_answer.lower().split()[1] + " "
            + correct_answer.lower()):

        print("That is correct!")

        player = tts_speak("That is correct!", "correct", "co.uk")
        wait_for_tts(player)

        PLAYER_TOTAL += int(question.value)

    else:
        print("Sorry, that is incorrect. The correct answer was: " + question.answer)

        player = tts_speak("Sorry, that is incorrect. The correct answer was: " +
                           question.answer, "incorrect", "co.uk")
        wait_for_tts(player)

        PLAYER_TOTAL -= int(question.value)


def display_board(current_board, categories):
    cats = ""

    for cat in categories:
        cats += cat + " | "

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


def tts_speak(text, filename, voice):
    if not DEBUG:
        tts = gTTS(text, lang="en", tld=voice)
        tts.save("audio/" + filename + ".mp3")
        player = vlc.MediaPlayer("audio/" + filename + ".mp3")
        player.play()

        return player
    else:
        return None


def start_game():
    global PLAYER_TOTAL
    questions_answered = 0
    round = 0

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

    player = tts_speak("    The categories are: " +
                       str(categories), "categories", "co.uk")
    print(categories)
    wait_for_tts(player)

    clear_line(1)

    while True:
        if questions_answered == 1:
            if round == 0:

                print("Double Jeopardy!")
                player = tts_speak(
                    "    Welcome to Double Jeopardy! In this round, question values are doubled.", "double_jep", "co.uk")
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

                player = tts_speak("    The categories are: " +
                                   str(categories), "categories", "co.uk")
                print(categories)
                wait_for_tts(player)

                clear_line(1)

            else:
                board = ["FINAL JEOPARDY!"]

                categories = generate_categories("final_", 1)
                questions = generate_questions(categories, 1, "final")

            round += 1
            questions_answered = 0

        display_board(board, categories)

        print("Player Total: " + str(PLAYER_TOTAL))

        selection = get_selection(board, categories)
        selected_question = questions[int(
            selection[0]) - 1][int(selection[1]) - 1]

        display_question(selected_question, board[int(
            selection[1]) - 1][int(selection[0]) - 1])
        
        if round == 2:
            return
        
        board[int(selection[1]) - 1][int(selection[0]) - 1] = "X"
        questions_answered += 1


start_game()
print("You won $" + str(PLAYER_TOTAL))
