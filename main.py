#!/usr/bin/env python3
# main.py - Quran Video Creator with Professional AI Prompt

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
import shutil

# ========== CONFIGURATION ==========
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables!")

GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-robotics-er-1.5-preview",
    "gemma-3-27b-it",
    "gemma-3-1b-it",
    "gemma-3n-e2b-it",
    "gemma-3n-e4b-it",
    "gemma-3-4b-it"
]

OUTPUT_DIR = "videos"
HISTORY_JSON = "used_verses_history.json"
RSS_FILE = "rss.xml"
REPO = "uploadtiktok/Croma"
BRANCH = "main"
VIDEOS_PER_RUN = 3
# ====================================

# ========== RECITERS LIST ==========
RECITERS = [
    {"id": "Yasser_Ad-Dussary_128kbps", "name": "ياسر الدوسري"},
    {"id": "MaherAlMuaiqly128kbps", "name": "ماهر المعيقلي"},
    {"id": "Abu_Bakr_Ash-Shaatree_128kbps", "name": "أبوبكر الشاطري"},
    {"id": "Ibrahim_Akhdar_32kbps", "name": "ابراهيم الاخضر"},
    {"id": "Ahmed_ibn_Ali_al-Ajamy_128kbps_ketaballah.net", "name": "أحمد العجمي"},
    {"id": "Ayman_Sowaid_64kbps", "name": "أيمن رشدي سويد"},
    {"id": "Ghamadi_40kbps", "name": "سعد الغامدي"},
    {"id": "Abdul_Basit_Murattal_192kbps", "name": "عبدالباسط عبدالصمد مرتل"},
    {"id": "Abdul_Basit_Mujawwad_128kbps", "name": "عبدالباسط عبدالصمد مجود"},
    {"id": "Abdurrahmaan_As-Sudais_192kbps", "name": "عبدالرحمن السديس"},
    {"id": "Abdullah_Basfar_192kbps", "name": "عبدالله بصفر"},
    {"id": "Abdullaah_3awwaad_Al-Juhaynee_128kbps", "name": "عبد الله عواد الجهني"},
    {"id": "Ali_Jaber_64kbps", "name": "علي جابر"},
    {"id": "Hudhaify_128kbps", "name": "علي الحذيفي"},
    {"id": "Fares_Abbad_64kbps", "name": "فارس عباد"},
    {"id": "khalefa_al_tunaiji_64kbps", "name": "خليفة الطنيجي"},
    {"id": "Husary_128kbps_Mujawwad", "name": "محمود خليل الحصري مجود"},
    {"id": "Husary_128kbps", "name": "محمود خليل الحصري مرتل"},
    {"id": "Minshawy_Mujawwad_192kbps", "name": "محمد صديق المنشاوي مجود"},
    {"id": "Minshawy_Murattal_128kbps", "name": "محمد صديق المنشاوي مرتل"},
    {"id": "Mohammad_al_Tablaway_128kbps", "name": "محمد الطبلاوي"},
    {"id": "Muhammad_Ayyoub_128kbps", "name": "محمد أيوب"},
    {"id": "Muhammad_Jibreel_128kbps", "name": "محمد جبريل"},
    {"id": "Alafasy_128kbps", "name": "مشاري العفاسي"},
    {"id": "Nasser_Alqatami_128kbps", "name": "ناصر القطامي"},
    {"id": "Hani_Rifai_192kbps", "name": "هاني الرفاعي"},
]

HASHTAGS = ["#كرومات", "#كرومات_قرآنية", "#كروما", "#كروما_قرآنية", "#قرآن", "#تلاوة", "#تدبر"]

# ========== CLEANUP FUNCTIONS ==========

def clear_all_videos():
    """حذف جميع الفيديوهات القديمة"""
    videos_dir = Path(OUTPUT_DIR)
    if videos_dir.exists():
        for video in videos_dir.glob("*.mp4"):
            try:
                video.unlink()
                print(f"🗑️ Removed old video: {video.name}")
            except Exception as e:
                print(f"⚠️ Could not remove {video.name}: {e}")
    else:
        videos_dir.mkdir(parents=True, exist_ok=True)

