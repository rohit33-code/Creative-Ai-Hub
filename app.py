
from flask import Flask, render_template, request, session, redirect
import pymysql as sql
import requests
import base64
import re
from io import BytesIO
from flask import send_file
import uuid




app = Flask(__name__)
app.secret_key = "your_secret_key_here"
# ------------------ Session ko automatically expiry karne ke liye -------------------
from datetime import timedelta
app.permanent_session_lifetime = timedelta(hours=24)




# ------------------ HOME -------------------
@app.route("/")
def home():
    return render_template("index.html", active_page="home")


# ------------------ SIGNUP PAGE -------------------
@app.route("/signup")
def sign():
    return render_template("signup.html")


# ------------------ SIGNUP PROCESS -------------------
@app.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        conn = sql.connect(user="root", password="rohit", port=3306, database="pythoncreative")
        cur = conn.cursor()

        # ---- check if email already exists
        cur.execute("SELECT * FROM login WHERE email=%s", (email,))
        data = cur.fetchone()

        if data:
            return render_template("signup.html", msg="This email is already registered!")

        # ---- insert new user
        cur.execute("INSERT INTO login (email, password) VALUES (%s, %s)", (email, password))

        conn.commit()
        conn.close()

        return render_template("login.html", success="Signup successful! Please login.")

    except Exception as e:
        return render_template("signup.html", e=e)




# ------------------ LOGIN PROCESS -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = sql.connect(user="root", password="rohit", port=3306, database="pythoncreative")
            cur = conn.cursor()

            # ---- check email exists
            cur.execute("SELECT password FROM login WHERE email=%s", (email,))
            data = cur.fetchone()

            if not data:
                # email not found
                return render_template("login.html", email_error="Email not found!")

            db_password = data[0]

            # ---- check password
            if password != db_password:
                return render_template("login.html", pass_error="Wrong password!")

            # ---- login success
            session.permanent = True       # session ko permanent bana diya/Session ko automatically expiry karne ke liye
            # session["user"] = email
            session['user'] = email.lower()
            return redirect("/")

        except Exception as e:
            return render_template("login.html", e=e)

    return render_template("login.html")


# ------------------ LOGOUT -------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------ PAGES -------------------
@app.route("/admin")
def admin():
    if not session.get("user"):
        return redirect("/login")

    email = session["user"]
    username = email.split("@")[0].capitalize()    
    return render_template("admin.html",username=username, email=email, active_page="admin")



