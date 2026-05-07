#!/usr/bin/env python3
# main.py - Quran Video Creator with RSS Feed (3 Videos Per Run)

import os
import json
import subprocess
import requests
import random
import re
from pathlib import Path
from datetime import datetime
from xml.dom import minidom
from xml.etree import ElementTree as ET
import time

# ========== CONFIGURATION ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables!")

GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-latest"
]

OUTPUT_DIR = "videos"
HISTORY_JSON = "used_verses_history.json"
RSS_FILE = "rss.xml"
REPO = "uploadtiktok/Croma"
BRANCH = "main"
VIDEOS_PER_RUN = 3  # عدد المقاطع التي سيتم إنشاؤها في كل تشغيل
# ====================================

# ... (RECITERS, ALL_SURAH_NAMES, HASHTAGS كما هي)

def init_json_history():
    if not os.path.exists(HISTORY_JSON):
        with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
            json.dump({"used_verses": []}, f, indent=2, ensure_ascii=False)
            print("✅ Created new history file")

def get_used_verses_list():
    try:
        with open(HISTORY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            used = [f"{item['surah']}:{item['from_verse']}-{item['to_verse']}" 
                    for item in data.get('used_verses', [])]
            return ','.join(used) if used else "None"
    except:
        return "None"

def save_to_history(surah, from_v, to_v, topic, reciter_name):
    try:
        with open(HISTORY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"used_verses": []}
    
    data['used_verses'].append({
        'surah': surah,
        'from_verse': from_v,
        'to_verse': to_v,
        'topic': topic,
        'reciter': reciter_name,
        'timestamp': datetime.now().isoformat()
    })
    
    with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_ai_suggestion_with_fallback(surah_num, surah_name, used_verses):
    prompt = f"""You are a Quran expert. Select powerful, impactful verses from Surah {surah_num} ({surah_name}).

CRITICAL REQUIREMENTS:
- Select 2-7 continuous verses from Surah {surah_num}
- ABSOLUTELY AVOID these previously used verse ranges: {used_verses}
- Choose verses from ANYWHERE in the surah (beginning, middle, or end)
- ALL verses must talk about ONE SINGLE TOPIC only
- Total recitation duration must be 60 seconds or less

Output format EXACTLY as:
FROM: [starting verse number]
TO: [ending verse number]
TOPIC: [the single topic of these verses]

Output nothing else."""
    
    for idx, model in enumerate(GEMINI_MODELS):
        try:
            print(f"    📡 Trying model: {model}...")
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text and ('FROM:' in text) and ('TO:' in text):
                    print(f"    ✅ Success with model: {model}")
                    return text
                else:
                    print(f"    ⚠️ Model {model} returned empty response")
            else:
                print(f"    ❌ Model {model} failed with status {response.status_code}")
        except Exception as e:
            print(f"    ❌ Model {model} error: {str(e)[:50]}")
        
        if idx < len(GEMINI_MODELS) - 1:
            time.sleep(1)
    
    print("    ❌ All Gemini models failed!")
    return ""

def create_video(surah_num, surah_ar, from_verse, to_verse, reciter_id, reciter_name, topic, video_num):
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    temp_dir = f"/tmp/q_video_{int(time.time())}_{video_num}"
    os.makedirs(temp_dir, exist_ok=True)
    
    total_duration = 0
    verses_processed = []
    
    for verse in range(from_verse, to_verse + 1):
        s = f"{surah_num:03d}"
        v = f"{verse:03d}"
        
        print(f"    - Processing verse {verse}...")
        
        # Download audio
        audio_url = f"https://www.everyayah.com/data/{reciter_id}/{s}{v}.mp3"
        audio_path = f"{temp_dir}/{verse}.mp3"
        try:
            r = requests.get(audio_url, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(audio_path, 'wb') as f:
                    f.write(r.content)
            else:
                print(f"      Audio not available for verse {verse}")
                continue
        except:
            print(f"      Failed to download audio for verse {verse}")
            continue
        
        # Download text image
        text_url = f"https://legacy.quran.com/images/ayat_retina/{surah_num}_{verse}.png"
        text_path = f"{temp_dir}/{verse}_text.png"
        try:
            r = requests.get(text_url, timeout=30)
            if r.status_code == 200:
                with open(text_path, 'wb') as f:
                    f.write(r.content)
        except:
            pass
        
        # Get duration
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout else 5.0
        total_duration += duration
        
        # Create frame with black background
        frame_path = f"{temp_dir}/{verse}_frame.jpg"
        if os.path.exists(text_path):
            subprocess.run([
                'convert', '-size', '1080x1920', 'xc:black',
                '(', text_path, '-trim', '+repage', '-resize', '900x', '-fill', 'white', '-colorize', '100%', ')',
                '-gravity', 'center', '-composite', frame_path
            ], capture_output=True)
        else:
            subprocess.run([
                'convert', '-size', '1080x1920', 'xc:black',
                '-gravity', 'center', '-pointsize', '80', '-fill', 'white',
                '-annotate', '0', f"سورة {surah_ar}\nالآية {verse}", frame_path
            ], capture_output=True)
        
        verses_processed.append(verse)
        print(f"      ✓ Verse {verse} done")
    
    if not verses_processed:
        print("    No verses processed successfully")
        return None
    
    # Create concat files
    concat_file = f"{temp_dir}/concat.txt"
    audio_list = f"{temp_dir}/audio_list.txt"
    
    with open(concat_file, 'w') as f:
        for verse in verses_processed:
            duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                           '-of', 'default=noprint_wrappers=1:nokey=1', f"{temp_dir}/{verse}.mp3"]
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip()) if result.stdout else 5.0
            f.write(f"file '{temp_dir}/{verse}_frame.jpg'\n")
            f.write(f"duration {duration}\n")
        last_verse = verses_processed[-1]
        f.write(f"file '{temp_dir}/{last_verse}_frame.jpg'\n")
    
    with open(audio_list, 'w') as f:
        for verse in verses_processed:
            f.write(f"file '{temp_dir}/{verse}.mp3'\n")
    
    # Merge audio
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', audio_list,
        '-c', 'copy', f"{temp_dir}/merged.mp3"
    ], capture_output=True)
    
    # Get merged duration
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', f"{temp_dir}/merged.mp3"
    ], capture_output=True, text=True)
    merged_duration = float(result.stdout.strip()) if result.stdout else total_duration
    
    # Create final video
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"quran_s{surah_num}_v{from_verse}-{to_verse}_{timestamp}_{video_num}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
        '-i', f"{temp_dir}/merged.mp3", '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-r', '25', '-t', str(merged_duration), '-c:a', 'aac', '-b:a', '192k', output_path
    ], capture_output=True)
    
    # Cleanup
    subprocess.run(['rm', '-rf', temp_dir])
    
    return output_filename

