import json as j
import random

def generate_categories(num_of_cats=5):
    with open("jeopardy_cats.txt", "r", encoding="utf-8") as file:
        cats = file.readlines()
        chosen = random.sample(cats, num_of_cats)
        
        for x in range(len(chosen)):
            chosen[x] = chosen[x].replace("\n", "")
            
    return chosen
 
def generate_questions(categories):   
    with open("Questions.json", "r", encoding="utf-8") as json:
        all_questions = j.load(json)
        
        selected_questions = []
        
        for cat in categories:
            cat_questions = list(filter(lambda x: x["category"] == cat, all_questions))
            cat_questions = random.sample(cat_questions, 5)
            
            selected_questions.append(sorted(cat_questions, key= lambda x: int(x["value"].replace("$", ""))))  
            
        return selected_questions
        
print(generate_questions(generate_categories()))         
        
    
