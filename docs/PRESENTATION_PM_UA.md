# Fooocus Pro — презентація для продактів

**Формат:** Google Slides · копіюй блок «Слайд N» на окремий слайд  
**Мова:** українська, без технічного жаргону  
**Актуально:** один Colab-ноутбук · preset Juggernaut Ragnarok

**Colab:** https://colab.research.google.com/github/sunsideaspect/foocus_new/blob/main/fooocus_colab.ipynb

---

## Слайд 1 — Титул

**Fooocus Pro**  
Генератор реалістичних фото в браузері

- Пишеш **опис сцени** → отримуєш **зображення**
- Працює через **Google Colab** (GPU в хмарі, нічого не встановлюєш)
- Налаштовано під **фотореалізм** і стабільну роботу на безкоштовному GPU

---

## Слайд 2 — Що таке Fooocus (якщо ніхто не чув)

**Fooocus** — це програма «**текст → картинка**».

Ти описуєш, що хочеш бачити (англійською), натискаєш **Generate** — через кілька хвилин з’являється PNG.

**На відміну від ChatGPT-картинок:**
- більше **ручного контролю** (розмір, стилі, дорисовка, upscale)
- можна **підтягнути обличчя** з референс-фото
- можна **переробити** частину картинки (inpaint)
- наш Colab-запуск — **без автоматичного blur** на контенті

**Fooocus Pro** — це не окремий сайт, а **готовий Colab + налаштований інтерфейс Fooocus** під реалістичні фото.

---

## Слайд 3 — Як потрапити в інтерфейс

1. Відкрий Colab-ноутбук (лінк вище)
2. **Runtime → Change runtime type → GPU (T4)**
3. **Runtime → Restart session**
4. **Runtime → Run all**
5. Дочекайся лінку **Open Fooocus (Colab proxy)** → відкрий у новій вкладці

**Перший запуск:** 10–15 хв (завантаження моделей)  
**Наступні генерації:** 2–5 хв

---

## Слайд 4 — Головний екран (layout)

```
┌─────────────────────────────────┬──────────────────────┐
│  Галерея (результати)           │  Settings / Styles / │
│                                 │  Models / Advanced   │
│  Prompt (опис сцени)            │  (права колонка)     │
│  [ Generate ]                   │                      │
│  ☐ Input Image  ☐ Enhance       │                      │
│  ☐ Advanced                     │                      │
└─────────────────────────────────┴──────────────────────┘
```

**Ліва частина** — промпт, кнопки, галерея.  
**Права частина** — з’являється, коли увімкнено **Advanced** (у нас у Colab увімкнено за замовчуванням через preset).

---

## Слайд 5 — Головні кнопки (завжди внизу під промптом)

| Кнопка | Коли видна | Що робить |
|--------|------------|-----------|
| **Generate** | Завжди | Запускає генерацію. Бере текст з Prompt + налаштування справа. |
| **Stop** | Під час генерації | Зупиняє поточну генерацію. |
| **Skip** | Під час багатокрокових задач | Пропускає поточний крок (наприклад, один enhance-прохід). |
| **Reconnect** | Якщо з’єднання обірвалось | Перепідключення до сервера Gradio. |
| **Load Parameters** | Рідко | Підвантажує параметри з буфера / metadata. |

**Галерея (Gallery):** показує готові картинки. Клік — перегляд; можна завантажити PNG.

**Preview / Progress:** під час генерації — попередній перегляд і прогрес-бар.

---

## Слайд 6 — Три перемикачі над Input Image

| Галочка | Що відкриває | Навіщо |
|---------|--------------|--------|
| **Input Image** | Панель з вкладками для роботи **з готовим зображенням** | Upscale, референс, inpaint, describe |
| **Enhance** | Панель **авто-покращення** після (або замість) генерації | Дорисовка обличчя, рук, деталей по маці |
| **Advanced** | Права колонка **Settings / Styles / Models / Advanced** | Розмір, стилі, моделі, тонкі параметри |

**Порада для новачка:** перший тест — **Input Image OFF**, **Enhance OFF**, **Advanced ON**.

---

## Слайд 7 — Settings (вкладка в правій колонці)

| Елемент | Що робить | Що дає |
|---------|-----------|--------|
| **Performance** | Швидкість vs якість | **Quality** (~60 кроків) — детальніше; **Speed** (~30) — швидше; Extreme/Lightning — дуже швидко, гірша якість |
| **Aspect Ratios** | Пропорції кадру | Portrait 768×1344 — вертикальне фото; 1024×1024 — квадрат; інші — під full body / landscape |
| **Image Number** | Скільки варіантів за один Generate | 1 — швидко; 4 — вибрати найкращий кадр |
| **Output Format** | png / jpeg / webp | PNG — без втрат, для подальшого Enhance |
| **Negative Prompt** | Чого **не** хочеш на картинці | cartoon, blur, watermark, bad anatomy… (у Colab уже заповнено preset-ом) |
| **Random** (seed) | Випадковий seed | Увімкнено = кожна генерація нова; вимкни + число = **повторюваний** результат |
| **Seed** | Число «рецепту» генерації | Той самий seed + той самий промпт ≈ та сама картинка |
| **History Log** | Посилання на локальний лог | Список згенерованих файлів (якщо увімкнено збереження) |

