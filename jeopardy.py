import json as j
import random
from gtts import gTTS
from io import BytesIO
import vlc
import time

# allow rewritting over lines instead of making new lines
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
MP3 = BytesIO()
PLAYER_TOTAL = 0
QUESTION_WORDS = ["what", "who", "when", "why", "how"]
ARTICLES = ["is", "are", "were", "was"]


class Question:

    def __init__(self, question, answer, value, category):
        self.question = question
        self.answer = answer
        self.value = value
        self.category = category
        self.daily_double = True

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
            try:
                json_questions = random.sample(cat_questions, num)

                cat_questions = []

                for quest in json_questions:
                    question = Question(
                        quest["question"], quest["answer"], quest["value"], quest["category"])
                    cat_questions.append(question)

            except ValueError:
                print("Error: too few questions for category: " + cat)

            if len(selected_questions) > 1:
                selected_questions.append(
                    sorted(cat_questions, key=lambda x: x.value))
            else:
                selected_questions.append(cat_questions)

        return selected_questions


def get_selection(board):

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
            return selection


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

    while True:
        if questions_answered == 1:
            if round == 0:

                print("Double Jeopardy!")
                tts = gTTS(
                    "Welcome to Double Jeopardy! In this round, question values are doubled.", lang="en", tld="co.uk")
                tts.save("double_jep.mp3")
                player = vlc.MediaPlayer("double_jep.mp3")
                player.play()

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

            else:
                board = ["FINAL JEOPARDY!"]

                categories = generate_categories("final_", 1)
                questions = generate_questions(categories, 1)

            round += 1
            questions_answered = 0

        display_board(board, categories)

        print("Player Total: " + str(PLAYER_TOTAL))

        selection = get_selection(board)
        selected_question = questions[int(
            selection[0]) - 1][int(selection[1]) - 1]

        display_question(selected_question, board[int(
            selection[1]) - 1][int(selection[0]) - 1])
        board[int(selection[1]) - 1][int(selection[0]) - 1] = "X"
        questions_answered += 1


def display_question(question, value):

    clear_line(8)

    if question.daily_double:
        player = vlc.MediaPlayer("daily_double.mp3")
        player.play()

        time.sleep(3)

        tts = gTTS("   How much would you like to wager?",
                   lang="en", tld="co.uk")
        tts.save("wager.mp3")
        player = vlc.MediaPlayer("wager.mp3")
        player.play()

        wait_for_tts(player)

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
        question.value = int(wager)

    print(question.question)

    tts = gTTS(question.question, lang="en", tld="co.uk")
    tts.save("question.mp3")
    player = vlc.MediaPlayer("question.mp3")
    player.play()

    wait_for_tts(player)

    get_player_input(question)
    clear_line(3)


def get_player_input(question):
    global PLAYER_TOTAL

    correct_answer = question.answer

    player_answer = input("Your answer: ")

    tts = gTTS(player_answer, lang="en", tld="com")
    tts.save("player_answer.mp3")
    player = vlc.MediaPlayer("player_answer.mp3")
    player.play()

    wait_for_tts(player)
    
    # TODO: implement FINAL JEOPARDY! value system
    # checks if players answer is correct and also it is in the form of a question, kinda messy, probably better way to do this
    if (player_answer.lower().split()[0] in QUESTION_WORDS and player_answer.lower().split()[1] in ARTICLES
        and player_answer == player_answer.lower().split()[0] + " " + player_answer.lower().split()[1] + " "
            + correct_answer.lower()):

        print("That is correct!")

        tts = gTTS("That is correct!", lang="en", tld="co.uk")
        tts.save("correct.mp3")
        player = vlc.MediaPlayer("correct.mp3")
        player.play()

        wait_for_tts(player)

        PLAYER_TOTAL += int(question.value)

    else:
        print("Sorry, that is incorrect. The correct answer was: " + question.answer)

        tts = gTTS("Sorry, that is incorrect. The correct answer was:",
                   lang="en", tld="co.uk")
        tts.save("incorrect.mp3")
        player = vlc.MediaPlayer("incorrect.mp3")
        player.play()

        wait_for_tts(player)
        PLAYER_TOTAL -= int(question.value)

        tts = gTTS(question.answer, lang="en", tld="co.uk")
        tts.save("answer.mp3")
        player = vlc.MediaPlayer("answer.mp3")
        player.play()

        wait_for_tts(player)


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
    time.sleep(0.5)
    duration = player.get_length() / 1000
    time.sleep(duration)


start_game()
