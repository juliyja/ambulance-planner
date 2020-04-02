import re
from functools import reduce

import nltk
import gensim

from main.DatabaseUtil import get_cursor

# minimum cosine similarity value between two words
threshold = 0.469

nltk.download('stopwords')
nltk.download('punkt')

cursor = get_cursor()
model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300-SLIM.bin', binary=True)

# TODO: delete this, this is only for testing
call_transcript = """none
"""


# fetch keywords stored in database and save them as a part of different data structures
# @return list of keywords, dictionary of keyword to keyword group, negation dictionary that stores mappings of
# negated keywords to keywords and keywords to negated keywords, set of negative keywords
# TODO: Add major and minor burns

def fetch_keywords_from_db():
    keywords_list = []
    keywords_dictionary = {}
    negation_dictionary = {}
    negated_keywords_set = set()
    cursor.execute("SELECT * FROM KEYWORD")
    rows = cursor.fetchall()
    for row in rows:
        # add keywords to list
        keywords_list.append(row[0])
        # assign keyword group values to keywords for both neutral and negated keywords
        keywords_dictionary[row[0]] = row[1]
        keywords_dictionary[row[2]] = row[3]
        # assign negated keywords to keywords and vice-versa
        negation_dictionary[row[2]] = row[0]
        negation_dictionary[row[0]] = row[2]
        # create set of negated keywords
        negated_keywords_set.add(row[2])

    return keywords_list, keywords_dictionary, negation_dictionary, negated_keywords_set


# save returned keywords structures
keywords, keywords_map, negation_map, negated_keywords = fetch_keywords_from_db()


# main method for text analysis using word2vec and nltk. It calls all the methods needed
# to process, analyse and categorise accident transcripts
# @param call_transcript
# @return accident information extracted from transcript: type of accident, category of accident and transport type

def categorize_accident(transcript):

    # add manoeuvre as a word embedding for american maneuver
    update_word_model('maneuver', 'manoeuvre')
    # TODO: to be removed once nlp is finished
    test_model()
    # prepare transcript
    prepared_text = prepare_text_for_processing(transcript)
    divided_text = create_conversation_list(prepared_text)

    # extract keywords from prepared transcript
    found_keywords = generate_keywords(divided_text)
    print(found_keywords)

    # map each keyword in found_keywords to it's respective group
    found_keywords = map_found_keywords(found_keywords)

    accident_type = match_accident_info(found_keywords, "ACCIDENT_TYPE")
    found_keywords.add(accident_type.lower())
    print("FOUND: ", found_keywords)
    category = match_accident_info(found_keywords, "ACCIDENT_CATEGORY")
    transport_type = find_transport_type(accident_type, category)
    print(transport_type)

    return accident_type, category, transport_type


# prepare transcript by modifying regex, removing any words that do not give any
# real meaning and are commonly used, punctuation and tokenize the text
# @return modified call transcript

def prepare_text_for_processing(transcript):
    new_transcript = modify_regex(transcript)

    stop_words = set(nltk.corpus.stopwords.words('english'))

    # TODO: remove also words such as ugh, hmmm, egh
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
    prepared_text = [w for w in words if w not in new_stop_words]

    return prepared_text


# Remove the useless expressions added in parenthesis by a person transcribing the call,
# such as "address removed" using regular expressions
# @return filtered transcript

def modify_regex(transcript):
    transcript = transcript.lower()
    # expand english language negative contractions such as can't into can not
    transcript = re.sub(r"'t", " not", transcript)
    # remove round brackets and text within them
    transcript = re.sub(r'\([^(\))]*\)', '', transcript)
    # remove square brackets and text within them
    new_transcript = re.sub(r'\[[^(\])]*\]', '', transcript)
    return new_transcript


# create list of questions and answers based on whether the caller
# or the operator made the remark
# @param simplified call transcript
# @return list of groups of words associated with either the caller or operator

def create_conversation_list(prepared_text):
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


# generate keywords for either operator's question or caller's answer

