import os
import re
import difflib
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from database import (
    setup_database,
    user_exists,
    save_user,
    get_users,
    get_user_count,
    save_attempt,
    save_mistake,
    get_statistics,
    get_common_mistakes,
)

# =========================================================
# الإعدادات الأساسية
# =========================================================
TOKEN = os.getenv("BOT_TOKEN", "8654982121:AAEjqWoi8gWMD12XWttXBXBdkQev-_YITCw")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6172479204))

# =========================================================
# بيانات الدروس والقطع الإملائية
# =========================================================
LESSONS = {
    "lesson1": {
        "name": "رسم التاء المفتوحة والتاء المربوطة",
        "pieces": {
            "piece1": {
                "name": "صفحات ماضٍ",
                "audio": "audio/piece1.mp3",
                "text": """ ليت الأيام تعود إلى الوراء، فترى يا بني أمجاد آبائك وأجدادك. كانت شمسهم تسطع في كل أرض. ليتك تفتح كتاب الأيام وتقرأ ما في سطوره من حكم وعبر، وتلتفت إلى ما قدموا لنا من مآثر عظيمة. كانوا أعلامًا في الكرامة، وهم الأجواد أوقات الضيق. هم الفرسان في ساحات الوغى، وهم العاملون في صمت وإخلاص، وهم المتحدون وقت التفرق والشتات. أين نحن الآن من أبناء يعيدون مجد آبائهم، ويمتلكون كرم الخلق مع كرم الكف، وتستيقظ في صدورهم النخوة والشجاعة، فيبعثوا الأمل فينا من جديد. """,
            },
            "piece2": {
                "name": "القهوة",
                "audio": "audio/piece2.mp3",
                "text": """ القهوة من أكثر المشروبات المنتشرة بين أبناء وطننا الغالي، فهي رمز للجود والكرم وحسن الضيافة. والقهوة ثمرة شجيرات دائمة الخضرة تنمو في المناطق المائلة إلى الحرارة. وأول من اكتشف القهوة أحد رعاة الماشية، حينما لاحظ أن ماشيته ظلت في ليلة من الليالي في حركة دائمة ودون نوم؛ لأنها أكلت نباتات برية معينة. وفي الليلة التالية أكل الراعي من هذه النباتات، فطار النوم من عينيه. وتعد القهوة من أهم المشروبات المنتشرة بين أبناء المملكة، عامتهم وخاصتهم. ويضيف بعض هواة شرب القهوة إليها الهيل أو الزنجبيل أو القرنفل. """,
            },
        },
    },
    "lesson2": {
        "name": "رسم همزة القطع",
        "pieces": {
            "piece3": {
                "name": "جزاء البخيل",
                "audio": "audio/piece3.mp3",
                "text": """ اشتهر أحد الكتاب بالبخل حتى أصبح يفتخر به أمام أصدقائه، ثم بدا له أن يؤلف كتابًا في مدح البخلاء، ثم قدمه إلى أمير عرف بإكرام الكتاب، مؤملًا أن يحظى بجائزة ثمينة. فلما قرأه الأمير وعرف فحواه، كتب إلى المؤلف يقول: قرأت مؤلفك الثمين فأعجبت به إعجابًا عظيمًا، فما أظرف ما كتبت فيه! وأنا أهنئك بهذا الكتاب، وأتمنى له رواجًا سريعًا، إنه يحبب البخل إلى الناس ويزينه إليهم. وكنت أردت أن أكافئك على هذا الجهد تقديرًا لأتعابك، وتهيئة لإخراج أمثاله من الكتب. لكنني رأيت أن أطيع نصائحك، فأقبض يدي عن العطاء، لأنك مدحت البخل والبخلاء. ومن استرشد برأي الكتاب فقد سلك سبيل المتأدبين، فهل بعد هذا ستمدح الكرم والكرماء؟ """,
            },
            "piece4": {
                "name": "المرء بأصغريه",
                "audio": "audio/piece4.mp3",
                "text": """ دخل على عمر بن عبد العزيز، خامس الخلفاء الراشدين، في أول خلافته وفود المهنئين، فتقدم وفد الحجاز بين يديه، فقام من بينهم غلام لم يتجاوز الحادية عشرة من عمره. وأراد أن يتكلم عن قومه، فقال له عمر: اجلس أنت وليقم من هو أسن منك. فقال الغلام: أيدك الله يا أمير المؤمنين، المرء بأصغريه: قلبه ولسانه، فإذا منح الله العبد لسانًا لافظًا وقلبًا حافظًا، فقد استحق الكلام. ولو أن الأمر يا أمير المؤمنين بالسن، لكان في الأمة من هو أحق منك بمجلسك هذا. فسر عمر من حسن جوابه وفصاحة لسانه، وأكرمه، وقضى حوائج قومه. """,
            },
        },
    },
    "lesson3": {
        "name": "قطع إضافية",
        "pieces": {
            "piece5": {
                "name": "أشرقت الشمس",
                "audio": "audio/piece5.mp3",
                "text": """ أشرقت الشمس، وأرسلت أشعتها إلى المزارع والحقول، وقد اكتست الأرض حلة زاهية الألوان، وتناثرت الأزهار بين الرياض، وانطلقت الأطيار تغرد، والفراشة الجميلة تنتقل من زهرة إلى زهرة بألوانها المبدعة. """,
            }
        },
    },
}

