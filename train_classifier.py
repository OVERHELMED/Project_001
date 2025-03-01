import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load the dataset
data_dict = pickle.load(open('./data.pickle', 'rb'))
data = data_dict['data']
labels = data_dict['labels']

# Ensure all data samples have the same length
max_length = max(len(sample) for sample in data)
data = [np.pad(sample, (0, max_length - len(sample)), mode='constant') for sample in data]

# Convert to NumPy arrays
data = np.array(data, dtype=np.float32)
labels = np.array(labels)

# Split dataset
x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, shuffle=True, stratify=labels)

# Train model
model = RandomForestClassifier()
model.fit(x_train, y_train)

# Evaluate model
y_predict = model.predict(x_test)
score = accuracy_score(y_predict, y_test)
print(f'{score * 100:.2f}% of samples were classified correctly!')

# Save trained model
with open('model.p', 'wb') as f:
    pickle.dump({'model': model}, f)
