# # from flask import Flask, render_template, request, jsonify
# # import requests

# # app = Flask(__name__)

# # # FastAPI backend URL
# # BACKEND_URL = "http://127.0.0.1:8000/submit-questionnaire/"

# # @app.route("/", methods=["GET", "POST"])
# # def index():
# #     if request.method == "POST":
# #         form_data = request.form.to_dict()

# #         # Process form data for FastAPI
# #         form_data["employed"] = form_data.get("employed") == "on"
# #         form_data["shift_to_ai"] = form_data.get("shift_to_ai") == "on"

# #         # Convert empty fields to None
# #         for key, value in form_data.items():
# #             if value == "":
# #                 form_data[key] = None

# #         # Send data to the FastAPI backend
# #         response = requests.post(BACKEND_URL, json=form_data)
# #         if response.status_code == 200:
# #             result = response.json()
# #             return render_template("result.html", result=result)
# #         else:
# #             error = response.json().get("detail", "An error occurred.")
# #             return render_template("index.html", error=error)

# #     return render_template("index.html")

# # if __name__ == "__main__":
# #     app.run(debug=True, port=5001)

# from flask import Flask, render_template, request
# import requests

# app = Flask(__name__)

# # FastAPI backend endpoints
# QUESTIONNAIRE_API = "http://127.0.0.1:8000/submit-questionnaire/"
# UPLOAD_CV_API = "http://127.0.0.1:8000/upload-cv/"

# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         form_type = request.form.get("form_type")

#         if form_type == "questionnaire":
#             # Handle questionnaire submission
#             form_data = request.form.to_dict()
#             form_data["employed"] = form_data.get("employed") == "on"
#             form_data["shift_to_ai"] = form_data.get("shift_to_ai") == "on"
#             for key, value in form_data.items():
#                 if value == "":
#                     form_data[key] = None

#             response = requests.post(QUESTIONNAIRE_API, json=form_data)
#             if response.status_code == 200:
#                 result = response.json()
#                 return render_template("result.html", result=result["data"])
#             else:
#                 error = response.json().get("detail", "An error occurred.")
#                 return render_template("index.html", error=error)

#         elif form_type == "upload_cv":
#             # Handle CV upload
#             file = request.files.get("file")
#             if not file:
#                 return render_template("index.html", error="No file uploaded.")

#             response = requests.post(UPLOAD_CV_API, files={"file": (file.filename, file.stream, file.mimetype)})
#             if response.status_code == 200:
#                 result = response.json()
#                 return render_template("result.html", result=result["extracted_information"])
#             else:
#                 error = response.json().get("detail", "An error occurred.")
#                 return render_template("index.html", error=error)

#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True, port=5001)

from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000/submit/"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Prepare form data for submission
        form_data = request.form.to_dict()
        form_data["employed"] = form_data.get("employed") == "on"
        form_data["shift_to_ai"] = form_data.get("shift_to_ai") == "on"


        # Prepare files if provided
        files = {"file": request.files["file"]} if "file" in request.files and request.files["file"].filename else None

        try:
            # Send data to the FastAPI backend
            response = requests.post(BACKEND_URL, data=form_data, files=files)
            if response.status_code == 200:
                result = response.json()
                return render_template("result.html", result=result["data"])
            else:
                error = response.json().get("detail", "An error occurred.")
                return render_template("index.html", error=error)
        except Exception as e:
            return render_template("index.html", error=f"Error connecting to backend: {str(e)}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