**У нашому Colab preset:** Performance = **Quality**, Aspect = **768×1344**, Image Number = **1**.

---

## Слайд 8 — Styles (вкладка)

| Елемент | Що робить | Що дає |
|---------|-----------|--------|
| **Пошук стилів** | Фільтр списку | Швидко знайти «Semi Realistic», «Spontaneous» тощо |
| **CheckboxGroup стилів** | Готові **пресети вигляду** | Додають до промпту слова про освітлення, камеру, mood |

**Стилі = «фільтри камери»**, не замінюють промпт.

**Для селфі (див. кінець):** `MRE Spontaneous Picture` + `Semi Realistic`.  
**Не змішуй** `Photo Iphone` з сильними cinematic-стилями — портретний blur зламається.

---

## Слайд 9 — Models (вкладка)

| Елемент | Що робить | Що дає |
|---------|-----------|--------|
| **Base Model** | Основна «нейромережа» для малювання | У Colab: **Juggernaut XL Ragnarok** — фотореалізм |
| **Refiner** | Другий прохід для деталей | Якщо **None** — один прохід (рекомендовано). Якщо та сама модель — refiner ігнорується |
| **Refiner Switch At** | На якому % кроків увімкнути refiner | Лише якщо refiner ≠ None |
| **LoRA 1–5** | Додаткові «надбудови» до моделі | У preset: anatomy, add detail (увімкнені); film style (вимкнений) |
| **Enable** (біля LoRA) | Увімк/вимк конкретну LoRA | Вимк anatomy — м’якше тіло; менше «надмірної» анатомії |
| **Weight** (LoRA) | Сила LoRA | Вище = сильніший ефект LoRA |
| **🔄 Refresh All Files** | Оновити списки файлів | Після ручного додавання моделей у папку |

**Користувачу в Colab зазвичай достатньо preset — Models не чіпати**, якщо не експериментуєш.

---

## Слайд 10 — Advanced (вкладка, основне)

| Елемент | Що робить | Що дає |
|---------|-----------|--------|
| **Guidance Scale (CFG)** | Наскільки модель «слухається» промпту | 3.5–4.5 — реалізм; вище — різкіше, «артовiше» |
| **Image Sharpness** | Різкість текстур | Вище — чіткіші деталі; занадто — «перешарп» |
| **Developer Debug Mode** | Відкриває **Debug Tools** | Доступ до кроків sampling, sampler, scheduler |

**У preset Colab:** CFG ≈ **4.2**, Sharpness ≈ **1.1**.

---

## Слайд 11 — Debug Tools (Advanced → увімкни Developer Debug Mode)

| Елемент | Що робить | Коли потрібно |
|---------|-----------|---------------|
| **Forced Overwrite of Sampling Step** | Фіксована кількість кроків | **48** у preset; для селфі спробуй **40–44**; **-1** = брати з Performance |
| **Sampler** | Алгоритм генерації | За замовчуванням **dpmpp_2m_sde_gpu** — не міняти без причини |
| **Scheduler** | Розклад кроків | **karras** — стандарт для якості |
| **Save Metadata to Images** | Зберігає параметри в PNG | Щоб потім **Metadata → Apply** і повторити кадр |
| **Black Out NSFW** | Замінює картинку на чорну | У нашому Colab **вимкнено** (censor off) |

Решта (ADM, VAE, overwrite width…) — для досвідчених; PM-аудиторії достатньо знати про **Sampling Step**.

---

## Слайд 12 — Input Image → Upscale or Variation

Увімкни **Input Image**, вкладка **Upscale or Variation**.

| Елемент | Що робить | Що дає |
|---------|-----------|--------|
| **Image** | Завантаж своє або згенероване фото | База для зміни |
| **Upscale or Variation** | Режим | **Disabled** — не використовувати цю вкладку; **Vary Subtle/Strong** — варіація схожого кадру; **Upscale 1.5x / 2x** — збільшення з дорисовкою деталей |

**Коли використовувати:** є хороший кадр, треба **більший розмір** або **легка варіація** без нового промпту.

---

## Слайд 13 — Input Image → Image Prompt

До **4 слотів** з референс-фото.

