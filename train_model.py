import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import pickle
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
print("Downloading NLTK data...")
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Load dataset
print("Loading dataset...")
df = pd.read_csv('dataset.csv')

# Text preprocessing function
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
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

# Preprocess all texts
print("Preprocessing text data...")
df['processed_text'] = df['text'].apply(preprocess_text)

print(f"Dataset shape: {df.shape}")
print(f"\nClass distribution:")
print(df['confidence_level'].value_counts())

# Prepare features and labels
X = df['processed_text']
y = df['confidence_level']

# Convert labels to numeric
label_mapping = {
    'Low Confidence': 0,
    'Medium Confidence': 1,
    'High Confidence': 2
}
y_numeric = y.map(label_mapping)

# Create TF-IDF features
print("\nExtracting features using TF-IDF...")
vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
X_features = vectorizer.fit_transform(X)

print(f"Feature matrix shape: {X_features.shape}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_features, y_numeric, test_size=0.2, random_state=42, stratify=y_numeric
)

print(f"Training set size: {X_train.shape[0]}")
print(f"Test set size: {X_test.shape[0]}")

# Train model - Fixed for multiclass classification
print("\nTraining Logistic Regression model...")

# Use 'lbfgs' solver which supports multiclass classification
# Other options: 'newton-cg', 'sag', 'saga'
model = LogisticRegression(
    C=50.0,
    solver='lbfgs',     # 'lbfgs' supports multiclass
    max_iter=1000,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy:.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=label_mapping.keys()))

# Save model, vectorizer, and label mapping
print("\nSaving model and preprocessing objects...")
with open('model.pkl', 'wb') as file:
    pickle.dump({
        'model': model,
        'vectorizer': vectorizer,
        'label_mapping': label_mapping
    }, file)

print("Model saved successfully as 'model.pkl'")

# Test with sample inputs
print("\n" + "="*50)
print("Testing model with sample inputs:")
print("="*50)

test_samples = [
    "I am absolutely certain about this solution and can explain it perfectly",
    "I think this might be correct but I need to review some concepts",
    "I have no idea what to do, this is very confusing"
]

reverse_mapping = {v: k for k, v in label_mapping.items()}

for sample in test_samples:
    processed = preprocess_text(sample)
    features = vectorizer.transform([processed])
    pred_num = model.predict(features)[0]
    pred_label = reverse_mapping[pred_num]
    
    # Get probability
    proba = model.predict_proba(features)[0]
    confidence = max(proba) * 100
    
    print(f"\nInput: {sample}")
    print(f"Prediction: {pred_label}")
    print(f"Confidence: {confidence:.2f}%")