def create_new_rss():
    """إنشاء ملف RSS جديد (فارغ)"""
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'Quran Video Feed - 3 Videos Daily'
    ET.SubElement(channel, 'description').text = 'Professional Quran recitation videos for chroma key'
    ET.SubElement(channel, 'link').text = f'https://github.com/uploadtiktok/Croma'
    ET.SubElement(channel, 'language').text = 'ar'
    
    xml_str = ET.tostring(rss, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    clean_xml = "\n".join(line for line in pretty_xml.split('\n') if line.strip())
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(clean_xml)
    print("✅ Created new empty RSS feed")

def update_rss_file(videos_data):
    """videos_data: list of (filename, title)"""
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'Quran Video Feed - 3 Videos Daily'
    ET.SubElement(channel, 'description').text = 'Professional Quran recitation videos for chroma key'
    ET.SubElement(channel, 'link').text = f'https://github.com/uploadtiktok/Croma'
    ET.SubElement(channel, 'language').text = 'ar'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    for filename, title in videos_data:
        video_url = f"https://raw.githubusercontent.com/uploadtiktok/Croma/main/{OUTPUT_DIR}/{filename}"
        pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        node = ET.SubElement(channel, 'item')
        ET.SubElement(node, 'title').text = title
        ET.SubElement(node, 'link').text = video_url
        ET.SubElement(node, 'pubDate').text = pub_date
        ET.SubElement(node, 'enclosure', url=video_url, type='video/mp4')
        ET.SubElement(node, 'guid', isPermaLink='false').text = video_url
    
    xml_str = ET.tostring(rss, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    clean_xml = "\n".join(line for line in pretty_xml.split('\n') if line.strip())
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(clean_xml)
    print(f"✅ RSS feed updated with {len(videos_data)} videos")

def init_json_history():
    if not os.path.exists(HISTORY_JSON):
        with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
            json.dump({"used_verses": []}, f, indent=2, ensure_ascii=False)
            print("✅ Created new history file")

def get_used_verses_list():
    try:
        with open(HISTORY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            used = [f"{item['surah']}:{item['from_verse']}-{item['to_verse']} ({item['topic']})" 
                    for item in data.get('used_verses', [])]
            if used:
                return "\n".join(used)
            return "لا توجد مقاطع سابقة"
    except:
        return "لا توجد مقاطع سابقة"

def save_to_history(surah, from_v, to_v, topic, reciter_name, subject):
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
        'subject': subject,
        'reciter': reciter_name,
        'timestamp': datetime.now().isoformat()
    })
    
    with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_ai_suggestion(used_verses_text):
    """استخدام البرومبت الاحترافي لاختيار آيات متكاملة"""
    
    prompt = f"""تصرف كخبير في علوم القرآن وصانع محتوى مرئي. أريد منك اختيار "مقطع قرآني" متكامل يصلح لإنتاج فيديو كروما، مع الالتزام بالشروط التالية:

1. اختيار سورة واختيار موضوع متكامل منها (مثل: عظمة الكون، صفات المؤمنين، أو مشاهد القيامة).
2. استخراج مجموعة آيات متتالية (من 4 إلى 7 آيات) لتشكل مقطعاً زمنياً كافياً (بين 45 إلى 90 ثانية عند التلاوة).
3. يجب أن تكون الآيات "محكمات" و "تامة المعنى"؛ بحيث يبدأ المقطع ببداية موضوع وينتهي بنهايته تماماً.
4. عرض النص بالرسم العثماني مع وضع رقم كل آية.
5. شرط عدم التكرار: يمنع منعاً باتاً اختيار آيات من السور أو المقاطع التي استخرجتها لي سابقاً. (هذه قائمة المقاطع المستبعدة):

{used_verses_text}

أمثلة لمستوى الجودة المطلوبة:
- مثال 1 (سورة الفرقان 63-67): موضوع "صفات عباد الرحمن".
- مثال 2 (سورة ق 6-11): موضوع "عظمة الخلق".
- مثال 3 (سورة النبأ 6-16): موضوع "نعم الله في الأرض".
- مثال 4 (سورة الإنسان 5-10): موضوع "جزاء الأبرار".
- مثال 5 (سورة الضحى كاملة): موضوع "السكينة والرضا".

و لا تركز على السور القصار فقط بل على جميع السور الـ 114. اختر من السور الطويلة أيضاً.

أخرج الإجابة بهذا التنسيق الدقيق:
السورة: [رقم السورة] - [اسم السورة]
الآيات: [من] إلى [إلى]
الموضوع: [وصف دقيق للموضوع]
عدد الآيات: [العدد]
التفسير الموجز: [شرح مختصر للمقطع]

لا تخرج أي شيء آخر غير هذا التنسيق."""
    
    for idx, model in enumerate(GEMINI_MODELS):
        try:
            print(f"    📡 Trying model: {model}...")
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text and ('السورة:' in text) and ('الآيات:' in text):
                    print(f"    ✅ Success with model: {model}")
                    return text
                else:
                    print(f"    ⚠️ Model {model} returned incomplete response")
            else:
                print(f"    ❌ Model {model} failed with status {response.status_code}")
                if response.status_code == 429:
                    print(f"    ⏳ Rate limited, waiting 3 seconds...")
                    time.sleep(3)
        except Exception as e:
            print(f"    ❌ Model {model} error: {str(e)[:50]}")
        
        if idx < len(GEMINI_MODELS) - 1:
            time.sleep(2)
    
    print("    ❌ All Gemini models failed!")
    return ""

def parse_ai_response(response_text):
    """استخراج البيانات من رد Gemini"""
    surah_num = None
    from_verse = None
    to_verse = None
    topic = "مقطع قرآني مميز"
    subject = ""
    
    for line in response_text.split('\n'):
        if 'السورة:' in line:
            match = re.search(r'(\d+)', line)
            if match:
                surah_num = int(match.group())
        elif 'الآيات:' in line:
            match = re.search(r'(\d+)\s*إلى\s*(\d+)', line)
            if match:
                from_verse = int(match.group(1))
                to_verse = int(match.group(2))
            else:
                match = re.search(r'(\d+)-(\d+)', line)
                if match:
                    from_verse = int(match.group(1))
                    to_verse = int(match.group(2))
        elif 'الموضوع:' in line:
            topic = line.replace('الموضوع:', '').strip()
        elif 'التفسير الموجز:' in line:
            subject = line.replace('التفسير الموجز:', '').strip()
    
    return surah_num, from_verse, to_verse, topic, subject

def get_surah_name(surah_num):
    """الحصول على اسم السورة بالعربية"""
    surah_names = {
        1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة",
        6: "الأنعام", 7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس",
        11: "هود", 12: "يوسف", 13: "الرعد", 14: "إبراهيم", 15: "الحجر",
        16: "النحل", 17: "الإسراء", 18: "الكهف", 19: "مريم", 20: "طه",
        21: "الأنبياء", 22: "الحج", 23: "المؤمنون", 24: "النور", 25: "الفرقان",
        26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم",
        31: "لقمان", 32: "السجدة", 33: "الأحزاب", 34: "سبأ", 35: "فاطر",
        36: "يس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر",
        41: "فصلت", 42: "الشورى", 43: "الزخرف", 44: "الدخان", 45: "الجاثية",
        46: "الأحقاف", 47: "محمد", 48: "الفتح", 49: "الحجرات", 50: "ق",
        51: "الذاريات", 52: "الطور", 53: "النجم", 54: "القمر", 55: "الرحمن",
        56: "الواقعة", 57: "الحديد", 58: "المجادلة", 59: "الحشر", 60: "الممتحنة",
        61: "الصف", 62: "الجمعة", 63: "المنافقون", 64: "التغابن", 65: "الطلاق",
        66: "التحريم", 67: "الملك", 68: "القلم", 69: "الحاقة", 70: "المعارج",
        71: "نوح", 72: "الجن", 73: "المزمل", 74: "المدثر", 75: "القيامة",
        76: "الإنسان", 77: "المرسلات", 78: "النبأ", 79: "النازعات", 80: "عبس",
        81: "التكوير", 82: "الإنفطار", 83: "المطففين", 84: "الإنشقاق", 85: "البروج",
        86: "الطارق", 87: "الأعلى", 88: "الغاشية", 89: "الفجر", 90: "البلد",
        91: "الشمس", 92: "الليل", 93: "الضحى", 94: "الشرح", 95: "التين",
        96: "العلق", 97: "القدر", 98: "البينة", 99: "الزلزلة", 100: "العاديات",
        101: "القارعة", 102: "التكاثر", 103: "العصر", 104: "الهمزة", 105: "الفيل",
        106: "قريش", 107: "الماعون", 108: "الكوثر", 109: "الكافرون", 110: "النصر",
        111: "المسد", 112: "الإخلاص", 113: "الفلق", 114: "الناس"
    }
    return surah_names.get(surah_num, "سورة")

def create_video(surah_num, surah_ar, from_verse, to_verse, reciter_id, reciter_name, topic, video_num):
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    temp_dir = f"/tmp/q_video_{int(time.time())}_{video_num}_{random.randint(1, 9999)}"
    os.makedirs(temp_dir, exist_ok=True)
    
    total_duration = 0
    verses_processed = []
    
    for verse in range(from_verse, to_verse + 1):
        s = f"{surah_num:03d}"
        v = f"{verse:03d}"
        
        print(f"    - Processing verse {verse}...")
        
        audio_url = f"https://www.everyayah.com/data/{reciter_id}/{s}{v}.mp3"
        audio_path = f"{temp_dir}/{verse}.mp3"
        audio_downloaded = False
        
        for retry in range(2):
            try:
                r = requests.get(audio_url, timeout=30)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(audio_path, 'wb') as f:
                        f.write(r.content)
                    audio_downloaded = True
                    break
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
        
        if not audio_downloaded:
            print(f"      ⚠️ Verse {verse} audio not available")
            continue
        
        text_url = f"https://legacy.quran.com/images/ayat_retina/{surah_num}_{verse}.png"
        text_path = f"{temp_dir}/{verse}_text.png"
        try:
            r = requests.get(text_url, timeout=30)
            if r.status_code == 200:
                with open(text_path, 'wb') as f:
                    f.write(r.content)
        except:
            pass
        
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout else 5.0
        total_duration += duration
        
        frame_path = f"{temp_dir}/{verse}_frame.jpg"
        if os.path.exists(text_path) and os.path.getsize(text_path) > 100:
            try:
                subprocess.run([
                    'convert', '-size', '1080x1920', 'xc:black',
                    '(', text_path, '-trim', '+repage', '-resize', '900x', '-fill', 'white', '-colorize', '100%', ')',
                    '-gravity', 'center', '-composite', frame_path
                ], capture_output=True, timeout=30)
            except:
                subprocess.run([
                    'convert', '-size', '1080x1920', 'xc:black',
                    '-gravity', 'center', '-pointsize', '60', '-fill', 'white',
                    '-annotate', '0', f"سورة {surah_ar}\nالآية {verse}", frame_path
                ], capture_output=True)
        else:
            subprocess.run([
                'convert', '-size', '1080x1920', 'xc:black',
                '-gravity', 'center', '-pointsize', '60', '-fill', 'white',
                '-annotate', '0', f"سورة {surah_ar}\nالآية {verse}", frame_path
            ], capture_output=True)
        
        verses_processed.append(verse)
        print(f"      ✓ Verse {verse} done")
    
    if not verses_processed:
        return None
    
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
    
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', audio_list,
        '-c', 'copy', f"{temp_dir}/merged.mp3"
    ], capture_output=True)
    
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', f"{temp_dir}/merged.mp3"
    ], capture_output=True, text=True)
    merged_duration = float(result.stdout.strip()) if result.stdout else total_duration
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"quran_s{surah_num}_v{from_verse}-{to_verse}_{timestamp}_{video_num}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
        '-i', f"{temp_dir}/merged.mp3", '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-r', '25', '-t', str(merged_duration), '-c:a', 'aac', '-b:a', '192k', output_path
    ], capture_output=True)
    
    subprocess.run(['rm', '-rf', temp_dir])
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return output_filename
    return None

