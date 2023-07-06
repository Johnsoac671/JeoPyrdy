import json as j
import random
import sys

# allow rewritting over lines instead of making new lines
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K' 
        
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
            cat_questions = random.sample(cat_questions, num)
            
            selected_questions.append(sorted(cat_questions, key= lambda x: int(x["value"].replace("$", "").replace(",", ""))))  
            
        return selected_questions 

def start_game():
    categories = generate_categories("")
    board = [[200, 200, 200, 200, 200], [400, 400, 400, 400, 400], [600, 600, 600, 600, 600], [800, 800, 800, 800, 800], [1000, 1000, 1000, 1000, 1000]]
    questions = generate_questions(categories)
    
    while True:
        display_board(board, categories)
        
        selection = input().split(",")
        selected_question = questions[int(selection[1]) - 1][int(selection[0]) - 1]
        
        display_question(selected_question)
        board[int(selection[1]) - 1][int(selection[0]) - 1] = "X"

def display_question(question):
    
        for x in range(7):
           print(LINE_UP, end=LINE_CLEAR)
           
        print(question["question"])
        input()
        
        for x in range(2):
            print(LINE_UP, end=LINE_CLEAR)
        
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
    
start_game()
        
    
