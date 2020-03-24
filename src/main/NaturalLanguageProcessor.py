import re
import nltk
import gensim
import wget

nltk.download('stopwords')
nltk.download('punkt')

model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300-SLIM.bin', binary=True)

call_transcript = """O: Hello, which service do you need?
C: I need an ambulance, quick!
O: What’s the problem? 
C: It’s my father. He’s unconscious. Maybe it’s a heart attack. 
O: Is he breathing? 
C: No, he is but very little 
O: OK. I need to ask you some questions. What’s your address? 
C: 24 Park Street. You turn right from the High Street and it’s on the left. Please hurry! 
O: Please stay calm. The ambulance is coming. Please listen carefully. Tell me what happened. 
C: We were watching TV. My dad had chest pains. Then he fell on the floor. 
O: Does he have a medical condition? 
C: Yes. He’s diabetic. 
O: Is he on his back? 
C: Yes he is. 
O: Good. Don’t move him. Where are you in the house? 
C: We’re in the living room. It’s at the front of the house. 
O: How old are you? 
C: I’m 14. 
O: How old is your dad? 
C: He’s 46. Please hurry! 
O: You’re doing very well. The ambulance is very near 
C: I can hear it now. Thank you! 
O: Good. Well done. Good bye. 
"""

keywords = ["heart", "attack", "breathing", "gunshot", "bleeding", "unconscious", "diabetes"]
found_keywords = set()



def categorizeAccident():

    divided_text = createConversationList(call_transcript)
    generateKeywords(divided_text)


# prepare
def prepareTextForProcessing(transcript):
    new_transcript = modifyRegex(transcript)

    stop_words = set(nltk.corpus.stopwords.words('english'))
    # add words frequently occurring in calls that do not carry any real meaning
    stop_words.update({"please", "help", "hurry", "quick", "hello"})
    # Remove stopwords leaving the ones needed to correctly classify accidents
    exclude_words = {"no", "nor", "not", "o"}
    new_stop_words = stop_words.difference(exclude_words)

    # tokenize words in the transcript
    word_tokens = nltk.word_tokenize(new_transcript)
    # remove punctuation
    words = [word for word in word_tokens if word.isalpha()]
    # remove stopwords
    filtered_sentence = [w for w in words if w not in new_stop_words]

    return filtered_sentence


# Remove the useless expressions added in parenthesis by a person transcribing the call,
# such as "address removed" using regular expressions

def modifyRegex(transcript):
    transcript = transcript.lower()
    # remove round brackets and text within them
    transcript = re.sub(r'\([^()]*\)', '', transcript)
    # remove square brackets and text within them
    new_transcript = re.sub(r'\[[^()]*\]', '', transcript)
    return new_transcript


# create list of questions and answers based on whether the caller
# or the operator made the remark

def createConversationList(transcript):

    prepared_text = prepareTextForProcessing(transcript)
    qa_list = []
    temp = []
    for w in prepared_text:
        if w == "c":
            flag = True
            if temp:
                qa_list.append(("o", temp))
                temp = []
        elif w == "o":
            flag = False
            if temp:
                qa_list.append(("c", temp))
                temp = []
        else:
            temp.append(w)
    if flag:
        qa_list.append(("c", temp))
    else:
        qa_list.append(("o", temp))
    print(qa_list)
    return qa_list


def generateKeywords(qa_list):

    question = []
    simple_answer = ["yes", "no"]
    for item in qa_list:
        for word in item[1]:
            keyword = findCosineSimiliarities(word, keywords)
            # find keywords for operator's questions
            if item[0] == "o":
                if keyword:
                    question.append(keyword)
            # find keywords for caller's remarks
            if item[0] == "c":
                if question:
                    checkAnswer(question, simple_answer, word)
                if keyword:
                    found_keywords.add(keyword)
    print(found_keywords)


def checkAnswer(question, simple_answer, word):
    answer = findCosineSimiliarities(word, simple_answer)
    if answer == "yes":
        found_keywords.update(question)
    elif answer:
        question1 = []
        for w in question:
            w = "not " + w
            question1.append(w)
        found_keywords.update(question1)
    question.clear()


# use word2vec in order to find whether a word from the remark matches any of the preset keyword
def findCosineSimiliarities(word, keywords):

    best_keyword = max(keywords, key=lambda keyword: model.similarity(word, keyword))
    if model.similarity(word, best_keyword) > 0.45:
        print(word, best_keyword, model.similarity(word, best_keyword))
        return best_keyword
