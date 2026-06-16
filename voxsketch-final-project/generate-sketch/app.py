import os
import io
import sys
import json

import torch
import numpy as np
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image
from sentence_transformers import SentenceTransformer, util


app = Flask(__name__, template_folder="templates")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Try ../static then ./static
_candidate1 = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "static"))
_candidate2 = os.path.abspath(os.path.join(SCRIPT_DIR, "static"))

if os.path.isdir(_candidate1):
    STATIC_DIR = _candidate1
elif os.path.isdir(_candidate2):
    STATIC_DIR = _candidate2
else:
    STATIC_DIR = _candidate1  

app.static_folder = STATIC_DIR

print("----- STARTUP DEBUG -----")
print("SCRIPT_DIR:", SCRIPT_DIR)
print("STATIC_DIR:", STATIC_DIR, "exists?", os.path.isdir(STATIC_DIR))
print("-------------------------")


BLANK_PATH = "BLANK"
DEFAULT_GENDER = "male"


def build_path(path_suffix: str) -> str:
    parts = [p for p in path_suffix.replace("\\", "/").split("/") if p]
    return os.path.normpath(os.path.join(STATIC_DIR, *parts))

COMPONENT_MAP = {
    "male": {
        "face": {
            "broad chin face": build_path("components/male/face/broadchinface.png"),
            "diamond face": build_path("components/male/face/diamondface.png"),
            "heavy jaw face": build_path("components/male/face/heavujawface.png"),
            "long face": build_path("components/male/face/longface.png"),
            "oblong face": build_path("components/male/face/oblongface.png"),
            "oval face": build_path("components/male/face/ovalface.png"),
            "rectangle face": build_path("components/male/face/rectangleface.png"),
            "round edge face": build_path("components/male/face/roundedgeface.png"),
            "round face": build_path("components/male/face/roundface.png"),
            "soft face": build_path("components/male/face/softface.png"),
            "square oval face": build_path("components/male/face/squareovalface.png"),
            "tall face": build_path("components/male/face/tallface.png"),
            "triangle face": build_path("components/male/face/triangleface.png"),
            "wide face": build_path("components/male/face/wideface.png"),
        },
        "eyes": {
            "almond eyes": build_path("components/male/eyes/almondeyes.png"),
            "dark eyes": build_path("components/male/eyes/darkeyes.png"),
            "dark round eyes": build_path("components/male/eyes/darkround.png"),
            "deep set eyes": build_path("components/male/eyes/deepset.png"),
            "down turned eyes": build_path("components/male/eyes/downturnedeyes.png"),
            "droop eyes": build_path("components/male/eyes/droopeyes.png"),
            "fold eyes": build_path("components/male/eyes/foldeyes.png"),
            "heavy upper eyes": build_path("components/male/eyes/heavyuppereyes.png"),
            "hooded eyes": build_path("components/male/eyes/hooded.png"),
            "intense eyes": build_path("components/male/eyes/intense.png"),
            "irregular eyes": build_path("components/male/eyes/irregulareyes.png"),
            "large eyes": build_path("components/male/eyes/largeeyes.png"),
            "low crease eyes": build_path("components/male/eyes/lowcreaseeyes.png"),
            "monolid eyes": build_path("components/male/eyes/monolid.png"),
            "narroweyes": build_path("components/male/eyes/narroweyes.png"),
            "normal eyes": build_path("components/male/eyes/normal.png"),
            "openalmond eyes": build_path("components/male/eyes/openalmond.png"),
            "open medium eyes": build_path("components/male/eyes/openmediumeyes.png"),
            "open monolid eyes": build_path("components/male/eyes/openmonolid.png"),
            "round eyes": build_path("components/male/eyes/roundeyes.png"),
            "sharp eyes": build_path("components/male/eyes/sharpeyes.png"),
            "small eyes": build_path("components/male/eyes/small.png"),
            "tired eyes": build_path("components/male/eyes/tiredeyes.png"),
            "wide set eyes": build_path("components/male/eyes/wideseteyes.png"),
        },
        "eyebrows": {
            "basic eyebrows": build_path("components/male/eyebrows/basic.png"),
            "bold eyebrows": build_path("components/male/eyebrows/bold.png"),
            "closee eyebrows": build_path("components/male/eyebrows/closee.png"),
            "curvetip eyebrows": build_path("components/male/eyebrows/curvetip.png"),
            "flat eyebrows": build_path("components/male/eyebrows/flat.png"),
            "flat wide eyebrows": build_path("components/male/eyebrows/flatwide.png"),
            "full thick eyebrows": build_path("components/male/eyebrows/fullthick.png"),
            "half curve eyebrows": build_path("components/male/eyebrows/halfcurve.png"),
            "hard angled eyebrows": build_path("components/male/eyebrows/hardangled.png"),
            "lifted eyebrows": build_path("components/male/eyebrows/lifted.png"),
            "light arched eyebrows": build_path("components/male/eyebrows/lightarched.png"),
            "low angle eyebrows": build_path("components/male/eyebrows/lowangle.png"),
            "medium eyebrows": build_path("components/male/eyebrows/medium.png"),
            "messy eyebrows": build_path("components/male/eyebrows/messy.png"),
            "slight curved eyebrows": build_path("components/male/eyebrows/slightcurved.png"),
            "slightly arched eyebrows": build_path("components/male/eyebrows/slightlyarched.png"),
            "slim eyebrows": build_path("components/male/eyebrows/slim.png"),
            "smooth eyebrows": build_path("components/male/eyebrows/smooth.png"),
            "soft eyebrows": build_path("components/male/eyebrows/soft.png"),
            "straight eyebrows": build_path("components/male/eyebrows/straight.png"),
            "thick eyebrows": build_path("components/male/eyebrows/thick.png"),
            "thin eyebrows": build_path("components/male/eyebrows/thin.png"),
            "upward eyebrows": build_path("components/male/eyebrows/upward.png"),
            "wide eyebrows": build_path("components/male/eyebrows/wide.png"),
        },
        "nose": {
            "broad nose": build_path("components/male/nose/broadnose.png"),
            "bulbous nose": build_path("components/male/nose/bulbousnose.png"),
            "bumpy nose": build_path("components/male/nose/bumpynose.png"),
            "compact nose": build_path("components/male/nose/compactnose.png"),
            "curved nose": build_path("components/male/nose/curvednose.png"),
            "droop nose": build_path("components/male/nose/droopnose.png"),
            "flare nose": build_path("components/male/nose/flarenose.png"),
            "flat tip nose": build_path("components/male/nose/flattipnose.png"),
            "fleshy nose": build_path("components/male/nose/fleshynose.png"),
            "hawk nose": build_path("components/male/nose/hawknose.png"),
            "low bridge nose": build_path("components/male/nose/lowbridgenose.png"),
            "medium nostrils nose": build_path("components/male/nose/mediumnostrils.png"),
            "medium wide nose": build_path("components/male/nose/mediumwidenose.png"),
            "narrow bridge nose": build_path("components/male/nose/narrowbridge.png"),
            "pointed nose": build_path("components/male/nose/pointednose.png"),
            "roman nose": build_path("components/male/nose/romannose.png"),
            "round nose": build_path("components/male/nose/roundnose.png"),
            "round tip nose": build_path("components/male/nose/roundtipnose.png"),
            "slim bridge nose": build_path("components/male/nose/slimbridgenose.png"),
            "slim nose": build_path("components/male/nose/slimnose.png"),
            "soft bridge nose": build_path("components/male/nose/softbridgenose.png"),
            "soft bulbous nose": build_path("components/male/nose/softbulbousnose.png"),
            "soft nose": build_path("components/male/nose/softnose.png"),
            "tilt nose": build_path("components/male/nose/tiltnose.png"),
            "turned up nose": build_path("components/male/nose/turnedupnose.png"),
            "wide nose": build_path("components/male/nose/widenose.png"),
        },
        "lips": {
            "bottom heavy lips": build_path("components/male/lips/bottomheavy.png"),
            "bottom heavy lips": build_path("components/male/lips/bottomheavylips.png"),
            "bow shaped lips": build_path("components/male/lips/bowshapedlips.png"),
            "cupid bow lips": build_path("components/male/lips/cupidbow.png"),
            "cupid bow lips": build_path("components/male/lips/cupidbowlips.png"),
            "equal lips": build_path("components/male/lips/equal.png"),
            "flat upper lips": build_path("components/male/lips/flatupperlips.png"),
            "full lips": build_path("components/male/lips/fullips.png"),
            "heart shaped lips": build_path("components/male/lips/heartshapedlips.png"),
            "heavy lips": build_path("components/male/lips/heavylips.png"),
            "lips": build_path("components/male/lips/lips.png"),
            "low curve lips": build_path("components/male/lips/lowcurvelips.png"),
            "medium lips": build_path("components/male/lips/mediumlips.png"),
            "normal lips": build_path("components/male/lips/normallips.png"),
            "round lips": build_path("components/male/lips/roundlips.png"),
            "short lips": build_path("components/male/lips/shortlips.png"),
            "soft thin lips": build_path("components/male/lips/softthinlips.png"),
            "straight thin lips": build_path("components/male/lips/straightthinlips.png"),
            "thin lips": build_path("components/male/lips/thinlips.png"),
            "top heavy lips": build_path("components/male/lips/topheavylips.png"),
            "upper flat lips": build_path("components/male/lips/upperflatlips.png"),
            "wide curve lips": build_path("components/male/lips/widecurvelips.png"),
        },
    "hair": {
        "long wavy hair": build_path("components/male/hairs/Longwavyhair.png"),
        "flat hair": build_path("components/male/hairs/flathair.png"),
        "front long hair": build_path("components/male/hairs/frontlong.png"),
        "high puff hair": build_path("components/male/hairs/highpuffhair.png"),
        "light wavy hair": build_path("components/male/hairs/lightwavyhair.png"),
        "medium wavy hair": build_path("components/male/hairs/mediumwavyhair.png"),
        "messy hair": build_path("components/male/hairs/messyhair.png"),
        "mid curly hair": build_path("components/male/hairs/midcurly.png"),
        "plain straight hair": build_path("components/male/hairs/plainstraight.png"),
        "puffy hair": build_path("components/male/hairs/puffyhair.png"),
        "right parted hair": build_path("components/male/hairs/rightpartedhair.png"),
        "short curly hair": build_path("components/male/hairs/shortcurlyhair.png"),
        "short hair": build_path("components/male/hairs/shorthair.png"),
        "side parted hair": build_path("components/male/hairs/sideparted.png"),
        "spiky hair": build_path("components/male/hairs/spikyhair.png"),
        "thick voluminous hair": build_path("components/male/hairs/thickvoluminoushair.png"),
        "no hair": BLANK_PATH,
        "none": BLANK_PATH,
        "bald": BLANK_PATH,
        "no": BLANK_PATH,
},

        "mustache": {
            "chevron mustache": build_path("components/male/mustache/chevronmustache.png"),
            "down mustache": build_path("components/male/mustache/downmustache.png"),
            "full heavy mustache": build_path("components/male/mustache/fullheavymustache.png"),
            "full medium mustache": build_path("components/male/mustache/fullmedium.png"),
            "horseshoe mustache": build_path("components/male/mustache/horseshoe.png"),
            "irregular mustache": build_path("components/male/mustache/irregularmustache.png"),
            "medium mustache": build_path("components/male/mustache/mediummustache.png"),
            "natural mustache": build_path("components/male/mustache/naturalmustache.png"),
            "parted mustache": build_path("components/male/mustache/partedmustache.png"),
            "pencil mustache": build_path("components/male/mustache/pencilmustache.png"),
            "rough mustache": build_path("components/male/mustache/rough.png"),
            "rough mustache": build_path("components/male/mustache/roughmustache.png"),
            "short mustache": build_path("components/male/mustache/short.png"),
            "small mustache": build_path("components/male/mustache/smustache.png"),
            "soft curve mustache": build_path("components/male/mustache/softcurve.png"),
            "thinmustache": build_path("components/male/mustache/thinmustache.png"),
            
            "no mustache": BLANK_PATH,
            "none": BLANK_PATH,
            "no": BLANK_PATH,
        },
        "beard": {
            "anchor beard": build_path("components/male/beard/anchorbeard.png"),
            "circle strap beard": build_path("components/male/beard/circlestrap.png"),
            "full beard": build_path("components/male/beard/fullbeard.png"),
            "full goatee beard": build_path("components/male/beard/fullgoatee.png"),
            "light beard": build_path("components/male/beard/lightbeard.png"),
            "long goatee beard": build_path("components/male/beard/longgoatee.png"),
            "lowjaw beard": build_path("components/male/beard/lowjaw.png"),
            "medium beard": build_path("components/male/beard/mediumbeard.png"),
            "pointed chin patch beard": build_path("components/male/beard/pointedchinpatch.png"),
            "roundchin beard": build_path("components/male/beard/roundchin.png"),
            "short connected goatee beard": build_path("components/male/beard/shortconnectedgoatee.png"),
            "small chinpatch beard": build_path("components/male/beard/smallchinpatch.png"),
            "soft chin beard": build_path("components/male/beard/softchin.png"),
            "thick chin beard": build_path("components/male/beard/thickchin.png"),
            "thin beard": build_path("components/male/beard/thin.png"),
            "no beard": BLANK_PATH,
            "none": BLANK_PATH,
            "no": BLANK_PATH,
        },
        "ears": {
            
            "narrow ears": build_path("components/male/ears/narrowear.png"),
            "oval ears": build_path("components/male/ears/ovalear.png"),
            "round ears": build_path("components/male/ears/roundear.png"),
            
            "small ears": build_path("components/male/ears/smallear.png"),
            "no ears": BLANK_PATH,
            "none": BLANK_PATH,
            "no": BLANK_PATH,
            "narrow years":build_path("components/male/ears/narrowear.png"),
            "oval years":build_path("components/male/ears/ovalear.png"),
            "round years": build_path("components/male/ears/roundear.png"),
            "small years": build_path("components/male/ears/smallear.png"),
        },
    },

    "female": {
        "face": {
            "rounded jawline face": build_path("components/female/face/Roundedjawlineface.png"),
            "heart face": build_path("components/female/face/heartface.png"),
            "long face": build_path("components/female/face/longface.png"),
            "oval face": build_path("components/female/face/ovalface.png"),
            "rectangle face": build_path("components/female/face/rectangleface.png"),
            "round face": build_path("components/female/face/roundface.png"),
            "soft oval face": build_path("components/female/face/softovalface.png"),
            "vtraingle face": build_path("components/female/face/vtraingleface.png"),
        },
        "eyes": {
            "almond eyes": build_path("components/female/eyes/almondeyes.png"),
            "calmset eyes": build_path("components/female/eyes/calmseteyes.png"),
            "circular eyes": build_path("components/female/eyes/circulareyes.png"),
            "deepset eyes": build_path("components/female/eyes/deepseteyes.png"),
            "down turned eyes": build_path("components/female/eyes/downturnedeyes.png"),
            "hooded eyes": build_path("components/female/eyes/hoodedeyes.png"),
            "monolid eyes": build_path("components/female/eyes/monolideyes.png"),
            "open lift eyes": build_path("components/female/eyes/openlifteyes.png"),
            "protruding eyes": build_path("components/female/eyes/protrudingeyes.png"),
            "round eyes": build_path("components/female/eyes/roundeyes.png"),
            "soft droop eyes": build_path("components/female/eyes/softdroopeyes.png"),
            "up turned eyes": build_path("components/female/eyes/upturnedeyes.png"),
            "wide set eyes": build_path("components/female/eyes/wideseteyes.png"),
        },
        "eyebrows": {
            "basic eyebrows": build_path("components/female/eyebrows/basiceyebrows.png"),
            "curved eyebrows": build_path("components/female/eyebrows/curvedeyebrows.png"),
            "medium thick eyebrows": build_path("components/female/eyebrows/mediumthickeyebrows.png"),
            "round eyebrows": build_path("components/female/eyebrows/roundeyebrows.png"),
            "slightly curved eyebrows": build_path("components/female/eyebrows/slightlycurvedeyebrows.png"),
            "soft angled eyebrows": build_path("components/female/eyebrows/softangledeyebrows.png"),
            "soft flat eyebrows": build_path("components/female/eyebrows/softflateyebrows.png"),
            "thick eyebrows": build_path("components/female/eyebrows/thickeyebrows.png"),
            "upwared eyebrows": build_path("components/female/eyebrows/upwaredeyebrows.png"),
        },
        "nose": {
            "greek nose": build_path("components/female/nose/greeknose.png"),
            "medium narrow nose": build_path("components/female/nose/mediumnarrow.png"),
            "medium width nose": build_path("components/female/nose/mediumwidthnose.png"),
            "mild wide nose": build_path("components/female/nose/mildwidenose.png"),
            "narrowpointed nose": build_path("components/female/nose/narrowpointed.png"),
            "nubian nose": build_path("components/female/nose/nubiannose.png"),
            "sharp nose": build_path("components/female/nose/sharp.png"),
            "slim bridge nose": build_path("components/female/nose/slimbridgenose.png"),
            "small nose": build_path("components/female/nose/smallnose.png"),
            "snub nose": build_path("components/female/nose/snubnose.png"),
            "soft nose": build_path("components/female/nose/softnose.png"),
            "straight nose": build_path("components/female/nose/straightnose.png"),
            "wide nose": build_path("components/female/nose/widenose.png"),
        },
        "lips": {
            "bottom heavy lips": build_path("components/female/lips/bottomheavylips.png"),
            "distinct cupid bow lips": build_path("components/female/lips/distinctcupidbow.png"),
            "full cupid bow lips": build_path("components/female/lips/fullcupidbow.png"),
            "full lips": build_path("components/female/lips/fullips.png"),
            "heavy lips": build_path("components/female/lips/heavy.png"),
            
            "normal lips": build_path("components/female/lips/normallips.png"),
            "soft even lips": build_path("components/female/lips/softevenlips.png"),
            "soft lips": build_path("components/female/lips/softlips.png"),
            "top heavy lips": build_path("components/female/lips/topheavylips.png"),
            "upper flat lips": build_path("components/female/lips/upperflatlips.png"),
        },
        "hair": {
           "bob hair": build_path("components/female/hairs/bobhair.png"),
            "curly bob hair": build_path("components/female/hairs/curlybobhair.png"),
            "curly long hair": build_path("components/female/hairs/curlylong.png"),
            "large barrel waves hair": build_path("components/female/hairs/largebarelwaves.png"),  # corrected
            "medium curly hair": build_path("components/female/hairs/mediumcurly.png"),
            "messy hair": build_path("components/female/hairs/messyhair.png"),
            "short hair": build_path("components/female/hairs/shorthair.png"),
            "short wavy hair": build_path("components/female/hairs/shorywavyhair.png"),  # corrected
            "straight long hair": build_path("components/female/hairs/straightlong.png"),
            "thin straight hair": build_path("components/female/hairs/thinstraight.png"),
    
},
        "mustache": {
            "no mustache": BLANK_PATH,
            "none": BLANK_PATH,
            "no": BLANK_PATH,
        },
        "beard": {
            "no beard": BLANK_PATH,
            "none": BLANK_PATH,
            "no": BLANK_PATH,
        },
        "ears": {
            "narrow ears": build_path("components/female/ears/narrowear.png"),
            "round ears": build_path("components/female/ears/roundear.png"),
            "small ears": build_path("components/female/ears/smallear.png"),
            "narrow years":build_path("components/female/ears/narrowear.png"),
            "round years": build_path("components/female/ears/roundear.png"),
            "small years": build_path("components/female/ears/smallear.png"),
            
            "no ears": BLANK_PATH,
            "none": BLANK_PATH,
            "no": BLANK_PATH,
        },
    },

}

