"""Упражнения: лексика C1, тема Environment.

Часть 1 (mc) — выбрать слово в пропуск. Первый вариант в options — правильный,
на экране варианты перемешиваются.

Часть 2 (tr) — перевести выделенное слово (**word**) на русский.
accept — начала слов (основы): ответ засчитывается, если любое слово ответа
начинается с одной из основ. Так проходят разные формы: «сократилось», «сокращается».
"""

MULTIPLE_CHOICE = [
    {
        "sentence": "The government has pledged to ___ greenhouse gas emissions by half within the next decade.",
        "options": ["curb", "restrain", "withhold", "suppress"],
        "translation": "ограничивать, сдерживать",
        "definition": "to control or limit something harmful",
        "note": "curb emissions / curb pollution — устойчивое сочетание.",
    },
    {
        "sentence": "Rising sea levels threaten low-lying coastal areas, and experts warn the damage may soon become ___.",
        "options": ["irreversible", "unrecoverable", "incurable", "unreturnable"],
        "translation": "необратимый",
        "definition": "impossible to change back to a previous state",
        "note": "irreversible damage / change — необратимый ущерб / необратимые изменения.",
    },
    {
        "sentence": "Excessive use of fertilisers leads to agricultural ___, which contaminates nearby rivers and lakes.",
        "options": ["run-off", "outflow", "overflow", "spillage"],
        "translation": "сток (смыв удобрений с полей)",
        "definition": "rain water carrying chemicals from fields into rivers",
        "note": "run-off — вода с химикатами, стекающая с полей в водоёмы.",
    },
    {
        "sentence": "Urban sprawl continues to ___ on farmland and wildlife habitats.",
        "options": ["encroach", "impose", "infringe", "interfere"],
        "translation": "вторгаться, посягать",
        "definition": "to gradually take over land that belongs to someone or something else",
        "note": "encroach on/upon — постепенно захватывать чужую территорию.",
    },
    {
        "sentence": "The brand was accused of ___ after exaggerating how eco-friendly its packaging really was.",
        "options": ["greenwashing", "whitewashing", "green-lighting", "eco-branding"],
        "translation": "гринвошинг, «зелёный камуфляж»",
        "definition": "making a company look more eco-friendly than it really is",
        "note": "greenwashing — вводящие в заблуждение заявления об экологичности.",
    },
    {
        "sentence": "Conservationists argue that ___ is the main driver of species loss in the Amazon basin.",
        "options": ["deforestation", "defoliation", "deformation", "desertion"],
        "translation": "вырубка лесов",
        "definition": "the cutting down of forests on a large scale",
        "note": "defoliation — опадание листвы, deformation — искажение формы.",
    },
    {
        "sentence": "Frequent long-haul flights can double an individual's carbon ___.",
        "options": ["footprint", "trace", "imprint", "trail"],
        "translation": "углеродный след",
        "definition": "the total amount of CO₂ produced by a person or activity",
        "note": "carbon footprint — объём выбросов CO₂ от деятельности человека.",
    },
    {
        "sentence": "Scientists fear that thawing ___ in Siberia will release vast quantities of methane.",
        "options": ["permafrost", "iceberg", "snowdrift", "ice floe"],
        "translation": "вечная мерзлота",
        "definition": "ground that stays permanently frozen",
        "note": "thawing permafrost — оттаивающая вечная мерзлота.",
    },
    {
        "sentence": "The new regulations are designed to ___ the impact of industrial pollution on local communities.",
        "options": ["mitigate", "militate", "meditate", "migrate"],
        "translation": "смягчать, уменьшать (вред)",
        "definition": "to make something less harmful or severe",
        "note": "Не путайте с militate against — препятствовать чему-либо.",
    },
    {
        "sentence": "Decades of overfishing have ___ cod stocks in the North Atlantic to dangerously low levels.",
        "options": ["depleted", "deployed", "deprived", "deflected"],
        "translation": "истощать, исчерпывать",
        "definition": "reduced so much that little is left",
        "note": "deplete stocks / resources — истощать запасы.",
    },
    {
        "sentence": "The heatwave was further ___ by the lack of green spaces in the city centre.",
        "options": ["exacerbated", "exaggerated", "exasperated", "exonerated"],
        "translation": "усугублять, обострять",
        "definition": "made a bad situation even worse",
        "note": "exaggerate — преувеличивать, exasperate — выводить из себя.",
    },
    {
        "sentence": "Packaging made from ___ materials breaks down naturally without harming the soil.",
        "options": ["biodegradable", "disposable", "perishable", "combustible"],
        "translation": "биоразлагаемый",
        "definition": "able to decay naturally without harming the environment",
        "note": "disposable — одноразовый, perishable — скоропортящийся.",
    },
    {
        "sentence": "The rhino population has been decimated by ___, driven by demand for its horn.",
        "options": ["poaching", "pouching", "culling", "grazing"],
        "translation": "браконьерство",
        "definition": "illegal hunting or catching of animals",
        "note": "culling — плановый отстрел для регулирования численности.",
    },
    {
        "sentence": "Some airlines let passengers pay extra to ___ the emissions from their flight by funding tree planting.",
        "options": ["offset", "outweigh", "offload", "outset"],
        "translation": "компенсировать",
        "definition": "to balance one effect by doing something with the opposite effect",
        "note": "offset emissions — компенсировать выбросы.",
    },
    {
        "sentence": "Coral reefs are among the most ___ ecosystems on the planet, sensitive to even slight rises in water temperature.",
        "options": ["fragile", "frail", "brittle", "feeble"],
        "translation": "хрупкий, уязвимый",
        "definition": "easily damaged or destroyed",
        "note": "fragile ecosystem — сочетание; frail обычно о пожилых людях.",
    },
    {
        "sentence": "Water ___ in the region has become so severe that rationing has been introduced.",
        "options": ["scarcity", "scarceness", "shortness", "rarity"],
        "translation": "нехватка, дефицит",
        "definition": "a situation in which there is not enough of something",
        "note": "water / resource scarcity — дефицит воды / ресурсов.",
    },
    {
        "sentence": "Many biologists believe we are witnessing the sixth mass ___ in Earth's history.",
        "options": ["extinction", "extermination", "expiry", "extinguishing"],
        "translation": "вымирание",
        "definition": "the situation in which a species no longer exists",
        "note": "mass extinction — массовое вымирание видов.",
    },
    {
        "sentence": "The island's ___ beaches attract thousands of eco-tourists every year.",
        "options": ["pristine", "primitive", "prestigious", "primal"],
        "translation": "нетронутый, первозданный",
        "definition": "in its original condition, untouched by people",
        "note": "pristine — в первозданном состоянии, не испорченный человеком.",
    },
    {
        "sentence": "Toxic waste from the factory was found to have ___ the town's groundwater.",
        "options": ["contaminated", "consecrated", "congregated", "concentrated"],
        "translation": "загрязнять, заражать",
        "definition": "made dirty or poisonous by adding a harmful substance",
        "note": "contaminate water / soil — загрязнять воду / почву.",
    },
    {
        "sentence": "Peatlands play a vital role in carbon ___, storing more CO₂ than all the world's forests combined.",
        "options": ["sequestration", "sedimentation", "segregation", "secretion"],
        "translation": "улавливание и хранение (углерода)",
        "definition": "the process of capturing and storing carbon",
        "note": "carbon sequestration — поглощение и связывание CO₂.",
    },
]

