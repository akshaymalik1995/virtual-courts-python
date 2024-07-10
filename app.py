from flask import Flask, jsonify, Response, make_response, request
import requests
import uuid
import base64
from flasgger import Swagger

# Go to localhost:5000/apidocs to see the swagger documentation

app = Flask(__name__)
swagger = Swagger(app)


captcha = "https://vcourts.gov.in/virtualcourt/securimage/securimage_show.php"


sessions = {}


@app.route("/api/v1/get_info", methods=["POST"])
def get_info():
    """
    Fetches challan information based on the provided details
    ---
    tags:
      - Information Retrieval
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: The required details for fetching information
        required: true
        schema:
          type: object
          required:
            - id
            - x
            - challan_no
            - vehicle_no
            - v_token
            - captcha
          properties:
            session_id:
              type: string
              description: Session ID

            x:
              type: "string"
              description: Operation to be performed. Example - "fetchpolicecases"
            challan_no:
              type: string
              description: Challan number
            vehicle_no:
              type: string
              description: Vehicle number Example - "HR55AK5584"
            v_token:
              type: string
              description: Verification token Example - "HRVC01"
            captcha:
              type: string
              description: Captcha code Example - "1234"
    responses:
      200:
        description: Information retrieved successfully
        schema:
          type: object
          properties:
            data:
              type: string
              description: The fetched information
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
      500:
        description: Error in fetching information
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    id = request.json.get("session_id")
    x = request.json.get("x")
    challan_no = request.json.get("challan_no")
    vehicle_no = request.json.get("vehicle_no")
    v_token = request.json.get("v_token")
    captcha = request.json.get("captcha")

    session = sessions.get(id)
    if session is None:
        return jsonify({"error": "Invalid session id"})

    # post_data = {
    #     "x": "fetchpolicecases",
    #
    #     "challan_no": "",
    #     "vehicle_no": "",
    #     "vajax": "Y",
    #     "v_token": "HRVC01",
    #     "fcaptcha_code": captcha,
    # }

    post_data = {
        "x": x,
        "challan_no": challan_no,
        "vehicle_no": vehicle_no,
        "vajax": "Y",
        "v_token": v_token,
        "fcaptcha_code": captcha,
    }

    try:
        response = session.post(
            "https://vcourts.gov.in/virtualcourt/admin/mobilesearchajax.php",
            data=post_data,
        )

        print(response.text)
        return jsonify(response.text)
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})


@app.route("/api/v1/get_captcha", methods=["POST"])
def virtual_courts():
    """
    Fetches a captcha image for the virtual courts system
    ---
    tags:
      - Captcha
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: State code to fetch the captcha for
        required: true
        schema:
          type: object
          required:
            - state_code
          properties:
            state_code:
              type: string
              description: The state code for which the captcha is requested
    responses:
      200:
        description: Captcha image and session ID
        schema:
          type: object
          properties:
            session_id:
              type: string
              description: Session ID for the captcha
            image:
              type: string
              description: Base64 encoded captcha image
      400:
        description: Error in fetching captcha
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    stateCode = request.json.get("state_code")  # 14~HRVC01
    session = requests.Session()
    id = str(uuid.uuid4())

    post_data = {
        "x": "setStateCode",
        "state_code": stateCode,
        "vajax": "Y",
        "v_token": "",
    }

    try:
        response = session.post(
            "https://vcourts.gov.in/virtualcourt/indexajax.php", data=post_data
        )

        print(response.text)

        response = session.get(captcha)

        image_base64 = base64.b64encode(response.content).decode("utf-8")

        sessions[id] = session
        cookies = session.cookies.get_dict()
        print(cookies["JSESSION"], cookies["PHPSESSID"])

        json_response = {
            "session_id": id,
            "image": "data:image/png;base64," + image_base64,
        }

        return jsonify(json_response)
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})


if __name__ == "__main__":
    app.run(debug=True)
