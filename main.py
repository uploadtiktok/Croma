#!/usr/bin/env python3
# main.py - Quran Video Creator with RSS Feed (3 Videos Per Run - No Accumulation)

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

# قائمة جميع النماذج المتاحة
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

# ========== SURAH LIST ==========
ALL_SURAH_NAMES = [
    "1|الفاتحة|Al-Fatiha", "2|البقرة|Al-Baqarah", "3|آل عمران|Aal-Imran",
    "4|النساء|An-Nisa", "5|المائدة|Al-Maidah", "6|الأنعام|Al-Anam",
    "7|الأعراف|Al-Araf", "8|الأنفال|Al-Anfal", "9|التوبة|At-Tawbah",
    "10|يونس|Yunus", "11|هود|Hud", "12|يوسف|Yusuf", "13|الرعد|Ar-Rad",
    "14|إبراهيم|Ibrahim", "15|الحجر|Al-Hijr", "16|النحل|An-Nahl",
    "17|الإسراء|Al-Isra", "18|الكهف|Al-Kahf", "19|مريم|Maryam",
    "20|طه|Taha", "21|الأنبياء|Al-Anbiya", "22|الحج|Al-Hajj",
    "23|المؤمنون|Al-Muminun", "24|النور|An-Nur", "25|الفرقان|Al-Furqan",
    "26|الشعراء|Ash-Shuara", "27|النمل|An-Naml", "28|القصص|Al-Qasas",
    "29|العنكبوت|Al-Ankabut", "30|الروم|Ar-Rum", "31|لقمان|Luqman",
    "32|السجدة|As-Sajda", "33|الأحزاب|Al-Ahzab", "34|سبأ|Saba",
    "35|فاطر|Fatir", "36|يس|Ya-Sin", "37|الصافات|As-Saffat",
    "38|ص|Sad", "39|الزمر|Az-Zumar", "40|غافر|Ghafir",
    "41|فصلت|Fussilat", "42|الشورى|Ash-Shura", "43|الزخرف|Az-Zukhruf",
    "44|الدخان|Ad-Dukhan", "45|الجاثية|Al-Jathiya", "46|الأحقاف|Al-Ahqaf",
    "47|محمد|Muhammad", "48|الفتح|Al-Fath", "49|الحجرات|Al-Hujurat",
    "50|ق|Qaf", "51|الذاريات|Adh-Dhariyat", "52|الطور|At-Tur",
    "53|النجم|An-Najm", "54|القمر|Al-Qamar", "55|الرحمن|Ar-Rahman",
    "56|الواقعة|Al-Waqia", "57|الحديد|Al-Hadid", "58|المجادلة|Al-Mujadila",
    "59|الحشر|Al-Hashr", "60|الممتحنة|Al-Mumtahina", "61|الصف|As-Saff",
    "62|الجمعة|Al-Jumuah", "63|المنافقون|Al-Munafiqun", "64|التغابن|At-Taghabun",
    "65|الطلاق|At-Talaq", "66|التحريم|At-Tahrim", "67|الملك|Al-Mulk",
    "68|القلم|Al-Qalam", "69|الحاقة|Al-Haqqah", "70|المعارج|Al-Maarij",
    "71|نوح|Nuh", "72|الجن|Al-Jinn", "73|المزمل|Al-Muzzammil",
    "74|المدثر|Al-Muddathir", "75|القيامة|Al-Qiyamah", "76|الإنسان|Al-Insan",
    "77|المرسلات|Al-Mursalat", "78|النبأ|An-Naba", "79|النازعات|An-Naziat",
    "80|عبس|Abasa", "81|التكوير|At-Takwir", "82|الإنفطار|Al-Infitar",
    "83|المطففين|Al-Mutaffifin", "84|الإنشقاق|Al-Inshiqaq", "85|البروج|Al-Buruj",
    "86|الطارق|At-Tariq", "87|الأعلى|Al-Ala", "88|الغاشية|Al-Ghashiyah",
    "89|الفجر|Al-Fajr", "90|البلد|Al-Balad", "91|الشمس|Ash-Shams",
    "92|الليل|Al-Lail", "93|الضحى|Ad-Duha", "94|الشرح|Ash-Sharh",
    "95|التين|At-Tin", "96|العلق|Al-Alaq", "97|القدر|Al-Qadr",
    "98|البينة|Al-Bayyinah", "99|الزلزلة|Az-Zalzalah", "100|العاديات|Al-Adiyat",
    "101|القارعة|Al-Qariah", "102|التكاثر|At-Takathur", "103|العصر|Al-Asr",
    "104|الهمزة|Al-Humazah", "105|الفيل|Al-Fil", "106|قريش|Quraish",
    "107|الماعون|Al-Maun", "108|الكوثر|Al-Kawthar", "109|الكافرون|Al-Kafirun",
    "110|النصر|An-Nasr", "111|المسد|Al-Masad", "112|الإخلاص|Al-Ikhlas",
    "113|الفلق|Al-Falaq", "114|الناس|An-Nas",
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
    ET.SubElement(channel, 'description').text = 'Daily Quran recitation videos (3 videos per day) with black screen'
    ET.SubElement(channel, 'link').text = f'https://github.com/{REPO}'
    ET.SubElement(channel, 'language').text = 'ar'
    
    # Pretty print
    xml_str = ET.tostring(rss, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    clean_xml = "\n".join(line for line in pretty_xml.split('\n') if line.strip())
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(clean_xml)
    print("✅ Created new empty RSS feed")

def update_rss_file(videos_data):
    """videos_data: list of (filename, title) - يحتفظ فقط بالمقاطع الجديدة"""
    # إنشاء RSS جديد (لا نحتفظ بالقديم)
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'Quran Video Feed - 3 Videos Daily'
    ET.SubElement(channel, 'description').text = 'Daily Quran recitation videos (3 videos per day) with black screen'
    ET.SubElement(channel, 'link').text = f'https://github.com/{REPO}'
    ET.SubElement(channel, 'language').text = 'ar'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # إضافة المقاطع الجديدة فقط
    for filename, title in videos_data:
        video_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{OUTPUT_DIR}/{filename}"
        pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        node = ET.SubElement(channel, 'item')
        ET.SubElement(node, 'title').text = title
        ET.SubElement(node, 'link').text = video_url
        ET.SubElement(node, 'pubDate').text = pub_date
        ET.SubElement(node, 'enclosure', url=video_url, type='video/mp4')
        ET.SubElement(node, 'guid', isPermaLink='false').text = video_url
    
    # Pretty print
    xml_str = ET.tostring(rss, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    clean_xml = "\n".join(line for line in pretty_xml.split('\n') if line.strip())
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(clean_xml)
    print(f"✅ RSS feed updated with {len(videos_data)} new videos")

# ========== MAIN FUNCTIONS ==========

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
    """تجربة جميع النماذج حتى النجاح"""
    prompt = f"""You are a Quran expert. Select powerful, impactful verses from Surah {surah_num} ({surah_name}).

CRITICAL REQUIREMENTS:
- Select 2-7 continuous verses from Surah {surah_num}
- ABSOLUTELY AVOID these previously used verse ranges: {used_verses}
- Choose verses from ANYWHERE in the surah (beginning, middle, or end)
- ALL verses must talk about ONE SINGLE TOPIC only
- Total recitation duration must be 60 seconds or less
- IMPORTANT: The verse must exist and have valid recitation audio available online

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
                timeout=45
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
                if response.status_code == 429:
                    print(f"    ⏳ Rate limited, waiting 3 seconds...")
                    time.sleep(3)
        except Exception as e:
            print(f"    ❌ Model {model} error: {str(e)[:50]}")
        
        if idx < len(GEMINI_MODELS) - 1:
            time.sleep(2)
    
    print("    ❌ All Gemini models failed!")
    return ""

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
        
        # Download audio
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
                    print(f"      Audio file too small, retry {retry+1}/2")
                    time.sleep(1)
            except:
                print(f"      Download failed, retry {retry+1}/2")
                time.sleep(1)
        
        if not audio_downloaded:
            print(f"      ⚠️ Verse {verse} audio not available, skipping...")
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
        
        # Create frame
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
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return output_filename
    else:
        print(f"    Video file too small or missing")
        return None

def create_single_video(video_number):
    """إنشاء مقطع فيديو واحد، مع إعادة المحاولة إذا فشل"""
    max_retries = 2
    
    for attempt in range(max_retries):
        print(f"\n{'='*40}")
        print(f"  Creating Video {video_number}/{VIDEOS_PER_RUN} (Attempt {attempt+1}/{max_retries})")
        print(f"{'='*40}")
        
        reciter = random.choice(RECITERS)
        reciter_id = reciter['id']
        reciter_name = reciter['name']
        
        surah_line = random.choice(ALL_SURAH_NAMES)
        surah_num = int(surah_line.split('|')[0])
        surah_ar = surah_line.split('|')[1]
        surah_en = surah_line.split('|')[2]
        
        used_verses = get_used_verses_list()
        
        print(f"\n🎙️ Reciter: {reciter_name}")
        print(f"📖 Selected Surah: {surah_num} - {surah_ar} ({surah_en})")
        print("🤖 Gemini is selecting fresh verses...")
        
        ai_response = get_ai_suggestion_with_fallback(surah_num, surah_ar, used_verses)
        
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
        
        if not from_verse or not to_verse:
            print("⚠️ AI response invalid, using random verses")
            from_verse = random.randint(1, 100)
            to_verse = min(from_verse + random.randint(2, 5), 200)
            if from_verse > to_verse:
                from_verse, to_verse = to_verse, from_verse
        
        verse_count = to_verse - from_verse + 1
        if verse_count > 6:
            to_verse = from_verse + 5
        
        # التحقق من صحة الآيات
        if surah_num == 45 and from_verse > 37:
            from_verse = 1
            to_verse = 5
        
        print(f"\n✨ Selection:")
        print(f"📖 Surah: {surah_num} - {surah_ar}")
        print(f"🗡️ Verses: {from_verse} - {to_verse} ({to_verse - from_verse + 1} verses)")
        print(f"💡 Topic: {topic}")
        
        print("\n🎬 Creating video...")
        filename = create_video(surah_num, surah_ar, from_verse, to_verse, 
                               reciter_id, reciter_name, topic, video_number)
        
        if filename:
            save_to_history(surah_num, from_verse, to_verse, topic, reciter_name)
            hashtags_str = " ".join(HASHTAGS)
            title = f"سورة {surah_ar} | الآيات {from_verse}-{to_verse} | {reciter_name} {hashtags_str}"
            print(f"\n✅ Video {video_number} completed!")
            return (filename, title)
        else:
            print(f"\n❌ Video {video_number} failed on attempt {attempt+1}")
            if attempt < max_retries - 1:
                print("⏳ Retrying with different verses...")
                time.sleep(5)
    
    return None

def main():
    print("==========================================")
    print("   Quran Video Creator (3 Videos Per Day)")
    print("==========================================")
    print(f"\n🎯 Target: {VIDEOS_PER_RUN} videos today")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Available models: {len(GEMINI_MODELS)} models")
    print("\n🗑️ Cleaning up old videos (keeping only today's 3 videos)...")
    
    # تنظيف الفيديوهات القديمة
    clear_all_videos()
    
    # إنشاء ملف RSS جديد
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
            video_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{OUTPUT_DIR}/{filename}"
            print(f"\n📹 Video {idx}:")
            print(f"   File: {filename}")
            print(f"   URL: {video_url}")
        
        print(f"\n📝 RSS Feed updated (only today's {len(successful_videos)} videos)")
        print(f"📊 History saved: {HISTORY_JSON}")
        print(f"🗑️ Old videos deleted - only today's videos remain")
    else:
        print("\n❌ No videos were created successfully!")

if __name__ == "__main__":
    main()