# -------------------------------------------------
# SentenceTransformer model & embeddings
# -------------------------------------------------
print("Loading SentenceTransformer model 'all-MiniLM-L6-v2' ...")
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    print("Failed to load SentenceTransformer:", e, file=sys.stderr)
    raise

encoded_keywords = []
keyword_to_file_map = {}

# Flatten gender + category + keyword
for gender, gender_map in COMPONENT_MAP.items():
    for category, kw_dict in gender_map.items():
        for keyword, file_path in kw_dict.items():
            vec = model.encode(keyword)
            encoded_keywords.append(vec)
            idx = len(encoded_keywords) - 1
            keyword_to_file_map[idx] = {
                "gender": gender,
                "category": category,
                "keyword": keyword,
                "file_path": file_path,
            }

keyword_embeddings = torch.tensor(np.array(encoded_keywords))
print("Keyword database ready with", len(encoded_keywords), "entries.")


def normalize_gender(raw: str) -> str:
    g = (raw or "").strip().lower()
    if g not in COMPONENT_MAP:
        g = DEFAULT_GENDER
    return g


def find_best_match_for_phrase(phrase: str, gender: str, top_k: int = 10):
    """
    Returns the best hit dict that matches the given gender, or None.
    hit dict will contain: score, corpus_id, and 'mapped' entry.
    """
    if not phrase:
        return None
    gender = normalize_gender(gender)
    q = model.encode(phrase, convert_to_tensor=True)
    hits = util.semantic_search(q, keyword_embeddings, top_k=top_k)[0]
    for h in hits:
        idx = h["corpus_id"]
        mapped = keyword_to_file_map.get(idx)
        if not mapped:
            continue
        if mapped["gender"] != gender:
            continue
        h["mapped"] = mapped
        return h
    return None


# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_category_options", methods=["POST"])
def get_category_options():
    data = request.get_json(silent=True) or {}
    category_name = (data.get("category") or "").strip()
    gender = normalize_gender(data.get("gender") or DEFAULT_GENDER)

    print(f"[get_category_options] gender={gender!r}, category={category_name!r}")

    gender_map = COMPONENT_MAP.get(gender, {})
    category_map = gender_map.get(category_name)
    if not category_map:
        print("  -> no category map found")
        return jsonify({"options": []})

    options = []
    seen_paths = set()

    for keyword, file_path in category_map.items():
        if file_path == BLANK_PATH:
            continue
        if file_path in seen_paths:
            continue
        seen_paths.add(file_path)

        exists = os.path.exists(file_path)
        print(f"  checking {file_path} exists? {exists}")
        if not exists:
            continue

        rel_path = os.path.relpath(file_path, STATIC_DIR)
        web_path = rel_path.replace("\\", "/")
        full_url = f"/static/{web_path}"
        options.append(
            {
                "label": keyword.title(),
                "url": full_url,
                "value": keyword,
            }
        )

    print(f"  -> returning {len(options)} options")
    return jsonify({"options": options})


@app.route("/build_sketch", methods=["POST"])
def build_sketch():
    payload = request.get_json(force=True, silent=True) or {}
    user_text = (payload.get("description") or "").strip()
    single_preview = bool(payload.get("single_preview", False))
    gender = normalize_gender(payload.get("gender") or DEFAULT_GENDER)

    if not user_text and not single_preview:
        return jsonify({"error": "No description provided"}), 400

    # -------- SINGLE COMPONENT PREVIEW (optional) --------
    if single_preview:
        hit = find_best_match_for_phrase(user_text, gender, top_k=10)
        if not hit:
            return jsonify({"error": "No match"}), 400

        mapped = hit["mapped"]
        #cosine similarity between input description embedding and stored component embedding.
        score = float(hit["score"])
        if score < 0.40:
            return jsonify({"error": "Low confidence"}), 400

        comp_path = mapped["file_path"]
        if comp_path == BLANK_PATH:
            img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            img_io = io.BytesIO()
            img.save(img_io, "PNG")
            img_io.seek(0)
            return send_file(img_io, mimetype="image/png")

        if not os.path.exists(comp_path):
            return jsonify({"error": "Component file not found"}), 500

        img = Image.open(comp_path).convert("RGBA")
        img_io = io.BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)
        return send_file(img_io, mimetype="image/png")

    # -------- COMPOSITE SKETCH --------
    user_phrases = [p.strip() for p in user_text.split(",") if p.strip()]
    best_hit_per_category = {}

    for phrase in user_phrases:
        hit = find_best_match_for_phrase(phrase, gender, top_k=10)
        if not hit:
            continue
        mapped = hit["mapped"]
        score = float(hit["score"])
        category = mapped["category"]
        file_path = mapped["file_path"]

        threshold = 0.45 if category in ("eyes", "eyebrows") else 0.55
        if score < threshold:
            continue

        prev = best_hit_per_category.get(category)
        if prev is None or score > prev["score"]:
            best_hit_per_category[category] = {
                "file_path": file_path,
                "score": score,
                "keyword": mapped["keyword"],
            }

    final_sketch = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
    LAYER_ORDER = ["face", "ears", "hair", "nose", "lips", "mustache", "beard", "eyes", "eyebrows"]

    for layer in LAYER_ORDER:
        hit = best_hit_per_category.get(layer)
        if not hit:
            continue
        comp_path = hit["file_path"]
        if comp_path == BLANK_PATH:
            continue
        if not os.path.exists(comp_path):
            print(f"[WARN] missing file for {layer}: {comp_path}")
            continue
        try:
            comp = Image.open(comp_path).convert("RGBA")
            final_sketch.paste(comp, (0, 0), comp)
        except Exception as e:
            print(f"[WARN] failed to paste {comp_path}: {e}")

    img_io = io.BytesIO()
    final_sketch.save(img_io, "PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")


if __name__ == "__main__":
    print("Starting Flask app at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)