def create_single_video(video_number):
    """إنشاء مقطع فيديو واحد باستخدام AI"""
    
    print(f"\n{'='*40}")
    print(f"  Creating Video {video_number}/{VIDEOS_PER_RUN}")
    print(f"{'='*40}")
    
    used_verses_text = get_used_verses_list()
    
    print("\n🤖 Gemini is selecting a complete Quranic passage...")
    ai_response = get_ai_suggestion(used_verses_text)
    
    if not ai_response:
        print("❌ Failed to get AI response")
        return None
    
    surah_num, from_verse, to_verse, topic, subject = parse_ai_response(ai_response)
    
    if not surah_num or not from_verse or not to_verse:
        print("❌ Failed to parse AI response")
        print(f"Raw response: {ai_response[:200]}")
        return None
    
    surah_ar = get_surah_name(surah_num)
    reciter = random.choice(RECITERS)
    reciter_id = reciter['id']
    reciter_name = reciter['name']
    
    verse_count = to_verse - from_verse + 1
    
    print(f"\n✨ AI Selection:")
    print(f"📖 Surah: {surah_num} - {surah_ar}")
    print(f"🗡️ Verses: {from_verse} - {to_verse} ({verse_count} verses)")
    print(f"💡 Topic: {topic}")
    if subject:
        print(f"📝 Summary: {subject}")
    print(f"🎙️ Reciter: {reciter_name}")
    
    print("\n🎬 Creating video...")
    filename = create_video(surah_num, surah_ar, from_verse, to_verse, 
                           reciter_id, reciter_name, topic, video_number)
    
    if filename:
        save_to_history(surah_num, from_verse, to_verse, topic, reciter_name, subject)
        hashtags_str = " ".join(HASHTAGS)
        title = f"سورة {surah_ar} | الآيات {from_verse}-{to_verse} | {topic} | {reciter_name} {hashtags_str}"
        print(f"\n✅ Video {video_number} completed!")
        return (filename, title)
    else:
        print(f"\n❌ Video {video_number} failed")
        return None

