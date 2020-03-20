import re
import nltk

nltk.download('stopwords')
nltk.download('punkt')

call_transcript = "C: He is not breathing, [square brackets] help! (second dispatcher joins the call) O: Is he" \
                  " conscious? C: No, I don't think so"


def categorizeAccident():
    tokenize(call_transcript)


def tokenize(transcript):
    # Remove the useless expressions added in parenthesis by a
    # person transcribing the call, such as "address removed"
    transcript = transcript.lower()
    transcript = re.sub(r'\([^()]*\)', '', transcript)
    new_transcript = re.sub(r'\[[^()]*\]', '', transcript)

    # Remove stopwords leaving the ones needed to correctly classify accidents
    stop_words = set(nltk.corpus.stopwords.words('english'))
    exclude_words = {"no", "nor", "not"}
    new_stop_words = stop_words.difference(exclude_words)
    print(new_stop_words)

    # tokenize words in the transcript
    word_tokens = nltk.word_tokenize(new_transcript)
    # remove punctuation
    words = [word for word in word_tokens if word.isalpha()]
    filtered_sentence = [w for w in words if w not in new_stop_words]
    print(filtered_sentence)
