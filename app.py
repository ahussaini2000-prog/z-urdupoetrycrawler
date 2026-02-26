import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
from googletrans import Translator
import random
import re
import os
import time

# --- Configuration & CSS ---
# We inject CSS to load a high-quality Nastaliq font from Google Fonts
def local_css():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&display=swap" rel="stylesheet">
    <style>
    .nastaliq-title {
        font-family: 'Noto Nastaliq Urdu', serif;
        font-size: 48px;
        text-align: center;
        direction: rtl;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    .poem-container {
        font-family: 'Noto Nastaliq Urdu', serif;
        font-size: 32px;
        text-align: center;
        direction: rtl;
        line-height: 2.2;
        background-color: #fffbf0;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #d4af37;
        color: #1a1a1a;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .poet-name {
        text-align: center;
        font-style: italic;
        color: #555;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Core Functions ---

def scrape_poetry(url, poet_name):
    """
    Scrapes the URL to find text. 
    Note: Generic scrapers often fail on dynamic sites (JS). 
    This works best on static HTML sites (like Wikipedia, specific poetry archives).
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Force UTF-8 encoding to handle Urdu characters correctly
        if not response.encoding or response.encoding.lower() != 'utf-8':
            response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Attempt to find specific poetry containers or paragraphs
        # We look for common tags. This is a heuristic approach.
        text_blocks = []
        
        # Strategy 1: Look for paragraph tags or divs
        for tag in soup.find_all(['p', 'div', 'span', 'blockquote']):
            text = tag.get_text(separator=" ").strip()
            # Heuristic: Urdu text generally contains characters in the Arabic Unicode block
            # We filter out very short lines (navigation menus) and empty strings
            if len(text) > 20:
                # Check if text actually contains Urdu/Arabic script ranges
                if re.search(r'[\u0600-\u06FF]', text):
                    text_blocks.append(text)
        
        if not text_blocks:
            return None, "Could not extract Urdu text from the page. The site might be dynamic (JavaScript)."

        # Return a random block that looks like a poem
        # We clean up excessive whitespace
        poem_candidate = random.choice(text_blocks)
        
        # Clean the text
        poem_candidate = re.sub(r'\s+', ' ', poem_candidate) # Remove multiple spaces
        poem_candidate = poem_candidate.strip()
        
        return poem_candidate, None

    except Exception as e:
        return None, str(e)

def generate_audio(text):
    """
    Generates an MP3 audio file from Urdu text using gTTS.
    """
    try:
        # gTTS supports Urdu ('ur')
        tts = gTTS(text=text, lang='ur', slow=False)
        audio_file = 'poem_song.mp3'
        tts.save(audio_file)
        return audio_file
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

# --- Main App ---

def main():
    local_css()
    
    st.markdown('<p class="nastaliq-title">اردو شاعری ایپ</p>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center; color:gray;">Poetry Crawler & Voice Generator</h3>', unsafe_allow_html=True)
    
    st.info("Note: This app works best on static websites (HTML-based). Dynamic sites (like Twitter or modern SPAs) may not render text correctly.")

    # Input Form
    with st.form("crawler_form"):
        col1, col2 = st.columns(2)
        with col1:
            poet_name = st.text_input("Poet Name (e.g., Allama Iqbal, Ghalib)", value="Allama Iqbal")
        with col2:
            website_url = st.text_input("Website Address", placeholder="https://ur.wikipedia.org/wiki/محمد_اقبال")
        
        submitted = st.form_submit_button("Crawl & Create Song")

    if submitted and website_url and poet_name:
        with st.spinner("Crawling the web for verses..."):
            poem_text, error = scrape_poetry(website_url, poet_name)
            
            if error:
                st.error(f"Error: {error}")
            elif poem_text:
                # Display Poet Name
                st.markdown(f'<div class="poet-name">— {poet_name} —</div>', unsafe_allow_html=True)
                
                # Display Poem in Nastaliq
                st.markdown(f'<div class="poem-container">{poem_text}</div>', unsafe_allow_html=True)

                # Generate Audio
                st.subheader("🎵 Generated Song (Recitation)")
                with st.spinner("Synthesizing voice..."):
                    audio_file = generate_audio(poem_text)
                    
                    if audio_file:
                        st.audio(audio_file)
                        
                        # Cleanup
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
            else:
                st.warning("No text found at the URL provided.")

if __name__ == "__main__":
    main()