def main():
    print("==========================================")
    print("   Quran Video Creator (Professional AI)")
    print("==========================================")
    print(f"\n🎯 Target: {VIDEOS_PER_RUN} videos today")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Available models: {len(GEMINI_MODELS)} models")
    
    print("\n🗑️ Cleaning up old videos...")
    clear_all_videos()
    create_new_rss()
    init_json_history()
    
    successful_videos = []
    
    for i in range(1, VIDEOS_PER_RUN + 1):
        result = create_single_video(i)
        if result:
            successful_videos.append(result)
        
        if i < VIDEOS_PER_RUN:
            print("\n⏳ Waiting 5 seconds before next video...")
            time.sleep(5)
    
    if successful_videos:
        update_rss_file(successful_videos)
        
        print("\n" + "="*50)
        print(f"✅ SUMMARY: Created {len(successful_videos)}/{VIDEOS_PER_RUN} videos")
        print("="*50)
        
        for idx, (filename, title) in enumerate(successful_videos, 1):
            video_url = f"https://raw.githubusercontent.com/uploadtiktok/Croma/main/{OUTPUT_DIR}/{filename}"
            print(f"\n📹 Video {idx}:")
            print(f"   File: {filename}")
            print(f"   URL: {video_url}")
        
        print(f"\n📝 RSS Feed updated")
        print(f"📊 History saved: {HISTORY_JSON}")
    else:
        print("\n❌ No videos were created successfully!")

if __name__ == "__main__":
    main()