def update_rss_file(videos_data):
    """videos_data: list of (filename, title)"""
    current_items = []
    if os.path.exists(RSS_FILE):
        try:
            tree = ET.parse(RSS_FILE)
            root = tree.getroot()
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                if link:
                    current_items.append({'title': title, 'link': link, 'pub_date': pub_date})
        except:
            pass
    
    # Create new items
    new_items = []
    for filename, title in videos_data:
        video_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{OUTPUT_DIR}/{filename}"
        pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        new_items.append({'title': title, 'link': video_url, 'pub_date': pub_date})
    
    # Combine (newest first)
    all_items = new_items + current_items[:50]  # احتفظ بآخر 50 مقطع
    
    # Create RSS
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'Quran Video Feed - 3 Videos Daily'
    ET.SubElement(channel, 'description').text = 'Daily Quran recitation videos (3 videos per day) with black screen'
    ET.SubElement(channel, 'link').text = f'https://github.com/{REPO}'
    ET.SubElement(channel, 'language').text = 'ar'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    for item in all_items:
        node = ET.SubElement(channel, 'item')
        ET.SubElement(node, 'title').text = item['title']
        ET.SubElement(node, 'link').text = item['link']
        ET.SubElement(node, 'pubDate').text = item['pub_date']
        ET.SubElement(node, 'enclosure', url=item['link'], type='video/mp4')
        ET.SubElement(node, 'guid', isPermaLink='false').text = item['link']
    
    # Pretty print
    xml_str = ET.tostring(rss, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    clean_xml = "\n".join(line for line in pretty_xml.split('\n') if line.strip())
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(clean_xml)

def create_single_video(video_number):
    """إنشاء مقطع فيديو واحد"""
    print(f"\n{'='*40}")
    print(f"  Creating Video {video_number}/{VIDEOS_PER_RUN}")
    print(f"{'='*40}")
    
    # Select random reciter
    reciter = random.choice(RECITERS)
    reciter_id = reciter['id']
    reciter_name = reciter['name']
    
    # Select random surah
    surah_line = random.choice(ALL_SURAH_NAMES)
    surah_num = int(surah_line.split('|')[0])
    surah_ar = surah_line.split('|')[1]
    surah_en = surah_line.split('|')[2]
    
    used_verses = get_used_verses_list()
    
    print(f"\n🎙️ Reciter: {reciter_name}")
    print(f"📖 Selected Surah: {surah_num} - {surah_ar} ({surah_en})")
    print("🤖 Gemini is selecting fresh verses...")
    
    # Get AI suggestion
    ai_response = get_ai_suggestion_with_fallback(surah_num, surah_ar, used_verses)
    
    # Parse AI response
    from_verse = None
    to_verse = None
    topic = "Powerful Quranic Verses"
    
    for line in ai_response.split('\n'):
        if line.startswith('FROM:'):
            match = re.search(r'\d+', line)
            if match:
                from_verse = int(match.group())
        elif line.startswith('TO:'):
            match = re.search(r'\d+', line)
            if match:
                to_verse = int(match.group())
        elif line.startswith('TOPIC:'):
            topic = line.replace('TOPIC:', '').strip()
    
    # Fallback if AI fails
    if not from_verse or not to_verse:
        print("⚠️ AI response invalid, using random verses")
        from_verse = random.randint(1, 50)
        to_verse = from_verse + random.randint(1, 4)
    
    verse_count = to_verse - from_verse + 1
    if verse_count > 7:
        to_verse = from_verse + 6
    
    print(f"\n✨ Selection:")
    print(f"📖 Surah: {surah_num} - {surah_ar}")
    print(f"🗡️ Verses: {from_verse} - {to_verse} ({to_verse - from_verse + 1} verses)")
    print(f"💡 Topic: {topic}")
    
    # Create video
    print("\n🎬 Creating video...")
    filename = create_video(surah_num, surah_ar, from_verse, to_verse, 
                           reciter_id, reciter_name, topic, video_number)
    
    if filename:
        # Save to history
        save_to_history(surah_num, from_verse, to_verse, topic, reciter_name)
        
        # Create title with hashtags
        hashtags_str = " ".join(HASHTAGS)
        title = f"سورة {surah_ar} | الآيات {from_verse}-{to_verse} | {reciter_name} {hashtags_str}"
        
        print(f"\n✅ Video {video_number} completed!")
        return (filename, title)
    else:
        print(f"\n❌ Video {video_number} failed!")
        return None

def main():
    print("==========================================")
    print("   Quran Video Creator (3 Videos Per Day)")
    print("==========================================")
    print(f"\n🎯 Target: {VIDEOS_PER_RUN} videos today")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    init_json_history()
    
    successful_videos = []
    
    for i in range(1, VIDEOS_PER_RUN + 1):
        result = create_single_video(i)
        if result:
            successful_videos.append(result)
        
        # انتظر بين المقاطع لتجنب الضغط على الخوادم
        if i < VIDEOS_PER_RUN:
            print("\n⏳ Waiting 5 seconds before next video...")
            time.sleep(5)
    
    # تحديث RSS بعد الانتهاء من جميع المقاطع
    if successful_videos:
        update_rss_file(successful_videos)
        
        print("\n" + "="*50)
        print(f"✅ SUMMARY: Created {len(successful_videos)}/{VIDEOS_PER_RUN} videos")
        print("="*50)
        
        for idx, (filename, title) in enumerate(successful_videos, 1):
            video_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{OUTPUT_DIR}/{filename}"
            print(f"\n📹 Video {idx}:")
            print(f"   File: {filename}")
            print(f"   URL: {video_url}")
        
        print(f"\n📝 RSS Feed updated: {RSS_FILE}")
        print(f"📊 History saved: {HISTORY_JSON}")
    else:
        print("\n❌ No videos were created successfully!")

if __name__ == "__main__":
    main()