TRANSLATION = [
    {
        "sentence": "The Arctic is warming at an **unprecedented** rate.",
        "translation": "беспрецедентный, небывалый",
        "accept": ["беспрецедент", "небывал", "невиданн", "неслыхан", "рекордн"],
        "hint": "never having happened or existed before",
    },
    {
        "sentence": "We need to switch to more **sustainable** forms of agriculture.",
        "translation": "устойчивый, экологически рациональный",
        "accept": ["устойчив", "экологичн", "рациональн", "неистощ", "щадящ", "бережн"],
        "hint": "able to continue without harming the environment",
    },
    {
        "sentence": "Ozone **depletion** allows more harmful UV radiation to reach the Earth's surface.",
        "translation": "истощение, разрушение",
        "accept": ["истощ", "разруш", "уменьшен", "сокращен", "исчерпан", "убыван"],
        "hint": "the reduction of something until little is left",
    },
    {
        "sentence": "Fresh water is becoming increasingly **scarce** in parts of Africa.",
        "translation": "дефицитный, скудный",
        "accept": ["дефицит", "скуд", "редк", "недостат", "нехват", "малодоступ"],
        "hint": "not available in large enough amounts",
    },
    {
        "sentence": "Some invasive species **thrive** in warmer climates, outcompeting native plants.",
        "translation": "процветать, бурно расти",
        "accept": ["процвет", "бурно", "преусп", "разраст", "благоденств", "расти", "растут", "размнож", "распростран"],
        "hint": "to grow, develop or be successful",
    },
    {
        "sentence": "The number of wild tigers has **dwindled** to just a few thousand.",
        "translation": "сокращаться, уменьшаться",
        "accept": ["сократ", "сокращ", "уменьш", "убыв", "убыл", "таять", "тает", "растаял", "снизил", "снижа", "упал", "падат"],
        "hint": "to gradually become smaller in number",
    },
    {
        "sentence": "The plant was fined for dumping **hazardous** waste into the river.",
        "translation": "опасный",
        "accept": ["опасн", "вредн", "токсичн"],
        "hint": "dangerous, especially to health or safety",
    },
    {
        "sentence": "Most of the plastic we throw away ends up in **landfill**.",
        "translation": "свалка, мусорный полигон",
        "accept": ["свалк", "полигон", "мусорн"],
        "hint": "a place where waste is buried under the ground",
    },
    {
        "sentence": "Without tree roots to hold it in place, the soil is vulnerable to **erosion**.",
        "translation": "эрозия, размывание",
        "accept": ["эрози", "размыв", "выветр", "вымыв", "разрушен"],
        "hint": "the gradual wearing away of soil or rock by wind or water",
    },
    {
        "sentence": "The destruction of their natural **habitat** has pushed many species to the brink of extinction.",
        "translation": "среда обитания, ареал",
        "accept": ["обитан", "ареал", "жилищ", "дом"],
        "hint": "the natural home of a plant or animal",
    },
    {
        "sentence": "It can take centuries for underground aquifers to **replenish** themselves.",
        "translation": "пополняться, восполняться",
        "accept": ["пополн", "восполн", "восстанов", "возобнов", "наполн"],
        "hint": "to fill something up again",
    },
    {
        "sentence": "Microplastics may have a **detrimental** effect on human health.",
        "translation": "пагубный, вредный",
        "accept": ["пагубн", "вредн", "губительн", "разрушительн", "негативн", "отрицательн", "неблагоприятн", "плох"],
        "hint": "causing harm or damage",
    },
    {
        "sentence": "The snow leopard is listed as an **endangered** species.",
        "translation": "вымирающий, находящийся под угрозой исчезновения",
        "accept": ["вымира", "исчеза", "угроз", "угрожаем", "краснокниж"],
        "hint": "at risk of no longer existing",
    },
    {
        "sentence": "Countries are investing billions to **harness** the power of the wind and the sun.",
        "translation": "использовать, обуздать (силы природы)",
        "accept": ["использ", "обузд", "задейств", "освои", "осваива", "применя", "примени", "запряч", "запряг", "покор", "приручи"],
        "hint": "to control and use a natural force to produce energy",
    },
    {
        "sentence": "Many cafés have stopped selling drinks in **disposable** cups.",
        "translation": "одноразовый",
        "accept": ["одноразов"],
        "hint": "intended to be thrown away after one use",
    },
]


def _build():
    items = {}
    for n, q in enumerate(MULTIPLE_CHOICE, 1):
        items[f"mc{n:02d}"] = {**q, "id": f"mc{n:02d}", "type": "mc", "answer": q["options"][0], "word": q["options"][0]}
    for n, q in enumerate(TRANSLATION, 1):
        word = q["sentence"].split("**")[1]
        items[f"tr{n:02d}"] = {**q, "id": f"tr{n:02d}", "type": "tr", "word": word, "answer": q["translation"],
                               "definition": q["hint"]}
    return items


ITEMS = _build()
