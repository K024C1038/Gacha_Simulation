from flask import Flask, render_template, request, redirect, url_for, jsonify
import random
import json
import os

app = Flask(__name__)

# ガチャの設定
GACHA_PROBABILITIES = {
    "single": {
        "N": 33,
        "N+": 25,
        "R": 20,
        "R+": 15,
        "SR": 5,
        "SR+": 2
    },
    "eleven": {
        "R": 57,
        "R+": 30,
        "SR": 10,
        "SR+": 3
    },
}

SR_PLUS_CHARACTERS = [f"Character {i}" for i in range(1, 11)]

# ファイルパス
DATA_FILE = "data/results.json"

# 初期化
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump(
            {
                "draws": 0,
                "cost": 0,
                "results": {},
                "sr_plus_collected": []
            }, f)


def save_results(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_results():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def draw_gacha(probabilities):
    """ガチャの結果をランダムに決定する"""
    rand = random.uniform(0, 100)
    cumulative = 0
    for rarity, chance in probabilities.items():
        cumulative += chance
        if rand <= cumulative:
            return rarity
    return "N"


def get_image_path(rarity):
    """指定されたレアリティに応じた画像パスを取得"""
    image_dir = os.path.join("static", "images", rarity)
    if not os.path.exists(image_dir):
        return None
    images = os.listdir(image_dir)
    if not images:
        return None
    return os.path.join("images", rarity, random.choice(images))


@app.route("/")
def index():
    data = load_results()
    return render_template("index.html",
                           data=data,
                           sr_plus_characters=SR_PLUS_CHARACTERS)


@app.route("/draw", methods=["POST"])
def draw():
    gacha_type = request.form.get("gacha_type")
    data = load_results()

    results = []
    if gacha_type == "single":
        rarity = draw_gacha(GACHA_PROBABILITIES["single"])
        image_path = get_image_path(rarity)
        results.append({"rarity": rarity, "image": image_path})
        data["cost"] += 100
        data["draws"] += 1
    elif gacha_type == "eleven":
        for i in range(10):
            rarity = draw_gacha(GACHA_PROBABILITIES["eleven"])
            image_path = get_image_path(rarity)
            results.append({"rarity": rarity, "image": image_path})
        # 11回目は必ずSR
        results.append({"rarity": "SR", "image": get_image_path("SR")})
        data["cost"] += 1000
        data["draws"] += 11

    # 結果を集計
    for result in results:
        rarity = result["rarity"]
        if rarity not in data["results"]:
            data["results"][rarity] = 0
        data["results"][rarity] += 1

    for result in results:
        if result["rarity"] == "SR+":
            # Select a random SR+ character
            character = random.choice(SR_PLUS_CHARACTERS)

            # Get a truly random image for this draw
            image_path = get_image_path(
                "SR+")  # Fetch a random image from the SR+ folder

            # Check if the character is already collected
            existing_character = next(
                (c
                 for c in data["sr_plus_collected"] if c["name"] == character),
                None)
            if not existing_character:
                # Add to collected SR+ if not already present
                data["sr_plus_collected"].append({
                    "name": character,
                    "image": image_path
                })

            # Add the draw result
            result.update({"character": character, "image": image_path})

            # Append the draw result with its specific character and image
            result.update({"character": character, "image": image_path})

    save_results(data)
    return render_template("result.html",
                           results=results,
                           data=data,
                           sr_plus_characters=SR_PLUS_CHARACTERS)


@app.route("/reset", methods=["POST"])
def reset():
    data = {"draws": 0, "cost": 0, "results": {}, "sr_plus_collected": []}
    save_results(data)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
