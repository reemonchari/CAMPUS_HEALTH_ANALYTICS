# Import necessary libraries
# flask - a micro web framework for Python
# request - to handle user input (incoming HTTP requests)
# jsonify - to convert Python dictionaries to JSON format for API responses
# pickle - to load the pre-trained machine learning model
# numpy - for numerical operations, especially for handling input data in the correct format for the model
# render_template - to display HTML pages from your backend
from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np

# Initialize the Flask application (creates the Flask web server)
app = Flask(__name__)

# Load the pre-trained saved model
with open("clinic_model.pkl", "rb") as file:
    model = pickle.load(file)

# Create home route (creates the default homepage)
@app.route('/')
def home():
    return render_template('index.html')  # Renders the index.html file when the home route is accessed

# Create prediction route (handles POST requests to make predictions using the model)
@app.route('/predict', methods=['POST'])
def predict():
        data = request.get_json()  # Receives input from frontend in JSON format
        
        # Extract features from the input data
        exam_period = data['exam_period']
        rainfall = data['rainfall']
        temperature = data['temperature']

        # Prepare the input data for prediction (model expects data in rows and columns format) so we create a 2D array with one row and three columns   
        features = np.array([[exam_period, rainfall, temperature]])
        
        # Make prediction of patient count
        prediction = model.predict(features)

        return jsonify({
             "predicted_patients": float(prediction[0])
             })

# Run the Flask application (starts the web server and listens for incoming requests)
if __name__ == '__main__':
    app.run(debug=True)