user_attempts = {}

setup_database()

# =========================================================
# معالجة النص والتصحيح
# =========================================================
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def check_answer(correct_text: str, student_text: str):
    correct_words = normalize_text(correct_text).split()
    student_words = normalize_text(student_text).split()
    matcher = difflib.SequenceMatcher(None, correct_words, student_words)
    correct_count = 0
    wrong_words = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            correct_count += i2 - i1
        elif tag == "replace":
            max_count = max(i2 - i1, j2 - j1)
            for index in range(max_count):
                correct_word = correct_words[i1 + index] if i1 + index < i2 else "—"
                student_word = student_words[j1 + index] if j1 + index < j2 else "مفقودة"
                wrong_words.append((student_word, correct_word))
        elif tag == "delete":
            for word in correct_words[i1:i2]:
                wrong_words.append(("مفقودة", word))
        elif tag == "insert":
            for word in student_words[j1:j2]:
                wrong_words.append((word, "غير موجودة"))

    total_words = len(correct_words)
    score = round(correct_count / total_words * 100) if total_words else 0
    return score, correct_count, total_words, wrong_words

# =========================================================
# القوائم واللوحات
# =========================================================
def lessons_keyboard():
    keyboard = [
        [InlineKeyboardButton("📘 رسم التاء المفتوحة والتاء المربوطة", callback_data="lesson1")],
        [InlineKeyboardButton("📗 رسم همزة القطع", callback_data="lesson2")],
        [InlineKeyboardButton("📙 قطع إضافية", callback_data="lesson3")],
    ]
    return InlineKeyboardMarkup(keyboard)

def teacher_keyboard():
    keyboard = [
        [InlineKeyboardButton("✏️ إضافة اسم المعلمة", callback_data="teacher_yes")],
        [InlineKeyboardButton("🚫 لا أرغب بإضافة المعلمة", callback_data="teacher_no")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 الطلاب", callback_data="admin_users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("🔎 البحث عن طالب", callback_data="admin_search")],
        [InlineKeyboardButton("📝 الأخطاء الشائعة", callback_data="admin_mistakes")],
    ]
    return InlineKeyboardMarkup(keyboard)

# =========================================================
# أوامر البلاغ والتسجيل
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_exists(user_id):
        await update.message.reply_text("📚 أهلاً بعودتك!\n\nاختر الدرس:", reply_markup=lessons_keyboard())
        return

    context.user_data["registration"] = "name"
    await update.message.reply_text(
        "👋 أهلاً بك في مذكرة الإملاء!\n\nقبل أن نبدأ، اكتب اسمك الثلاثي ✍️"
    )

async def teacher_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "teacher_no":
        name = context.user_data.get("student_name", "غير معروف")
        save_user(user_id, name, "لم يرغب بالإضافة")
        context.user_data.clear()
        await query.message.edit_text(
            f"✅ تم تسجيل بياناتك.\n\n👤 الاسم: {name}\n👩‍🏫 المعلمة: لم يرغب بالإضافة\n\n📚 اختر الدرس:",
            reply_markup=lessons_keyboard(),
        )
    elif query.data == "teacher_yes":
        context.user_data["registration"] = "teacher_name"
        await query.message.edit_text("✏️ اكتب اسم المعلمة:")