| Type | Що робить | Коли |
|------|-----------|------|
| **ImagePrompt** | Загальний стиль / композиція з референсу | «Зроби схоже на це фото» |
| **FaceSwap** | **Обличчя** з референсу на згенерованому тілі | Референс = фото обличчя; Weight ~1.2–1.4, Stop ~0.98 |
| **PyraCanny** | Контур / структура | Утримати позу / силует |
| **CPDS** | М’якший structure control | Альтернатива Canny |

| Параметр | Що означає |
|----------|------------|
| **Stop At** | До якого % генерації діє референс |
| **Weight** | Сила впливу референсу |
| **Advanced** | Показує Type / Stop / Weight для кожного слоту |

**FaceSwap:** завантаж фото людини → Generate з промптом тіла → обличчя ближче до референсу.

---

## Слайд 14 — Input Image → Inpaint or Outpaint

| Елемент | Що робить |
|---------|-----------|
| **Image + brush** | Малюєш **білу маску** — що перегенерувати |
| **Method** | Inpaint / Outpaint / Improve Detail / Modify Content |
| **Outpaint Direction** | Розширити кадр (Left/Right/Top/Bottom) |
| **Inpaint Additional Prompt** | Опис **лише для замаскованої зони** |
| **Generate mask from image** | Авто-маска (SAM, u2net…) |

**Improve Detail (face, hand…):** маска на обличчя → дорисовка деталей.  
**Modify Content:** змінити одяг, фон, об’єкт у зоні маски.

---

## Слайд 15 — Input Image → Describe

| Елемент | Що робить |
|---------|-----------|
| **Image** | Завантаж фото |
| **Content Type** | Photograph / Art·Anime |
| **Apply Styles** | Чи додавати активні стилі до згенерованого промпту |
| **Describe this Image into Prompt** | AI **описує** картинку текстом → текст потрапляє в **Prompt** |

**Навіщо:** швидко зрозуміти, «якими словами» описати схожий кадр; навчання промптам.

---

## Слайд 16 — Input Image → Enhance (завантаження)

| Елемент | Що робить |
|---------|-----------|
| **Use with Enhance, skips image generation** | Завантаж готове PNG → **тільки Enhance**, без нової генерації |

Корисно, коли картинка вже є, треба лише **підтягнути обличчя** через Enhance-проходи.

---

## Слайд 17 — Input Image → Metadata

| Елемент | Що робить |
|---------|-----------|
| **For images created by Fooocus** | Завантаж PNG, згенерований Fooocus |
| **Metadata (JSON)** | Показує збережені параметри |
| **Apply Metadata** | **Відновлює** промпт, seed, налаштування в UI |

**Навіщо:** повторити вдалий кадр або трохи змінити seed.

---

## Слайд 18 — Enhance (галочка Enhance + панель)

**Enhance** = другий етап **після** основної генерації (або замість неї, див. слайд 16).

### Upscale or Variation (в Enhance)
| Опція | Що робить |
|-------|-----------|
| **Upscale / Vary** | Те саме, що в Input Image, але **в ланцюжку Enhance** |
| **Order of Processing** | Before First Enhancement / After Last Enhancement |
| **Prompt** | Який промпт використати для upscale |

### Вкладки #1, #2, #3… (enhance-проходи)
| Елемент | Що робить |
|---------|-----------|
| **Enable** | Увімкнути цей прохід |
| **Detection prompt** | Що знайти на фото: `face`, `hand`, `eyes`… (SAM) |
| **Enhancement positive/negative prompt** | Окремий промпт для зони (порожньо = глобальний) |
| **Mask generation model** | sam / u2net… — як будується маска |
| **Inpaint Engine** | v2.6 — алгоритм дорисовки Fooocus |
| **Inpaint Denoising Strength** | Наскільки сильно перемалювати зону |
| **Inpaint Respective Field** | Розмір області навколо маски |

**Типовий кейс:** Generate → Enhance ON → #1 Enable → detection `face` → дорисовка обличчя.

**Для першого селфі-тесту:** Enhance **OFF** (швидше і передбачуваніше).

---

## Слайд 19 — Типовий workflow (3 сценарії)

### A. Проста генерація
Advanced ON → Prompt → Generate → Download

### B. Краще обличчя
Generate → Enhance ON → #1 `face` → Generate знову (або inpaint на обличчя)

### C. Одне обличчя на різних тілах
Input Image ON → Image Prompt → FaceSwap + референс → Prompt про тіло/сцену → Generate

---

## Слайд 20 — Обмеження (чесно)

- Colab може **відключити сесію** — Restart + Run all
- **Селфі «як iPhone»** важче, ніж full body — потрібні стилі + промпт
- **Обличчя на full body** часто слабше — FaceSwap або Enhance face
- Промпти **англійською** працюють найкраще
- Перша генерація **довга** через завантаження моделей

