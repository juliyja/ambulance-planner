import re
from functools import reduce

import nltk
import gensim
import wget
from nltk import sent_tokenize
from gensim.models.word2vec import Word2Vec

from main.DatabaseUtil import get_cursor

threshold = 0.469

nltk.download('stopwords')
nltk.download('punkt')

cursor = get_cursor()
model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300-SLIM.bin', binary=True)

call_transcript = """none
"""


def fetch_keywords_from_db():
    keywords = []
    keywords_map = {}
    negation_map = {}
    negated_keywords = set()
    cursor.execute("SELECT * FROM KEYWORD")
    rows = cursor.fetchall()
    for row in rows:
        keywords.append(row[0])
        keywords_map[row[0]] = row[1]
        keywords_map[row[2]] = row[3]
        negation_map[row[2]] = row[0]
        negation_map[row[0]] = row[2]
        negated_keywords.add(row[2])

    return keywords, keywords_map, negation_map, negated_keywords


keywords, keywords_map, negation_map, negated_keywords = fetch_keywords_from_db()


def categorizeAccident(transcript):
    # add manoeuvre as a word embedding for american maneuver
    update_word_model('maneuver', 'manoeuvre')
    test_model()
    divided_text = createConversationList(transcript)
    found_keywords = generateKeywords(divided_text)
    print(found_keywords)
    found_keywords = map_found_keywords(found_keywords)
    accident_type = match_accident_info(found_keywords, "ACCIDENT_TYPE")
    found_keywords.add(accident_type.lower())
    print("FOUND: ", found_keywords)
    category = match_accident_info(found_keywords, "ACCIDENT_CATEGORY")
    transport_type = find_transport_type(accident_type, category)
    print(transport_type)

    return accident_type, category, transport_type


# prepare
def prepareTextForProcessing(transcript):
    new_transcript = modifyRegex(transcript)

    stop_words = set(nltk.corpus.stopwords.words('english'))
    # add words frequently occurring in calls that do not carry any real meaning
    stop_words.update({"please", "help", "hurry", "quick", "hello", "erm"})
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
    transcript = re.sub(r'\([^(\))]*\)', '', transcript)
    # remove square brackets and text within them
    new_transcript = re.sub(r'\[[^(\])]*\]', '', transcript)
    print(new_transcript)
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
    found_keywords = set()
    question = []
    simple_answer = ["yes", "no", "not know"]
    skip_keyword = False

    for item in qa_list:
        sentence = item[1]
        if question:
            checkAnswer(question, simple_answer, sentence, found_keywords)
        check_sentence(found_keywords, item, question, sentence, skip_keyword)

    return found_keywords


def check_sentence(found_keywords, item, question, sentence, skip_keyword):
    for i in range(len(sentence)):
        keyword = None
        if skip_keyword:
            skip_keyword = False
            continue
        if sentence[i] == "not":
            i += 1
            after_not = findBestKeyword(sentence, keywords, i)[0]
            if after_not:
                keyword = "not " + after_not
                skip_keyword = True
        else:
            keyword = findBestKeyword(sentence, keywords, i)[0]
        # find keywords for operator's questions
        if item[0] == "o":
            if keyword:
                question.append(keyword)
        # find keywords for caller's remarks
        if item[0] == "c":
            if keyword:
                found_keywords.add(keyword)
                print("JULIA JEST LEPSZA NIZ SZYMON", sentence[i], "FOR KEYWORD", keyword)


def checkAnswer(question, simple_answer, sentence, found_keywords):
    answers = {"yes": 0, "no": 0, "not know": 0}
    for index in range(len(sentence)):
        answer, cosine = findBestKeyword(sentence, simple_answer, index)
        print("ANSWER:", answer, "QUESTION: ", question)
        if answer:
            answers[answer] = max(answers[answer], cosine)
            print(answers[answer])
        index += 1
    print("DUZY SZYMON", answers)
    if answers["yes"] > answers["no"] and answers["yes"] > answers["not know"]:
        found_keywords.update(question)
    elif answers["no"] > answers["yes"] and answers["no"] > answers["not know"]:
        for w in question:
            w = negation_map[w]
            found_keywords.add(w)
    question.clear()


# use word2vec in order to find whether a word from the remark matches any of the preset keyword
def findBestKeyword(sentence, keywords, index):
    best_keyword = max(keywords, key=lambda keyword: findCosineSimiliarity(sentence, keyword, index))
    cosine_similiarity = findCosineSimiliarity(sentence, best_keyword, index)
    if cosine_similiarity > threshold:
        return best_keyword, cosine_similiarity
    return None, 0


def findCosineSimiliarity(sentence, keyword, index):
    try:
        sum_cosines = 0
        list = keyword.split()
        for k in list:
            if index < len(sentence):
                cosine = model.similarity(sentence[index], k)
                if cosine < threshold:
                    return 0
                sum_cosines += cosine
                # print(sentence[index], k, cosine)
                index += 1
            else:
                return 0
        average = sum_cosines / len(list)
        return average

    except KeyError:
        print("keyword \"" + keyword + "\" or word \"" + sentence[index] + "\" not in vocabulary")
        return 0


def map_found_keywords(found_keywords):
    mapped_keyword_list = set(map(keywords_map.get, found_keywords))
    return mapped_keyword_list


def match_accident_info(found_keywords, table):
    types_map = {}
    print(found_keywords)
    for k in found_keywords:
        negated = False
        if k in negated_keywords:
            k = negation_map[k]
            negated = True
        cursor.execute("SELECT * FROM " + table + " WHERE RELATED_KEYWORD = '" + k + "'")
        rows = cursor.fetchall()
        for row in rows:
            if row[1] not in types_map:
                types_map[row[1]] = 0
            types_map[row[1]] += row[4] if negated else row[3]

    print(types_map)
    best_type = max(types_map, key=types_map.get)
    print(best_type)
    print(found_keywords)
    return best_type


def find_transport_type(type, category):
    cursor.execute(
        "SELECT TRANSPORT_TYPE FROM TRANSPORT_TYPE_MAPPING WHERE TYPE = '" + type + "' OR CATEGORY = '" + str(
            category) + "'")
    rows = cursor.fetchall()
    if len(rows) > 1:
        transport_type = reduce(lambda x, y: x[0] | y[0], rows)
    else:
        return rows[0][0]
    return transport_type


def test_model():
    word_1 = "burns"
    word_2 = "abrasions"
    print("cosine similarity between " + word_1 + " and " + word_2 + " is: " + str(model.similarity(word_1, word_2)))


# update similar words to have the same vector embedding such as British spelling and American spelling
def update_word_model(word, new_word):
    model.add(new_word, model.get_vector(word), replace=False)
