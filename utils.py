import datetime

def build_description(profile):
    """Возвращает форматированное описание профиля"""
    ico = profile['ico']
    name = profile['name']
    cafedras = profile['cafedras']
    zav_caf = profile['zav_caf']
    description = profile['description']
    date_reg = profile['date_reg']
    date_olimp = profile['date_olimp']
    time_olimp = profile['time_olimp']
    place = profile['place']

    text = f"{ico} *{name}*\n\n"

    if cafedras:
        if len(cafedras) == 1:
            cafedra_text = f"🎓 *Кафедра-организатор:*\n{cafedras[0]}\n"
        else:
            cafedra_text = "🎓 *Кафедры-организаторы:*\n"
            for c in cafedras:
                cafedra_text += f"- {c}\n"
        text += cafedra_text + "\n"
    
    if zav_caf:
        text += f"👨‍🎓 *Заведующий кафедрой:* {zav_caf}\n\n"

    if description == '':
        text += '🕐 Это новый профиль.\nПодробности про него появятся позднее'
    else:
        text += f"📝 *Описание профиля:*\n{description}\n\n"
        text += "✏️ Олимпиада проводится в *очном формате* в МГТУ \"СТАНКИН\"\n\n"

    if date_reg or date_olimp:
        text += f"🗓️ *ОСНОВНЫЕ ДАТЫ*\n"
        if date_reg: 
            text += f"*Регистрация:* {date_reg}\n"
        if date_olimp: 
            text += f"*Проведение олимпиады:* {date_olimp}"
            if time_olimp:
                text += f" в {time_olimp}"
            text += "\n"
        text += "\n"
    
    if place:
        text += f"📍 *Место проведения:* {place}"
    
    return text


def find_group_by_id(data, gid):
    for g in data["groups"]:
        if g["id"] == gid:
            return g
    return None


def find_profile_by_id(data, pid):
    for g in data["groups"]:
        for p in g.get("profiles", []):
            if p["id"] == pid:
                return p, g
    return None, None


def get_top5_profiles(data):
    """Возвращает топ-5 профилей по дате проведения"""
    all_profiles = []
    for group in data["groups"]:
        for p in group.get("profiles", []):
            if p.get("date_olimp", "") != "":
                all_profiles.append(p) # (p, group)
    
    # функция извлечения даты для сортировки
    def extract_date(profile):
        date_str = profile["date_olimp"]
        day, month, year = map(int, date_str.split("."))

        #проверка, если дата уже прошла, то не учитывать её
        date = datetime.date(year, month, day)
        if date < datetime.date.today():
            return (9999, 12, 31)
        return (year, month, day)
    
    all_profiles.sort(key=extract_date)
    top5_profiles = all_profiles[:5]
    return top5_profiles