---

## Слайд 21 — Позиціонування (для PM)

| | ChatGPT Images | **Fooocus Pro** |
|---|----------------|-----------------|
| Вхід | Легко | Colab + 15 хв перший раз |
| Контроль | Мало | Повний UI |
| Full body реалізм | Середньо | Сильний кейс |
| Ціна | Підписка | Colab free tier |

**Один продуктовий вхід:** один Colab-ноутбук, один preset, один інтерфейс Fooocus.

---

---

# Додаток — інструкція для тесту: детальний промпт

> Останній слайд презентації або окремий handout для QA / користувача.

**Структура промпту (чому він довгий):**
1. **Персонаж** — вік, риси обличчя, шкіра, волосся  
2. **Сцена** — де, коли, освітлення, фон  
3. **Поза / дія** — що робить, як стоїть, вираз  
4. **Камера** — smartphone, candid, unposed, pores, imperfections  

Чим конкретніше опис — тим менше «рандому» і вищий реалізм.

## Запуск (2 хв дій + очікування)

1. Colab → GPU → Restart → **Run all**
2. **Open Fooocus (Colab proxy)**

## Налаштування в UI (перевір перед Generate)

| Де | Значення |
|----|----------|
| **Input Image** | OFF |
| **Enhance** | OFF |
| **Advanced** | ON |
| **Performance** | Quality |
| **Aspect Ratios** | **768×1344** (portrait, full body) |
| **Image Number** | **2** (вибереш краще) |
| **Styles** | ✅ **MRE Spontaneous Picture** + ✅ **Semi Realistic** |
| **Models → Refiner** | **None** |
| **Advanced → Developer Debug Mode** | ON |
| **Forced Overwrite of Sampling Step** | **42** (діапазон 40–44) |

**Не вмикай зараз:** Photo Iphone + MRE Cinematic Dynamic разом.

## Prompt (скопіюй цілком)

```
32-year-old woman, striking pale eyes, straight messy hair with one distinct bleached-blonde streak framing her face, firm lips, sharp facial structure, realistic skin texture with visible pores, fine lines near eyes. Standing naked on the rooftop of a high-rise building at night, city lights blurred in the background, leaning over the metal railing, exposed skin, nipples erect, gritty urban environment, intense and defiant expression. Realistic smartphone photo, taken with a modern phone camera, casual everyday moment, unposed, candid lifestyle photo, natural lighting, realistic skin pores, tiny imperfections, authentic human appearance.
```

## Negative Prompt (скопіюй або доповни preset)

```
cartoon, anime, manga, cgi, 3d render, illustration, painting, drawing, plastic skin, waxy skin, airbrushed, beauty filter, overprocessed, oversaturated, studio lighting, professional photoshoot, glamour lighting, soft focus portrait blur, blurry, out of focus, lowres, jpeg artifacts, watermark, text, signature, logo, deformed face, deformed body, bad anatomy, extra limbs, extra fingers, missing fingers, fused fingers, cross-eyed, asymmetric eyes, unnatural pose, floating objects, duplicate person, mannequin, doll-like skin, uncanny valley
```

## Generate → оцінка

- [ ] **Обличчя** — риси з промпту читаються (очі, streak у волоссі, структура)
- [ ] **Тіло / поза** — відповідає сцені (дах, перила, full body)
- [ ] **Фон** — нічне місто, bokeh вогнів
- [ ] **Стиль камери** — схоже на phone candid, не на 3D-рендер
- [ ] **Шкіра** — pores / imperfections, не пластик
- [ ] Немає blur / blackout / watermark

## Якщо обличчя або деталі обличчя слабкі (крок 2)

1. Увімкни **Enhance**
2. Вкладка **#1** → Enable → Detection prompt: **`face`**
3. Inpaint Strength: **0.35–0.45**
4. Generate ще раз (той самий seed, якщо Random OFF)

## Якщо треба конкретне обличчя (крок 3)

1. **Input Image** ON → **Image Prompt**
2. Слот 1: фото обличчя → Type **FaceSwap** → Weight **1.3**, Stop **0.98**
3. Той самий детальний Prompt → Generate

## Звіт після тесту

1. Час до першого PNG: ___ хв  
2. Якість (1–5): ___  
3. Colab впав: так / ні  
4. Що не збіглось з промптом: ___  
5. Скрін + seed, якщо баг

---

## Speaker notes (коротко)

**«Це складно?»** — Перший раз так; далі Generate + 2–3 повзунки.  
**«Скільки коштує?»** — Colab free; Pro опційно.  
**«Чому Colab?»** — GPU без свого сервера.  
**«Що не чіпати?»** — Models / Debug, поки не освоїш базовий Prompt + Styles.
