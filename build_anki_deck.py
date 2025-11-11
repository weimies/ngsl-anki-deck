#!/usr/bin/env python3
"""
Build an Anki .apkg containing the top-N high-frequency words (NGSL or fallback) plus a cheatsheet card.
- By default the script looks for a local file 'ngsl_2000.txt' (one word per line). If not found,
  it falls back to the google-10000-english list and takes the top 2000 words.
- For each word the script generates a simple example sentence (template-based) and places
  a placeholder for part-of-speech / definition so you can edit later in Anki.
- Output: ngsl_2000_with_cheatsheet.apkg

Requirements: Python 3.8+, pip install genanki requests

Usage:
  python3 build_anki_deck.py

"""

import os
import sys
import requests
import genanki
import random
import html

TOP_N = 2000
OUTPUT_FILE = "ngsl_2000_with_cheatsheet.apkg"
NGSL_LOCAL = "ngsl_2000.txt"
FALLBACK_WORDLIST_RAW = (
    "https://raw.githubusercontent.com/first20hours/google-10000-english/"
    "d0736d492489198e4f9d650c7ab4143bc14c1e9e/google-10000-english.txt"
)

CHEATSHEET_FILE = "cheatsheet.md"

CHEATSHEET_MD = None
if os.path.exists(CHEATSHEET_FILE):
    with open(CHEATSHEET_FILE, "r", encoding="utf-8") as f:
        CHEATSHEET_MD = f.read()
else:
    CHEATSHEET_MD = """
功能词・常见连词・基础句型 速查表（阅读专用）\n\n(在 Anki 中可作为单张参考卡)\n"""

# Fetch or read top words

def read_local_ngsl(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
            return words[:TOP_N]
    except Exception:
        return []


def fetch_fallback_wordlist(url, top_n):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    words = []
    for line in r.text.splitlines():
        if "|" in line:
            parts = line.split("|", 1)
            word = parts[1].strip()
        else:
            word = line.strip()
        if word:
            words.append(word)
        if len(words) >= top_n:
            break
    return words


def generate_example_sentence(word):
    # A small set of template sentences to avoid monotony
    templates = [
        "I saw the word '{w}' in an article yesterday.",
        "Many people use '{w}' when they talk about technology.",
        "The {w} is important for understanding this topic.",
        "He asked me about {w} during the meeting.",
        "This sentence contains the word '{w}'.",
    ]
    tpl = random.choice(templates)
    return tpl.format(w=word)


def build_deck(words, cheatsheet_md, output_file):
    model_id = random.randrange(1 << 30, 1 << 31)
    deck_id = random.randrange(1 << 30, 1 << 31)

    model = genanki.Model(
        model_id,
        "Simple FrontBack Model",
        fields=[{"name": "Front"}, {"name": "Back"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "<div style=\"font-size:24px\">{{Front}}</div>",
                "afmt": "{{Front}}<hr id=\"answer\">{{Back}}",
            }
        ],
    )

    deck = genanki.Deck(deck_id, "NGSL Top {} + Cheatsheet".format(len(words)))

    # Add cheatsheet as a single reference card
    cheatsheet_html = "<pre style='white-space:pre-wrap; font-family:monospace'>{}</pre>".format(html.escape(cheatsheet_md))
    deck.add_note(genanki.Note(model=model, fields=["速查表（阅读速查）", cheatsheet_html]))

    for w in words:
        front = w
        example = generate_example_sentence(w)
        back = f"词性：\n释义：\n例句：{example}\n搭配："
        deck.add_note(genanki.Note(model=model, fields=[front, back]))

    pkg = genanki.Package(deck)
    pkg.write_to_file(output_file)
    print(f"Wrote: {output_file} (cards: {len(words)+1})")


def main():
    words = read_local_ngsl(NGSL_LOCAL)
    source = 'local file' if words else 'fallback list'
    if not words:
        try:
            print("Fetching fallback wordlist...")
            words = fetch_fallback_wordlist(FALLBACK_WORDLIST_RAW, TOP_N)
        except Exception as e:
            print("Failed to fetch fallback wordlist:", e)
            sys.exit(1)
    print(f"Using {len(words)} words from {source}.")
    build_deck(words, CHEATSHEET_MD, OUTPUT_FILE)


if __name__ == '__main__':
    main()