def generate_keywords(qa_list):
    found_keywords = set()
    question = []
    # main answers to search for in caller's remark
    simple_answer = ["yes", "no", "not know"]
    skip_keyword = False

    for remark in qa_list:
        sentence = remark[1]
        if question:
            check_answer(question, simple_answer, sentence, found_keywords)
        check_sentence(found_keywords, remark, question, sentence, skip_keyword)

    return found_keywords


# search caller remark for any words with high cosine similarity to answer words (yes, no, not know)
# @params list of keywords found in operator's question, list of three simple answers for
# yes, no and don't know, sentence to analyse, list of all already found keywords

def check_answer(question, simple_answer, sentence, found_keywords):
    answers = {"yes": 0, "no": 0, "not know": 0}
    for index in range(len(sentence)):
        answer, cosine = find_best_keyword(sentence, simple_answer, index)
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


# check sentence for any relevant keywords
# @param list of already found keywords, analysed remark with mark c for caller and o for operator,
# list of question keywords, sentence in remark associated with either caller or operator,
# flag whether next keyword should be skipped or not

def check_sentence(found_keywords, remark, question, sentence, skip_keyword):
    for i in range(len(sentence)):
        keyword = None
        if skip_keyword:
            skip_keyword = False
            continue
        # if word in the sentence is not check if the ones that immediately follow are any relevant keywords
        if sentence[i] == "not":
            i += 1
            after_not = find_best_keyword(sentence, keywords, i)[0]
            if after_not:
                keyword = "not " + after_not
                skip_keyword = True
        else:
            keyword = find_best_keyword(sentence, keywords, i)[0]
        # find keywords for operator's questions
        if remark[0] == "o":
            if keyword:
                question.append(keyword)
        # find keywords for caller's remarks
        if remark[0] == "c":
            if keyword:
                found_keywords.add(keyword)
                print("JULIA JEST LEPSZA NIZ SZYMON", sentence[i], "FOR KEYWORD", keyword)


# use word2vec in order to find whether a word from the remark matches any of the preset keyword

def find_best_keyword(sentence, keywords, index):
    best_keyword = max(keywords, key=lambda keyword: find_cosine_similiarity(sentence, keyword, index))
    cosine_similiarity = find_cosine_similiarity(sentence, best_keyword, index)
    if cosine_similiarity > threshold:
        return best_keyword, cosine_similiarity
    return None, 0


# find the cosine similarity between 2 words using word2vec
# @param sentence said by either operator or caller, keyword checked,
# index of the word to be checked from the sentence
# @return cosine similarity if it's above the threshold otherwise 0

def find_cosine_similiarity(sentence, keyword, index):

    try:
        sum_cosines = 0
        split_keyword_list = keyword.split()
        for k in split_keyword_list:
            if index < len(sentence):
                cosine = model.similarity(sentence[index], k)
                if cosine < threshold:
                    return 0
                sum_cosines += cosine
                # print(sentence[index], k, cosine)
                index += 1
            else:
                return 0
        average = sum_cosines / len(split_keyword_list)
        return average

    # catch exception if either the keyword or the word in a sentence does not exist
    except KeyError:
        print("keyword \"" + keyword + "\" or word \"" + sentence[index] + "\" not in vocabulary")
        return 0


# map each keyword from found keywords list to their respective group
# and so for instance not awake and not responding will both map to unconscious
# @param list of all found keywords

def map_found_keywords(found_keywords):
    mapped_keyword_list = set(map(keywords_map.get, found_keywords))
    return mapped_keyword_list


# check all keywords and calculate value for each type of accident or category based on the
# keywords that characterise them, return the one with the highest score
# @param list of all found keywords, table name in the database
# @return most probable type of the accident

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


# @param type of the accident found and the category found
# @return binary transport type value corresponding to the given type and category

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


# TODO: Remove after no more changes to nlp are to be made

def test_model():
    word_1 = "burns"
    word_2 = "abrasions"
    print("cosine similarity between " + word_1 + " and " + word_2 + " is: " + str(model.similarity(word_1, word_2)))


# update similar words to have the same vector embedding such as British spelling and American spelling
def update_word_model(word, new_word):
    model.add(new_word, model.get_vector(word), replace=False)
