from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Step and validation data
steps = {
    1: {
        "description": "Preparation of Phenylacetone",
        "procedure": "1. Weigh 100 g of Phenylacetone using a precise balance. Ensure the weight is within the range of 95 g to 105 g.\n"
                     "2. Measure 200 mL of ethanol in a graduated cylinder. The volume should be within 180 mL to 220 mL.\n"
                     "3. Combine the Phenylacetone and ethanol in a round-bottom flask.\n"
                     "4. Heat the mixture to a reflux temperature of 78 °C (within 75 °C to 80 °C) for 2 hours (within 1.5 to 2.5 hours).\n"
                     "5. Allow the mixture to cool to room temperature.",
        "variables": {
            "Phenylacetone weight": (95.0, 105.0, "g"),
            "Ethanol volume": (180.0, 260.0, "mL"),
            "Reflux temperature": (75.0, 80.0, "°C"),
            "Reflux time": (1.5, 2.5, "hours")
        }
    },
    2: {
        "description": "Reaction with Hydroxylamine",
        "procedure": "1. Weigh 50 g of Hydroxylamine. Ensure the weight is between 45 g and 55 g.\n"
                     "2. Slowly add Hydroxylamine to the cooled Phenylacetone solution over a period of 30 minutes (between 25 and 35 minutes). Stir continuously.\n"
                     "3. Maintain the stirring temperature at room temperature (20 °C to 25 °C) for 2 hours (within 1.5 to 2.5 hours).",
        "variables": {
            "Hydroxylamine weight": (45.0, 55.0, "g"),
            "Addition time": (25.0, 35.0, "minutes"),
            "Stirring temperature": (20.0, 25.0, "°C"),
            "Stirring time": (1.5, 2.5, "hours")
        }
    },
    3: {
        "description": "Cyclization Reaction",
        "procedure": "1. Measure 100 mL of acetic acid (within 90 mL to 110 mL) and 25 mL of concentrated sulfuric acid (between 20 mL and 30 mL).\n"
                     "2. Add the acetic acid and sulfuric acid to the reaction mixture obtained from Step 2.\n"
                     "3. Heat the mixture to a reflux temperature of 130 °C (within 125 °C to 135 °C) and maintain for 4 hours (within 3.5 to 4.5 hours).",
        "variables": {
            "Acetic acid volume": (90.0, 110.0, "mL"),
            "Sulfuric acid volume": (20.0, 30.0, "mL"),
            "Reflux temperature": (125.0, 135.0, "°C"),
            "Reflux time": (3.5, 4.5, "hours")
        }
    },
    4: {
        "description": "Purification of Paracetamol",
        "procedure": "1. After refluxing, allow the mixture to cool to room temperature.\n"
                     "2. Set up a vacuum distillation apparatus to remove excess acetic acid. Ensure that the pressure is sufficient for effective removal.\n"
                     "3. Once the acetic acid is removed, wash the solid product with distilled water.\n"
                     "4. Crystallize the product from a hot aqueous solution, ensuring the temperature of the solution is around 70 °C (within 60 °C to 80 °C).",
        "variables": {
            "Vacuum distillation pressure": (0.5, 1.0, "atm"),  # Specify pressure as a range
            "Crystallization solvent": "Hot aqueous solution",  # Keep as a string, no validation needed
            "Crystallization temperature": (60.0, 80.0, "°C")
        }
    }
}

def load_image(image_file):
    img = Image.open(image_file)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def preprocess_image(image):
    """Apply preprocessing that includes adaptive thresholding and contour detection."""
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours and filter based on area size, then draw rectangles
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) > 100:  # adjust this threshold as needed
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # draws a rectangle on original image

    # Convert cv2 image back to PIL image for consistent encoding
    img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    buffer = BytesIO()
    img_pil.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def image_summarize(img_base64):
    """Make image summary using a chat model and invoke function definition."""
    prompt = """You are an assistant tasked with analyzing images of various digital and mechanical meters to 
    identify and record the main measurement displayed."""

    # Define the function that will be called
    function_definition = {
        "name": "extract_meter_measurement",
        "description": "Extracts the flow meter reading and units from an image.",
        "parameters": {
            "type": "object",
            "properties": {
                "measurement": {
                    "type": "string",
                    "description": "The numeric reading from the flow meter."
                },
                "units": {
                    "type": "string",
                    "description": "The units of measurement (e.g., L/min, GPM)."
                }
            },
            "required": ["measurement", "units"]
        }
    }

    # Initialize the chat model (ensure ChatOpenAI and related classes are properly imported)
    chat = ChatOpenAI(model="gpt-4o-mini", max_tokens=1024)

    # Define the human message with both prompt and the base64 image
    msg = chat.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            )
        ],
        functions=[function_definition]
    )
    
    if msg and msg.additional_kwargs and msg.additional_kwargs.get("function_call"):
      function_call = msg.additional_kwargs["function_call"]
      arguments = function_call.get("arguments")
    else:
        return "The uploaded image does not contain a digital or mechanical meter. Please upload an appropriate image."
    if arguments:
      import json
      arguments_dict = json.loads(arguments)
    else:
        return "The uploaded image does not contain a digital or mechanical meter. Please upload an appropriate image." 
    return arguments_dict["measurement"]




def validate_input(variable, user_input):
    if isinstance(variable, tuple):
        min_val, max_val, _ = variable
        return min_val <= user_input <= max_val
    return True

@app.route('/validate', methods=['POST'])
def validate_image():
    try:
        step_number = int(request.form['step_number'])
        variable = request.form['variable']
        file = request.files['file']
        image = load_image(file)
        extracted_measurement = image_summarize(preprocess_image(image))
        step_info = steps[step_number]
        variable_info = step_info["variables"].get(variable)
        if variable_info:
            try:
                measurement_value = float(extracted_measurement)
                is_valid = validate_input(variable_info, measurement_value)
                response = {
                    "valid": is_valid,
                    "measurement": measurement_value,
                    "units": variable_info[2]
                }
                return jsonify(response), 200
            except ValueError:
                return jsonify({"error": "Invalid measurement extracted."}), 400
        else:
            return jsonify({"error": "Invalid variable for the specified step."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
