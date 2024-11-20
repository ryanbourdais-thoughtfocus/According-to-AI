import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

# Download necessary resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

# Sample transcript
transcript = """
---

> "Hello, I’m interested in learning more about your data analytics services. Could you give me an overview of what you offer?"

> "Of course! We offer a range of data analytics services, including data visualization, predictive modeling, and business intelligence reporting. Could you share more about your specific needs?"

> "Sure, we’re looking to improve our sales forecasting. Currently, we have some historical data, but we’re not sure how to turn that into useful insights."

> "That’s something we can definitely assist with. Our team can help analyze your historical data and build a predictive model tailored to your business goals. Would you like a consultation session to go over the details?"

> "Yes, that sounds great. I’d like to set up a consultation. When are you available?"

> "I’m available this Wednesday at 10 a.m. Does that work for you?"

> "Yes, that works perfectly. Thank you!"

---

This transcript only includes the conversation text. You can use this for testing without speaker labels. Let me know if you need further modifications!
"""

# Initialize lemmatizer and define stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Tokenize the text
words = word_tokenize(transcript)

# Remove stop words, lemmatize, and perform POS tagging
processed_transcript = []
for word in words:
    if word.lower() not in stop_words and word.isalnum():  # Removing stop words and non-alphanumeric characters
        lemmatized_word = lemmatizer.lemmatize(word.lower())  # Lemmatize the word
        processed_transcript.append(lemmatized_word)

# Reconstruct into a normal sentence
reconstructed_sentence = ' '.join(processed_transcript)

print("Reconstructed Sentence:")
print(reconstructed_sentence)
with open("reconstructed_sentence.txt", "w") as file:
    file.write(reconstructed_sentence)

print("Processed transcript saved to 'processed_transcript.txt'")