async def show_pieces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson = LESSONS.get(query.data)
    if not lesson:
        return

    keyboard = []
    for piece_id, piece in lesson["pieces"].items():
        keyboard.append([InlineKeyboardButton(f"📝 {piece['name']}", callback_data=piece_id)])
    keyboard.append([InlineKeyboardButton("🔙 رجوع للدروس", callback_data="back")])

    await query.message.edit_text(
        f"📚 {lesson['name']}\n\nاختر قطعة الإملاء:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def choose_piece(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    piece_id = query.data

    piece = None
    for lesson in LESSONS.values():
        if piece_id in lesson["pieces"]:
            piece = lesson["pieces"][piece_id]
            break

    if not piece:
        return

    user_id = query.from_user.id
    user_attempts[user_id] = {
        "piece_id": piece_id,
        "started_at": datetime.now(),
        "waiting": True,
    }

    await query.message.edit_text(
        f"📝 {piece['name']}\n\n"
        "🎧 استمع للتسجيل الصوتي جيدًا.\n\n"
        "✍️ بعد انتهاء التسجيل، اكتب ما سمعته وأرسله كنص أو صورة كتابتك."
    )

    audio_path = piece["audio"]
    if os.path.exists(audio_path):
        with open(audio_path, "rb") as audio:
            await query.message.reply_audio(audio=audio, caption=f"🎧 {piece['name']}")
    else:
        await query.message.reply_text(f"❌ لم أجد الملف الصوتي: {audio_path}")

async def back_to_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("📚 اختر الدرس:", reply_markup=lessons_keyboard())

# =========================================================
# استقبال النص واستخراج الصور وتصحيح الإجابات
# =========================================================
async def process_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, student_text: str):
    user_id = update.effective_user.id
    attempt = user_attempts.get(user_id)

    if not attempt or not attempt.get("waiting"):
        await update.message.reply_text("📚 اختر قطعة إملاء أولًا من /start")
        return

    # آلية الانتظار (60 ثانية بدون ظهور مؤقت عد تنازلي للمستخدم)
    elapsed = (datetime.now() - attempt["started_at"]).total_seconds()
    if elapsed < 60:
        await update.message.reply_text("⚠️ يرجى التمهل والتركيز في الكتابة والإجابة بشكل كامل قبل الإرسال.")
        return

    piece_id = attempt["piece_id"]
    piece = None
    for lesson in LESSONS.values():
        if piece_id in lesson["pieces"]:
            piece = lesson["pieces"][piece_id]
            break

    if not piece:
        return

    score, correct_count, total_words, wrong_words = check_answer(piece["text"], student_text)
    save_attempt(user_id, piece_id, score, len(wrong_words))

    for wrong, correct in wrong_words:
        save_mistake(user_id, wrong, correct)

    result = (
        f"🎯 نتيجة الإملاء\n\n"
        f"📖 القطعة: {piece['name']}\n\n"
        f"⭐ الدرجة: {score}/100\n"
        f"✅ الكلمات الصحيحة: {correct_count}/{total_words}\n"
        f"❌ عدد الأخطاء: {len(wrong_words)}\n"
    )

    if wrong_words:
        result += "\n📝 التصحيح:\n\n"
        for wrong, correct in wrong_words[:30]:
            result += f"❌ {wrong} → ✅ {correct}\n"
    else:
        result += "\n🎉 ممتاز جدًا! لم أجد أي أخطاء."

    keyboard = [
        [InlineKeyboardButton("🔄 إعادة القطعة", callback_data=piece_id)],
        [InlineKeyboardButton("📚 قطعة أخرى", callback_data="back")],
    ]
    await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard))
    user_attempts.pop(user_id, None)

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # التعامل مع مراحل التسجيل الأولية
    if not user_exists(user_id):
        registration = context.user_data.get("registration")
        if registration == "name":
            name = update.message.text.strip()
            if len(name) < 2:
                await update.message.reply_text("⚠️ اكتب اسمًا صحيحًا من فضلك.")
                return
            context.user_data["student_name"] = name
            context.user_data["registration"] = "teacher"
            await update.message.reply_text("👩‍🏫 ما اسم معلمتك؟", reply_markup=teacher_keyboard())
            return
        elif registration == "teacher_name":
            name = context.user_data.get("student_name", "غير معروف")
            teacher = update.message.text.strip()
            save_user(user_id, name, teacher)
            context.user_data.clear()
            await update.message.reply_text(
                f"✅ تم تسجيل بياناتك!\n\n👤 الاسم: {name}\n👩‍🏫 المعلمة: {teacher}\n\n📚 اختر الدرس:",
                reply_markup=lessons_keyboard(),
            )
            return

    # التعامل مع حالة البحث في لوحة الإدارة
    if context.user_data.get("admin_state") == "search":
        search_query = update.message.text.strip()
        users = get_users()
        matched = [u for u in users if search_query.lower() in u[1].lower()]
        context.user_data.pop("admin_state", None)

        if not matched:
            text = f"❌ لم يتم العثور على طالب باسم '{search_query}'."
        else:
            text = f"🔎 نتائج البحث عن '{search_query}':\n\n"
            for u_id, name, teacher in matched:
                text += f"👤 {name}\n👩‍🏫 المعلمة: {teacher}\n🆔 {u_id}\n\n"

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_back")]]),
        )
        return

    # معالجة نص الإملاء للطلاب
    await process_submission(update, context, update.message.text)

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_exists(user_id):
        await update.message.reply_text("⚠️ يرجى إكمال التسجيل أولاً عبر إرسال /start.")
        return

    await update.message.reply_text("📷 جاري قراءة ورقة الإجابة وتصحيحها...")
    # هنا يتم استخراج النص المستخرج من الصورة عبر مكتبة OCR
    extracted_text = "النص المستخرج من الصورة"
    await process_submission(update, context, extracted_text)

