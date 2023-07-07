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
            cat_questions = list(filter(lambda x: x["category"] == cat, all_questions))
            try:
                cat_questions = random.sample(cat_questions, num)
            except ValueError:
                print("Error: too few questions for category: " + cat)
            
            selected_questions.append(sorted(cat_questions, key= lambda x: int(x["value"].replace("$", "").replace(",", ""))))  
            
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
    
    categories = generate_categories("")
    
    board = [[200, 200, 200, 200, 200],
             [400, 400, 400, 400, 400],
             [600, 600, 600, 600, 600],
             [800, 800, 800, 800, 800],
             [1000, 1000, 1000, 1000, 1000]]
    
    questions = generate_questions(categories)
    
    while True:
        display_board(board, categories)
        
        print("Player Total: " + str(PLAYER_TOTAL))
        
        selection = get_selection(board)
        selected_question = questions[int(selection[0]) - 1][int(selection[1]) - 1]
        
        display_question(selected_question, board[int(selection[1]) - 1][int(selection[0]) - 1])
        board[int(selection[1]) - 1][int(selection[0]) - 1] = "X"

def display_question(question, value):
    
        clear_line(8) 
        print(question["question"])
        
        tts = gTTS(question["question"], lang="en", tld="co.uk")
        tts.save("question.mp3")
        player = vlc.MediaPlayer("question.mp3")
        player.play()
    
        wait_for_tts(player)
        
        get_player_input(question, value)   
        clear_line(3)  

def get_player_input(question, value):
    global PLAYER_TOTAL
    
    correct_answer = question["answer"]
    
    player_answer = input("Your answer: ")
    
    tts = gTTS(player_answer, lang="en", tld="com")
    tts.save("player_answer.mp3")
    player = vlc.MediaPlayer("player_answer.mp3")
    player.play()
    
    wait_for_tts(player)
    
    if player_answer.lower() == "what is " + correct_answer.lower():
        print("That is correct!")
        
        tts = gTTS("That is correct!", lang="en", tld="co.uk")
        tts.save("correct.mp3")
        player = vlc.MediaPlayer("correct.mp3")
        player.play()
    
        wait_for_tts(player)
        
        PLAYER_TOTAL += int(value)
        
        
    else:
        print("Sorry, that is incorrect. The correct answer was: "  + question["answer"])
        
        tts = gTTS("Sorry, that is incorrect. The correct answer was:", lang="en", tld="co.uk")
        tts.save("incorrect.mp3")
        player = vlc.MediaPlayer("incorrect.mp3")
        player.play()
    
        wait_for_tts(player)
        PLAYER_TOTAL -= int(value)
        
        tts = gTTS(question["answer"], lang="en", tld="co.uk")
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
        
def clear_line(num):
    
    for x in range(num):
        print(LINE_UP, end=LINE_CLEAR)  

def wait_for_tts(player):
    time.sleep(0.5)
    duration = player.get_length() / 1000
    time.sleep(duration)
          
start_game()
        
    
