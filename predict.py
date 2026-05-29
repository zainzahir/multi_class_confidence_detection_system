import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Load the model and preprocessing objects
def load_model():
    with open('model.pkl', 'rb') as file:
        saved_objects = pickle.load(file)
    return saved_objects

# Text preprocessing function
def preprocess_text(text, stemmer, stop_words):
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenize
    words = nltk.word_tokenize(text)
    
    # Remove stopwords and stem
    words = [stemmer.stem(word) for word in words if word not in stop_words]
    
    # Join back
    return ' '.join(words)

# Predict confidence level
def predict_confidence(text, model, vectorizer, label_mapping, stemmer, stop_words):
    # Preprocess the input text
    processed_text = preprocess_text(text, stemmer, stop_words)
    
    # Transform using the fitted vectorizer
    text_features = vectorizer.transform([processed_text])
    
    # Make prediction
    prediction_numeric = model.predict(text_features)[0]
    
    # Convert numeric prediction back to label
    reverse_mapping = {v: k for k, v in label_mapping.items()}
    predicted_label = reverse_mapping[prediction_numeric]
    
    # Get prediction probabilities
    probabilities = model.predict_proba(text_features)[0]
    confidence_score = max(probabilities) * 100
    
    return predicted_label, confidence_score

# Example usage
if __name__ == "__main__":
    # Load saved objects
    saved_objects = load_model()
    model = saved_objects['model']
    vectorizer = saved_objects['vectorizer']
    label_mapping = saved_objects['label_mapping']
    
    # Initialize NLP tools
    stemmer = PorterStemmer()
    stop_words = set(stopwords.words('english'))
    
    # Test examples
    test_texts = [
        "I am absolutely sure about this and can explain it perfectly",
        "I think this might be right but I'm not completely sure",
        "I have no idea what to do, this is very confusing"
    ]
    
    print("Testing predictions:")
    print("-" * 50)
    for text in test_texts:
        label, confidence = predict_confidence(text, model, vectorizer, label_mapping, stemmer, stop_words)
        print(f"Text: {text}")
        print(f"Predicted: {label} (Confidence: {confidence:.2f}%)\n")