@app.route("/Image", methods=["POST", "GET"])
def image():


    if request.method == "POST":
        prompt = request.form.get("prompt")
        model = request.form.get("model")

        url = "https://ai-text-to-image-generator-free-api.p.rapidapi.com/generate"

        querystring = {
            "prompt": prompt,
            "model": model,
            "r_type": "3"
        }

        headers = {
            "x-rapidapi-key": "0aadff2423msh37644e8f0562dcfp12eaf5jsn768ee9f39bf3",
            "x-rapidapi-host": "ai-text-to-image-generator-free-api.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=20)

            # Agar API ne JSON return kiya ho (error case me aata hai)
            try:
                json_data = response.json()

                # Check for quota exceeded
                if "message" in json_data:
                    if "exceeded" in json_data["message"].lower():
                        return render_template("image.html",
                                               error=" Daily API quota exceeded. Please try again tomorrow.")
                    else:
                        return render_template("image.html",
                                               error=f" API Error: {json_data['message']}")
            except:
                pass  # ignore json error, because image might be binary

            # --- Success Case (image binary) ---
            if response.status_code == 200:
                img_base64 = base64.b64encode(response.content).decode("utf-8")
                return render_template("image.html", image_data=img_base64)

            # Other status codes
            return render_template("image.html",
                                   error=f" Error: API returned status code {response.status_code}")

        except requests.exceptions.Timeout:
            return render_template("image.html",
                                   error=" API Timeout — Server took too long to respond.")

        except Exception as e:
            return render_template("image.html",
                                   error=f" Unexpected Error: {str(e)}")


    # GET Request
    return render_template("image.html", active_page="image")





@app.route("/Text", methods = ["POST","GET"])
def Text():
 
    summary = ""

    if request.method == "POST":

        user_text = request.form.get("input_text")
        print(user_text)

        url = "https://paraphrase-and-summarize-api.p.rapidapi.com/v1/summarize"

        payload = {
            "text": user_text
        }

        headers = {
            "x-rapidapi-key": "0aadff2423msh37644e8f0562dcfp12eaf5jsn768ee9f39bf3",
            "x-rapidapi-host": "paraphrase-and-summarize-api.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            if "message" in data and "quota" in data["message"].lower():
                summary = "Your daily API limit is over. Please try again tomorrow."
            else:
                summary = data.get("paraphrased_smmary", "No summary returned")

        except Exception as e:
            summary = "API Error: " + str(e)

    return render_template("textsumm.html", summary=summary)







@app.route("/Language", methods=["GET", "POST"])
def language():
    translation = ""

    if request.method == "POST":
        text = request.form.get("inputText")
        target_lang = request.form.get("targetLang")

        # Auto detect (English or Auto)
        if re.search(r"[A-Za-z]", text):
            source_lang = "en"
        else:
            source_lang = "auto"

        url = "https://google-translate113.p.rapidapi.com/api/v1/translator/text"

        payload = {
            "from": source_lang,
            "to": target_lang,
            "text": text
        }

        headers = {
            "x-rapidapi-key": "0aadff2423msh37644e8f0562dcfp12eaf5jsn768ee9f39bf3",
            "x-rapidapi-host": "google-translate113.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            translation = data.get("trans", "No translation returned")

        except Exception as e:
            translation = "API Error: " + str(e)


    return render_template("language.html",translation=translation, active_page="language")





VOICE_MAP = {
    "en_male": {
        "languageCode": "en-US",
        "name": "en-US-Wavenet-D",
        "ssmlGender": "MALE"
    },
    "en_female": {
        "languageCode": "en-US",
        "name": "en-US-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "hi_male": {
        "languageCode": "hi-IN",
        "name": "hi-IN-Wavenet-C",
        "ssmlGender": "MALE"
    },
    "hi_female": {
        "languageCode": "hi-IN",
        "name": "hi-IN-Wavenet-D",
        "ssmlGender": "FEMALE"
    },

    "es_male": {
        "languageCode": "es-ES",
        "name": "es-ES-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "es_female": {
        "languageCode": "es-ES",
        "name": "es-ES-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "fr_male": {
        "languageCode": "fr-FR",
        "name": "fr-FR-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "fr_female": {
        "languageCode": "fr-FR",
        "name": "fr-FR-Wavenet-C",
        "ssmlGender": "FEMALE"
    },

    "ar_male": {
        "languageCode": "ar-XA",
        "name": "ar-XA-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "ar_female": {
        "languageCode": "ar-XA",
        "name": "ar-XA-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "zh_CN_male": {
        "languageCode": "cmn-CN",
        "name": "cmn-CN-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "zh_CN_female": {
        "languageCode": "cmn-CN",
        "name": "cmn-CN-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "zh_TW_male": {
        "languageCode": "cmn-TW",
        "name": "cmn-TW-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "zh_TW_female": {
        "languageCode": "cmn-TW",
        "name": "cmn-TW-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "de_male": {
        "languageCode": "de-DE",
        "name": "de-DE-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "de_female": {
        "languageCode": "de-DE",
        "name": "de-DE-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "ru_male": {
        "languageCode": "ru-RU",
        "name": "ru-RU-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "ru_female": {
        "languageCode": "ru-RU",
        "name": "ru-RU-Wavenet-C",
        "ssmlGender": "FEMALE"
    },

    "ja_male": {
        "languageCode": "ja-JP",
        "name": "ja-JP-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "ja_female": {
        "languageCode": "ja-JP",
        "name": "ja-JP-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "ko_male": {
        "languageCode": "ko-KR",
        "name": "ko-KR-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "ko_female": {
        "languageCode": "ko-KR",
        "name": "ko-KR-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "it_male": {
        "languageCode": "it-IT",
        "name": "it-IT-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "it_female": {
        "languageCode": "it-IT",
        "name": "it-IT-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "bn_male": {
        "languageCode": "bn-IN",
        "name": "bn-IN-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "bn_female": {
        "languageCode": "bn-IN",
        "name": "bn-IN-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "ur_male": {
        "languageCode": "ur-IN",
        "name": "ur-IN-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "ur_female": {
        "languageCode": "ur-IN",
        "name": "ur-IN-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "ta_male": {
        "languageCode": "ta-IN",
        "name": "ta-IN-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "ta_female": {
        "languageCode": "ta-IN",
        "name": "ta-IN-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "te_male": {
        "languageCode": "te-IN",
        "name": "te-IN-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "te_female": {
        "languageCode": "te-IN",
        "name": "te-IN-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

    "gu_male": {
        "languageCode": "gu-IN",
        "name": "gu-IN-Wavenet-B",
        "ssmlGender": "MALE"
    },
    "gu_female": {
        "languageCode": "gu-IN",
        "name": "gu-IN-Wavenet-A",
        "ssmlGender": "FEMALE"
    },

}

# ---------------------------------------
#   SHOW PAGE
# ---------------------------------------
@app.route("/Voice", methods=["GET", "POST"])
def voice():
    if request.method == "POST":
        try:
            text = request.form.get("textInput")
            voice_name = request.form.get("voiceSelect")
            action = request.form.get("action")  # generate / download

            if not text.strip():
                return render_template("speech.html", error="Please enter text first.")

            # Pick voice config — fallback alloy
            voice_config = VOICE_MAP.get(voice_name, VOICE_MAP["en_male"])

            url = "https://joj-text-to-speech.p.rapidapi.com/"

            payload = {
                "input": {"text": text},
                "voice": voice_config,
                "audioConfig": {"audioEncoding": "MP3"}
            }

            headers = {
                "x-rapidapi-key": "0aadff2423msh37644e8f0562dcfp12eaf5jsn768ee9f39bf3",
                "x-rapidapi-host": "joj-text-to-speech.p.rapidapi.com",
                "Content-Type": "application/json"
            }

            # -------------------------
            #   API REQUEST
            # -------------------------
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            except requests.exceptions.Timeout:
                return render_template("speech.html", error="API Timeout - Server not responding.")
            except requests.exceptions.ConnectionError:
                return render_template("speech.html", error="Internet / API Connection Error.")

            # -------------------------
            #   HANDLE STATUS ERRORS
            # -------------------------
            if response.status_code == 429:
                return render_template("speech.html",
                                    error="API Limit Exceeded — Try again later.")

            if response.status_code != 200:
                return render_template("speech.html",
                                    error=f"API Error: {response.status_code}")

            # -------------------------
            #   PARSE JSON
            # -------------------------
            data = response.json()

            if "error" in data:
                return render_template("speech.html", error=data["error"])

            audio_b64 = data.get("audioContent")

            if not audio_b64:
                return render_template("speech.html",
                                    error="API returned no audio.")

            # Convert b64 → bytes
            audio_bytes = base64.b64decode(audio_b64)

            # Save MP3
            filename = f"static/audio_{uuid.uuid4()}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_bytes)

            # -------------------------
            # DOWNLOAD BUTTON CLICKED
            # -------------------------
            if action == "download":
                return send_file(filename, as_attachment=True)

            # -------------------------
            # PLAY ON PAGE
            # -------------------------
            return render_template("speech.html", audio_file="/" + filename)

        except Exception as e:
            return render_template("speech.html",
                                error=f"Unexpected Error: {str(e)}")

    return render_template("speech.html", active_page="voice")





@app.route("/Anime", methods=["GET", "POST"])
def anime():
    if request.method == "POST":
        try:
            file = request.files.get("image")
            style = request.form.get("style")

            if not file:
                return render_template("anime.html", error="Please upload an image.")

            url = "https://phototoanime1.p.rapidapi.com/photo-to-anime"

            files = {
                "image": (file.filename, file.stream, file.mimetype)
            }

            payload = {
                "style": style
            }

            headers = {
                "x-rapidapi-key": "0aadff2423msh37644e8f0562dcfp12eaf5jsn768ee9f39bf3",
                "x-rapidapi-host": "phototoanime1.p.rapidapi.com"
            }

            response = requests.post(url, data=payload, files=files, headers=headers)

            # --- JSON parse error handling ---
            try:
                result = response.json()
            except:
                return render_template("anime.html", error="Invalid response from API.")

            print(result)

            # --- QUOTA EXCEEDED CHECK ---
            if "message" in result and "quota" in result["message"].lower():
                return render_template(
                    "anime.html",
                    error="API quota exceeded! Please try after some time or use another API Key."
                )

            # --- Check for API specific error message ---
            if result.get("statusCode") != 200:
                msg = result.get("message", "Something went wrong. Try with another image.")
                return render_template("anime.html", error=f"API Error: {msg}")

            # --- Successful response ---
            if "body" in result and "imageUrl" in result["body"]:
                output_url = result["body"]["imageUrl"]
                return render_template("anime.html", output_url=output_url)

            return render_template("anime.html", error="API error! No image returned.")

        except Exception as e:
            # --- General Exception Handler ---
            return render_template("anime.html", error=f"Error: {str(e)}")

    return render_template("anime.html")





@app.route("/Background", methods=["GET", "POST"])
def remove():
    if request.method == "POST":

        # ---- Check file upload ----
        file = request.files.get("image")
        if not file:
            return render_template(
                "backgrounremover.html",
                error="Please upload an image."
            )

        url = "https://remove-background18.p.rapidapi.com/public/remove-background-file"

        files = {
            "file": (file.filename, file.stream, file.mimetype)
        }

        headers = {
            "x-rapidapi-key": "0aadff2423msh37644e8f0562dcfp12eaf5jsn768ee9f39bf3",
            "x-rapidapi-host": "remove-background18.p.rapidapi.com"
        }

        try:
            # API request
            response = requests.post(url, files=files, headers=headers, timeout=20)

            # If API returns an error code
            if response.status_code != 200:
                if response.status_code == 429:
                    return render_template(
                        "backgrounremover.html",
                        error="API Limit Exceeded — Try again later."
                    )
                return render_template(
                    "backgrounremover.html",
                    error=f"API Error: {response.status_code}"
                )

            # Try extracting JSON
            result = response.json()
            final_url = result.get("url")

            if not final_url:
                return render_template(
                    "backgrounremover.html",
                    error="Error: Failed to process image. Please try again."
                )

            return render_template(
                "backgrounremover.html",
                output_url=final_url
            )

        except requests.exceptions.Timeout:
            return render_template(
                "backgrounremover.html",
                error="Request timed out — Internet slow ya API busy hai."
            )

        except requests.exceptions.RequestException:
            return render_template(
                "backgrounremover.html",
                error="Network error — Please try again."
            )

        except Exception as e:
            return render_template(
                "backgrounremover.html",
                error=f"Unexpected Error: {str(e)}"
            )

    # GET request
    return render_template("backgrounremover.html", active_page="background")


@app.route("/download_image")
def download_image():
    img_url = request.args.get("img")

    res = requests.get(img_url)
    img_bytes = BytesIO(res.content)

    return send_file(
        img_bytes,
        mimetype="image/png",
        as_attachment=True,
        download_name="bg_removed.png"
    )





app.run(port=5050, debug=True)