# =========================================================
# لوحة الإدارة والإحصائيات
# =========================================================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمشرف فقط.")
        return

    count = get_user_count()
    await update.message.reply_text(
        f"👨‍🏫 لوحة الإدارة\n\n👥 عدد الطلاب المسجلين: {count}\n\nاختر العملية:",
        reply_markup=admin_keyboard(),
    )

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    users = get_users()
    if not users:
        text = "📋 لا يوجد طلاب مسجلون."
    else:
        text = "📋 الطلاب المسجلون:\n\n"
        for index, (user_id, name, teacher) in enumerate(users[:50], start=1):
            text += f"{index}. 👤 {name}\n   👩‍🏫 المعلمة: {teacher}\n   🆔 {user_id}\n\n"

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_back")]]),
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    users = get_users()
    total_attempts = 0
    scores = []
    for user_id, name, teacher in users:
        attempts, highest, average = get_statistics(user_id)
        total_attempts += attempts
        if attempts:
            scores.append(average)

    average_all = round(sum(scores) / len(scores)) if scores else 0

    await query.message.edit_text(
        f"📊 إحصائيات البوت\n\n👥 عدد الطلاب: {len(users)}\n📝 إجمالي المحاولات: {total_attempts}\n⭐ متوسط الدرجات العامة: {average_all}/100",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_back")]]),
    )

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    context.user_data["admin_state"] = "search"
    await query.message.edit_text("🔎 اكتب اسم الطالب أو جزءاً منه للبحث عنه:")

async def admin_mistakes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    mistakes = get_common_mistakes()
    if not mistakes:
        text = "📝 لا توجد أخطاء شائعة مسجلة بعد."
    else:
        text = "📝 أكثر الأخطاء الإملائية تكراراً:\n\n"
        for wrong, correct, count in mistakes[:15]:
            text += f"❌ {wrong} → ✅ {correct} (تكررت {count} مرة)\n"

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_back")]]),
    )

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    context.user_data.pop("admin_state", None)
    count = get_user_count()
    await query.message.edit_text(
        f"👨‍🏫 لوحة الإدارة\n\n👥 عدد الطلاب: {count}\n\nاختر العملية:",
        reply_markup=admin_keyboard(),
    )

# =========================================================
# تشغيل التطبيق
# =========================================================
def main():
    app = Application.builder().token(TOKEN).build()

    # معالجة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    # معالجة استدعاءات الأزرار (Callback Queries)
    app.add_handler(CallbackQueryHandler(show_pieces, pattern=r"^lesson[1-3]$"))
    app.add_handler(CallbackQueryHandler(back_to_lessons, pattern=r"^back$"))
    app.add_handler(CallbackQueryHandler(choose_piece, pattern=r"^piece[1-5]$"))
    app.add_handler(CallbackQueryHandler(teacher_choice, pattern=r"^teacher_(yes|no)$"))
    app.add_handler(CallbackQueryHandler(admin_users, pattern=r"^admin_users$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern=r"^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_search, pattern=r"^admin_search$"))
    app.add_handler(CallbackQueryHandler(admin_mistakes, pattern=r"^admin_mistakes$"))
    app.add_handler(CallbackQueryHandler(admin_back, pattern=r"^admin_back$"))

    # معالجة الرسائل النصية والصور
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    app.add_handler(MessageHandler(filters.PHOTO, receive_photo))

    print("🤖 مذكرة الإملاء تعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()