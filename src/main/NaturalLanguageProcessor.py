import re
import nltk
import gensim
import wget
from nltk import sent_tokenize
from gensim.models.word2vec import Word2Vec

from main.RESTapi import get_cursor

nltk.download('stopwords')
nltk.download('punkt')

cursor = get_cursor()
model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300-SLIM.bin', binary=True)

call_transcript = """O: Hello, which service do you need?
C: I need an ambulance, quick!
O: What’s the problem? 
C: It’s my father. He’s not breathing. Maybe it’s a heart attack. 
O: Is he awake? 
C: no, he isn't
O: OK. I need to ask you some questions. What’s your address? 
C: 24 Park Street. You turn right from the High Street and it’s on the left. Please hurry! 
O: Please stay calm. The ambulance is coming. Please listen carefully. Tell me what happened. 
C: We were watching TV. My dad had chest pains. Then he fell on the floor. 
O: Does he have a medical condition? 
C: Yes. He is diabetic. 
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

found_keywords = set()


def fetch_keywords_from_db():

    keywords = []
    keywords_map = {}
    negation_map = {}
    cursor.execute("SELECT * FROM KEYWORD")
    rows = cursor.fetchall()
    for row in rows:
        keywords.append(row[0])
        keywords_map[row[0]] = row[1]
        keywords_map[row[2]] = row[3]
        negation_map[row[2]] = row[0]

    return keywords, keywords_map, negation_map


keywords, keywords_map, negation_map = fetch_keywords_from_db()


def categorizeAccident():

    # add manoeuvre as a word embedding for american maneuver
    update_word_model('maneuver', 'manoeuvre')
    test_model()
    divided_text = createConversationList(call_transcript)
    generateKeywords(divided_text)
    final_keywords = map_found_keywords()
    accident_type = assign_type(final_keywords)


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
    # expand english language negative contractions such as can't into can not
    transcript = re.sub(r"'t", " not", transcript)
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
    skip_keyword = False

    for item in qa_list:
        for i in range(len(item[1])):
            keyword = None
            sentence = item[1]
            if skip_keyword:
                skip_keyword = False
                continue
            if sentence[i] == "not":
                i += 1
                after_not = findBestKeyword(sentence, keywords, i)
                if after_not:
                    keyword = "not " + after_not
                    skip_keyword = True
            else:
                keyword = findBestKeyword(sentence, keywords, i)
            # find keywords for operator's questions
            if item[0] == "o":
                if keyword:
                    question.append(keyword)
            # find keywords for caller's remarks
            if item[0] == "c":
                if question:
                    checkAnswer(question, simple_answer, sentence, i)
                if keyword:
                    found_keywords.add(keyword)
    print(found_keywords)


def checkAnswer(question, simple_answer, sentence, index):
    answer = findBestKeyword(sentence, simple_answer, index)
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
def findBestKeyword(sentence, keywords, index):

    best_keyword = max(keywords, key=lambda keyword: findCosineSimiliarity(sentence, keyword, index))
    if findCosineSimiliarity(sentence, best_keyword, index) > 0.45:
        return best_keyword


def findCosineSimiliarity(sentence, keyword, index):

    try:
        sum_cosines = 0
        list = keyword.split()
        for k in list:
            if index < len(sentence):
                cosine = model.similarity(sentence[index], k)
                sum_cosines += cosine
                # print(sentence[index], k, cosine)
                index += 1
            else:
                return 0
        average = sum_cosines/len(list)
        return average

    except KeyError:
        print("keyword \"" + keyword + "\" or word \"" + sentence[index] + "\" not in vocabulary")
        return 0


def map_found_keywords():
    mapped_keyword_list = set(map(keywords_map.get, found_keywords))
    return mapped_keyword_list


def assign_type(found_keywords):

    types_map = {}
    for k in found_keywords:
        negated = False
        if k in negation_map:
            k = negation_map[k]
            negated = True
        cursor.execute("SELECT * FROM ACCIDENT_TYPE WHERE RELATED_KEYWORD = '" + k + "'")
        rows = cursor.fetchall()
        for row in rows:
            if row[1] not in types_map:
                types_map[row[1]] = 0
            types_map[row[1]] += row[4] if negated else row[3]

    print(types_map)
    best_type = max(types_map, key=types_map.get)
    print(best_type)
    return best_type


def assign_category():
    category = None
    return category


def test_model():

    word_1 = "diabetic"
    word_2 = "diabetes"
    print("cosine similarity between " + word_1 + " and " + word_2 + " is: " + str(model.similarity(word_1, word_2)))


# update similiar words to have the same vector embedding such as British spelling and American spelling
def update_word_model(word, new_word):
    model.add(new_word, model.get_vector(word), replace=False)

