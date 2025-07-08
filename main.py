from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "سلام، سرور در حال کار است!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)