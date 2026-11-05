---
name: create-mind-map
description: สร้าง "แผนที่การเรียนรู้" ของ keyword หรือหัวข้อ ที่เริ่มจาก overview แล้วเจาะลึกลงได้เรื่อยๆ render เป็น mind map แบบ interactive (root กลาง กิ่งแตกซ้ายขวา พับ/กางได้ ลาก/ซูมได้ คลิก node เปิดแผงเนื้อหา) เปิดใน browser ตรงๆ ไม่ใช้ Lavish ปุ่มในหน้าคัดลอกคำสั่งให้ user วางในแชท: ขยายลึก / ยกตัวอย่าง / ทำไม / เทียบกับ / ทดสอบตัวเอง หรือเลือกคำในเนื้อหาแล้วขยายเป็น node ใหม่ ทุกการขยายเป็น node ลูกใหม่ (append-only ไม่แก้ข้อความเดิม) และผูกกับงานจริงของ project ปัจจุบัน resume map เดิมได้ export ลง vault Alice ได้เมื่อสั่ง. Use when user says "/create-mind-map <keyword>", "/learnmap" (old name), "ทำ map การเรียนรู้", "learning map", "อยากเข้าใจ X แบบเจาะลึกได้", "แตก overview เรื่อง X", or pastes a "/create-mind-map <slug> <action> <node>" (or older "/learnmap ...") command copied from the page. Do NOT use for lesson decks with recall loop (use /teach), studying a repo/video (use /learn), or a one-off visual answer (use /visualize).
argument-hint: "<keyword> [--context <text>] | <slug> <action> <node> [\"arg\"] | --resume <slug> | --export <slug> | --list"
---

# /create-mind-map

แผนที่ความรู้ที่โตขึ้นได้: เริ่มจาก overview แล้ว user เป็นคนเลือกว่าจะเจาะกิ่งไหน เหมือนเวลาถาม keyword ในแชท แต่ทุกคำตอบไปต่อกันเป็น tree ที่เปิดกลับมาดูได้

ตอบเป็นภาษาไทย ศัพท์เทคนิคคงรูปเดิม

## หลักการ (ห้ามละเมิด)

1. **Overview ก่อนเสมอ**: map ใหม่ = root ที่มี body สั้นๆ + กิ่ง 5–8 กิ่งที่เป็น stub (มีแค่ title + summary บรรทัดเดียว)
2. **Append-only**: body ที่เขียนแล้วห้ามแก้ การขยาย = node ลูกใหม่ ถ้าเนื้อหาเดิมผิดให้เพิ่มลูก `kind=correction` ที่อธิบายว่าผิดตรงไหน `mapctl.py fill` จะปฏิเสธถ้า node มี body อยู่แล้ว **ห้ามเลี่ยงด้วยการแก้ map.json ตรงๆ**
3. **โยงกับงานจริง**: ถ้า project ปัจจุบันเกี่ยวข้อง ให้ใส่ `link_to_work` ที่อ้างของจริง (ชื่อตาราง ไฟล์ ตัวเลข decision) ถ้าไม่เกี่ยวก็ปล่อยว่าง ห้ามแต่งการเชื่อมโยงขึ้นมาเอง
4. **ความถูกต้อง**: `confidence=verified` ต้องมี `sources` เสมอ (script บังคับ) ข้อเท็จจริงเรื่อง product/ราคา/feature/เวอร์ชัน **ต้องค้น web ก่อนเขียน** ส่วนความรู้พื้นฐานที่นิ่งแล้วใช้ `from-memory` ได้
5. **Fact check ทุก node ที่มีข้อเท็จจริงตรวจสอบได้** (ดู section "Fact check") ห้ามบอก user ว่า node "เสร็จ" ถ้ายังไม่ผ่านขั้นนี้
6. **Vault ก่อน web**: ค้น MOC ใน `03 - Resources/` → grep vault Alice → web ถ้าเจอใน vault ให้ใส่ `{"type":"vault","ref":"Note Name"}` ใน sources

## ที่อยู่ของไฟล์

- Script: `~/.claude/skills/create-mind-map/scripts/mapctl.py`  (ด้านล่างเรียกว่า `$M`)
- Map: `<cwd>/.learnmap/<slug>/` มี `map.json` (source of truth) + `index.html` (render ใหม่จาก map.json ทุกครั้งที่แก้ และฝังข้อมูลไว้ในไฟล์ จึงเปิดแบบ `file://` ได้โดยไม่ต้องมี server)
- หน้าเว็บ: mind map (d3) + แผงเนื้อหาด้านขวา (เลือกข้อความ → ไฮไลต์ · ปุ่ม "อ่านแล้ว" / กด m) + แผง "โน้ต" แยกทางซ้ายของหน้าหลัก รวมไฮไลต์ทุกอันพร้อมป้ายที่มา (สีกิ่ง ชื่อกล่อง เส้นทาง) เขียนโน้ตได้ ส่งออก markdown ได้ · บนผังมีวงกลมเหลืองนับไฮไลต์ต่อกล่อง · เก็บใน localStorage + ช่องค้นหา (กด `/` ค้นจาก title/summary/body เรียงตามคะแนน Enter เปิด node) · node `kind=factcheck` ไม่ขึ้นบนผัง แต่แสดงเป็นกล่องพับได้ในแผงของ node ที่ถูกตรวจ · สถานะพับ/กางจำไว้ใน localStorage ส่วน node ที่เปิดอยู่จำผ่าน URL hash
- ชื่อเดิมของ skill คือ `learnmap` (เปลี่ยนชื่อ 2026-11-05) โฟลเดอร์ข้อมูล `.learnmap/` และ key ใน localStorage (`learnmap:<slug>:…`) **คงชื่อเดิมไว้โดยตั้งใจ** เพื่อไม่ให้ map, ไฮไลต์, โน้ต และสถานะอ่านแล้วที่มีอยู่หาย ห้ามเปลี่ยน
- **ไม่ใช้ Lavish** (user สั่งไว้ 2026-11-05) ห้ามรัน `lavish-axi` กับ map
- slug = kebab-case ภาษาอังกฤษ เช่น `apache-iceberg`

## Flow: map ใหม่

1. **เช็คก่อน**: `ls .learnmap/` ถ้ามี slug นี้อยู่แล้วให้ resume แทน
2. **หา context**: ค้น vault (MOC → grep) + ดู CLAUDE.md/memory ของ project ว่า keyword นี้ไปโผล่ในงานตรงไหน
3. **init**:
   ```bash
   python3 $M init .learnmap/<slug> --slug <slug> --title "<หัวข้อ>" \
     --summary "<หนึ่งประโยค>" --context "<project/งานที่ผูกอยู่ หรือว่าง>"
   ```
4. **เขียน root body** ด้วย `fill` (คำจำกัดความ 1 ย่อหน้า + ภาพรวมว่าจะแตกกิ่งอะไรบ้าง ไม่เกิน ~150 คำ)
5. **เพิ่มกิ่ง overview** 5–8 กิ่งเป็น stub ด้วย `add` เลือกจาก lens เหล่านี้ตามที่เหมาะกับหัวข้อ:
   คืออะไร / ทำไมต้องมี (ปัญหาที่แก้) / กลไกทำงานยังไง / ส่วนประกอบ / ใช้เมื่อไหร่-ไม่ควรใช้ / ข้อแลกเปลี่ยน / เทียบกับทางเลือก / โยงกับงานเรา / กับดักที่เจอบ่อย
6. **Fact check** root (ดู section "Fact check")
7. **เปิด**: `open .learnmap/<slug>/index.html` (macOS เปิดใน browser default) แล้วสรุปสั้นๆ ในแชทว่ามีกิ่งอะไรบ้าง

## รับคำสั่ง (ผ่านแชท)

ปุ่มในหน้าเว็บคัดลอกคำสั่งรูปแบบนี้ลง clipboard ให้ user วางในแชท:
```
/create-mind-map <slug> <action> <node> ["arg"]
```
เช่น `/create-mind-map apache-iceberg term n2 "manifest list"` ถ้า user พิมพ์เป็นภาษาคน (เช่น "ขยาย manifest list ใน map iceberg") ก็ให้แปลงเป็น action เดียวกัน ถ้าระบุ node ไม่ได้ให้ใช้ `outline` หาก่อน

ทุก action ให้เริ่มด้วย `python3 $M path <dir> --node <id>` เพื่อดึง context ขั้นต่ำ (เส้นทางจาก root, body ของ node, พี่น้อง, ลูกที่มีอยู่) **ห้ามโหลด map ทั้งก้อนเข้า context** แล้วอย่าสร้างซ้ำกับพี่น้องหรือลูกที่มีอยู่แล้ว

| action | ทำอะไร | คำสั่ง |
|---|---|---|
| `fill` | เขียน body ของ stub (200–400 คำ มี heading/ตาราง/ไดอะแกรมได้) | `fill --node <id>` |
| `expand` | แตกลูก 3–5 อันที่ลึกลงหนึ่งชั้น เป็น stub (title + summary) | `add` |
| `term` | คำใน `arg` กลายเป็นลูกใหม่ `kind=term` **พร้อม body** (user อยากรู้ทันที) `asked_by="select:'<arg>'"` | `add` |
| `example` | ลูก `kind=example` พร้อม body ใช้ข้อมูลจริงของ project ถ้ามี | `add` |
| `why` | ลูก `kind=rationale` พร้อม body: ทำไมออกแบบแบบนี้ ถ้าไม่มีจะเกิดอะไร | `add` |
| `compare` | ลูก `kind=compare` พร้อม body ที่มีตารางเทียบกับ `arg` (ค้น web ถ้าเป็น product) | `add` |
| `ask` | ลูกพร้อม body ที่ตอบคำถามใน `arg` เลือก kind ให้ตรง | `add` |
| `quiz` | ลูก `kind=quiz` body = คำถาม 2–3 ข้อที่ต้องอธิบาย/ประยุกต์ ไม่ใช่ท่องจำ (ห้ามใส่เฉลยใน body) | `add` |
| `quiz-answer` | node เป็น quiz: ตรวจ `arg` เทียบกับเนื้อหาใน map → ลูก `kind=feedback` บอกว่าถูก/ขาด/เข้าใจผิดตรงไหน ชี้ node ที่ควรกลับไปอ่าน | `add` |
| `explain` | user อธิบาย node ด้วยคำของตัวเองใน `arg` → ลูก `kind=feedback` (ไม่ต้อง fact check): ส่วนที่ถูก (อ้างประโยคของ user) · ส่วนที่ขาด · ส่วนที่เข้าใจผิดพร้อมที่ถูก · ความสัมพันธ์กับกิ่งอื่นที่ user เห็นหรือยังไม่เห็น · ชี้ node ที่ควรกลับไปอ่าน ถ้า node เดิมเป็น stub ให้เขียนคำอธิบายของ user เข้าไปเป็นจุดตั้งต้นของ body แล้ว fact check | `add` (+ `fill`) |
| `link` | เชื่อม 2 node ข้ามกิ่ง `arg` = `"<node ปลายทาง> \| <คำบอกความสัมพันธ์>"` | `link` |
| `known` | `status --node <id> --set known` ไม่ต้องเขียนอะไร | `status` |
| `factcheck` | ตรวจ node นี้ (หรือตรวจซ้ำ) ตาม section "Fact check" | `factcheck` |

หลังเขียน body ใหม่ทุกครั้ง (fill/term/example/why/compare/ask) ให้ **fact check ทันทีในรอบเดียวกัน** ก่อนตอบ user · node feedback กับ quiz ไม่ต้องตรวจ แต่ให้บันทึก `factcheck --result not-applicable` เพื่อไม่ให้ค้างใน `unchecked`

ตอบในแชทสั้นๆ: เพิ่ม node อะไร (id + ชื่อ), สรุปผล fact check (ถ้ามีจุดผิดให้บอกชัด) แล้วบอกให้ refresh หน้า (หน้าจะจำ node ที่อ่านอยู่ผ่าน URL hash) ถ้า user ส่งมาหลายคำสั่งในข้อความเดียว ให้ทำตามลำดับแล้วตอบรวมครั้งเดียว

## วิธีสร้างเนื้อหา

### ลำดับแหล่งข้อมูล (หาก่อนเขียน)
1. **เอกสารของงานเอง**: รายงาน, spec, บันทึกประชุม, CLAUDE.md, memory ของ project — ตัวเลขและข้อสรุปที่ทีมวัดหรือตกลงไว้แล้ว อ้างพร้อมเลขหัวข้อ
2. **ของจริงในระบบ**: เปิดโค้ด/DDL, query ข้อมูลจริงหรือข้อมูลจำลองของ project (ค่าใช้จ่ายต่ำ ไม่แตะ PII), ดู metadata (เช่น Glue GetTable) — ใช้ยืนยัน claim ที่เป็นข้อเท็จจริงของ project
3. **เอกสารทางการของ product**: ค้นแล้วเปิดหน้าจริง ระวังหน้าเก่า (ดูวันที่ ถ้าขัดกันให้เชื่อหน้าใหม่)
4. **vault Alice**: ใช้เป็นบริบทและ wikilink ไม่ใช่แหล่งสุดท้ายของเรื่องที่เปลี่ยนเร็ว

### สูตรของ node ที่ดี
- **คำตอบนำ 1–2 บรรทัด** แล้วค่อยตาราง/ไดอะแกรม
- **ตัวอย่างต้องเป็นของจริงถ้าทำได้**: แถวตัวอย่างจากตารางจริง, ตัวเลขที่วัดเอง (เช่น bytes scanned ของ 2 query เทียบกัน) ดีกว่าตัวเลขสมมติ ถ้าใช้ตัวเลขสมมติต้องบอกว่าสมมติ
- **link_to_work ต้องชี้ของที่มีอยู่จริง**: ชื่อตาราง ไฟล์ ตัวเลข การตัดสินใจ หรือคำถามที่ยังค้าง
- **บอกขอบเขตของความรู้**: ถ้า vendor ไม่เปิดเผย (เช่น โครงภายในของ Athena) ให้เขียนว่าเป็นการอนุมานและติด `unverifiable` ใน fact check
- **แยก "ผลจากข้อมูลทดลอง" กับ "ข้อสรุปเรื่องระบบจริง"** เสมอ เช่น อัตรา fail จากชุดทดสอบที่ตั้งใจให้ยาก ห้ามอ่านเป็นคุณภาพของระบบ
- คำถามของ user ที่ถามในแชทแล้วอยากเก็บ ให้เป็น node `ask` ที่ขึ้นด้วยคำถามเดิม → คำตอบ → จุดที่ต้องแก้ความเข้าใจ

### Lens ตามชนิดหัวข้อ
| หัวข้อ | กิ่งที่ควรมี |
|---|---|
| product / บริการ | สถาปัตยกรรมพื้นฐาน · ทำงานยังไง · คิดเงิน · ข้อจำกัด · เทียบทางเลือก · ใช้ในงานเรายังไง |
| data pipeline | รูปแบบ data แต่ละขั้น (schema + แถวจริง) · ใครเขียน ใครอ่าน · จุดที่มี PII · ประเด็นใน spec · คำถามที่ค้าง |
| การตัดสินใจ | ทางเลือก · เกณฑ์ · หลักฐาน · เหตุผลที่เลือก · เงื่อนไขที่จะเปลี่ยนใจ · สิ่งที่ยังไม่ได้ทดลอง |

### Cross-link (เส้นเชื่อมข้ามกิ่ง)
map ที่เป็น tree ล้วนบอกแค่ "อะไรอยู่ใต้อะไร" แต่ความเข้าใจจริงอยู่ที่ "อะไรเกี่ยวกับอะไร" ข้ามกิ่ง
- หลังเขียน node ใหม่ ถามตัวเองว่า node นี้**อธิบาย เป็นสาเหตุ ขัดแย้ง หรือเป็นเงื่อนไข**ของ node ในกิ่งอื่นไหม ถ้าใช่ให้เพิ่ม link
- `python3 $M link <dir> --from nA --to nB --label "<วลีสั้นบนเส้น เช่น ใช้ได้จริงเมื่อ / เป็นเหตุผลที่ต้อง>" --why "<เส้นนี้ช่วยให้เข้าใจอะไร>"`
- **ทุกเส้นต้องมีจุดประสงค์** (script บังคับ `--why`) ห้ามเชื่อมพ่อลูก ห้ามเชื่อมเพราะแค่คำซ้ำกัน
- ปกติให้เชื่อมห่าง ๆ (~1 เส้นต่อ 4–5 node) · ถ้า user สั่ง "เชื่อมให้ครบ" ให้ทุก node ใบและ node กลางมีอย่างน้อย 1 เส้น (ยกเว้น root, หัวกิ่ง และ correction/factcheck) แล้วเช็ค coverage ด้วย script สั้น ๆ
- หน้าเว็บแสดงเฉพาะเส้นของ node ที่เลือก (กางทางไปหาปลายทางชั่วคราว) สีเส้นและป้ายตามกิ่งต้นทาง มีลูกศรบอกทิศ โค้งออกจาก root และเลื่อนป้ายไม่ให้ทับกัน · สวิตช์ "ทุกเส้นเชื่อม" แสดงทุกเส้น (เส้นที่ไม่เกี่ยวกับ node ที่เลือกจะจาง) ผังจึงไม่รกแม้มีเส้นเยอะ

### จำนวนกิ่ง
"มากเท่าที่จำเป็น น้อยที่สุดเท่าที่ทำได้": ลูก 3–5 อันต่อ node · ถ้าเกิน 7 ให้จัดกลุ่มเป็นชั้นกลาง หรือแยกเป็น map ใหม่แล้วเชื่อมด้วย link

### ไม่ให้ map กลายเป็นการอ่านเฉย ๆ
ความรู้ที่ Claude เขียนให้ครบสวยเสี่ยงเป็น "ภาพลวงของการเรียน" ([[Mind Mapping]] · Justin Sung) learning เกิดตอน user ต้องดึงออกมาเอง
- หน้าเว็บมี **อธิบายเองก่อน** (ส่ง `explain`) และ **โหมดทบทวน** (ซ่อนเนื้อหาไว้ให้นึกก่อนแล้วค่อยเปิด)
- เมื่อ user ขอ node ใหม่หลายรอบติดกันโดยไม่ได้ explain หรือ quiz เลย ให้ชวนสั้น ๆ ท้ายคำตอบสักครั้ง (ไม่ต้องทุกรอบ)

### โหมดเติมลึกแบบพับไว้ (user สั่ง "เติมลงลึกไปเรื่อย ๆ")
- เติม body ให้ stub ทุกอันใน level ที่สั่ง + เพิ่มลูก 2–3 อันต่อ node **พร้อม body** แล้ว fact check ทุกอัน
- ไม่ต้องทำอะไรเรื่องการแสดงผล: หน้าเว็บพับทุก node ไว้ยกเว้น root จนกว่า user จะกด (กดแล้วลูกของ node นั้นกางออก)
- งานใหญ่ให้เขียนเป็น script ใน scratchpad ที่เรียก `add` / `fill` / `factcheck` ทีละ node และอ่าน id ใหม่จาก output (`added nX`) อย่าแก้ map.json ตรง
- จบแล้วรัน `unchecked` ต้องว่าง และทุก node ที่ผล `issues` ต้องมีลูก `correction`

## การเขียน node

ส่ง JSON ผ่าน stdin (`--file -`) ด้วย heredoc แบบ quote (`<<'EOF'`) เพื่อไม่ให้ shell ไปแตะ `$` และ backtick:

```bash
python3 $M add .learnmap/apache-iceberg --file - <<'EOF'
[{"parent": "n3", "title": "manifest list", "kind": "term",
  "summary": "รายการ manifest ของ snapshot หนึ่ง",
  "body": "## คืออะไร\n...",
  "link_to_work": "eval_score มี metadata 1,590 เวอร์ชัน เพราะ MERGE ทุกครั้งสร้าง snapshot ใหม่",
  "sources": [{"type": "web", "ref": "https://iceberg.apache.org/spec/"}],
  "confidence": "verified", "asked_by": "select:'manifest list'"}]
EOF
```

field: `parent`, `title`, `kind` (root/concept/mechanism/example/rationale/compare/quiz/feedback/correction/term), `summary` (บรรทัดเดียว โชว์ใน tree และ card), `body` (markdown รองรับตาราง, code block และ ` ```mermaid `), `link_to_work`, `sources` (`type`: web/vault/doc/file, `ref`), `confidence` (verified/from-memory), `asked_by`

สไตล์ body: คำตอบนำก่อนแล้วค่อยลงรายละเอียด / ใช้ตาราง หรือไดอะแกรมเมื่อช่วยให้เข้าใจ / ประโยคไทยสั้น ไม่ใช้ emoji / หนึ่ง node = หนึ่งใจความ ถ้ายาวเกิน 400 คำให้แตกเป็นลูกแทน

## Fact check

เป้าหมาย: ข้อความใน map ต้องเชื่อได้ ไม่ใช่แค่อ่านลื่น ตรวจแบบ**ผู้ตรวจที่ตั้งใจหาจุดผิด** ไม่ใช่หาหลักฐานมายืนยันสิ่งที่ตัวเองเขียนไปแล้ว

1. **ดึง claim**: อ่าน body + link_to_work ของ node แล้วแยกข้อความที่ตรวจสอบได้ออกมาเป็นข้อ ๆ (ตัวเลข, ราคา, เวอร์ชัน, ชื่อ feature, ว่า X รองรับหรือไม่รองรับ Y, ความสัมพันธ์เชิงเหตุผล, ข้อเท็จจริงจาก project เช่นชื่อตารางหรือจำนวนแถว) ไม่ต้องตรวจคำอธิบายเชิงอุปมา ถ้าไม่มี claim ที่ตรวจได้เลยให้ใช้ `--result not-applicable`
2. **หาหลักฐานแยกทีละข้อ** โดยเลือกแหล่งตามชนิดของ claim:
   - product/spec/ราคา → เอกสารทางการก่อน (เช่น iceberg.apache.org, docs.aws.amazon.com) ใช้ WebSearch แล้วเปิดหน้าจริง ห้ามตัดสินจาก snippet อย่างเดียว
   - ข้อเท็จจริงของ project → เปิดไฟล์ รัน query หรือ grep ของจริง อ้าง path
   - ความรู้ใน vault → อ้าง `[[note]]` แต่ vault ไม่นับเป็นแหล่งสุดท้ายสำหรับเรื่อง product ที่เปลี่ยนเร็ว
3. **ตัดสิน**: `correct` / `wrong` / `partly` (ถูกแต่ขาดเงื่อนไขสำคัญ หรือ overclaim) / `unverifiable` (หาแหล่งที่เชื่อได้ไม่เจอ ห้ามปัดเป็น correct)
4. **บันทึก**:
   ```bash
   python3 $M factcheck <dir> --node <id> --result passed|issues|not-applicable --file - <<'EOF'
   {"claims": [{"claim": "...", "verdict": "correct", "evidence": "ข้อความจากแหล่งแบบสั้น", "source": "https://..."}],
    "note": "ข้อสังเกตเพิ่ม ถ้ามี"}
   EOF
   ```
   script จะเพิ่ม node ลูก `kind=factcheck` ที่เป็นตาราง claim และตั้ง badge บน node (ห้าม `passed` ถ้ามี wrong/partly)
5. **ถ้าผล = issues**: เพิ่มลูก `kind=correction` ทันทีสำหรับแต่ละจุดที่ผิด อ้างประโยคเดิม บอกว่าที่ถูกคืออะไร พร้อม source **ห้ามแก้ body เดิม** → fact check correction นั้น → `python3 $M resolve <dir> --node <id>` (script ยอมเฉพาะเมื่อ correction ผ่าน fact check แล้ว) node จะเปลี่ยนเป็น "แก้ไขแล้ว" และหน้าเว็บแสดงกล่องแจ้งการแก้ไขเหนือเนื้อหาเดิม แจ้ง user ให้ชัดว่าแก้ตรงไหน
6. `python3 $M unchecked <dir>` แสดง node ที่ยังไม่ได้ตรวจ ใช้ตอน resume หรือก่อน export (export ได้เฉพาะ node ที่ผ่านแล้ว หรือที่มี correction ครบ)

ถ้า user สั่งตรวจทั้ง map หรือ node เยอะ (เกิน ~5 node) และขอให้ตรวจแบบอิสระ ให้ส่งงานให้ subagent ที่ไม่เห็นเหตุผลตอนเขียน โดยส่งไปแค่ body กับคำสั่งตามขั้น 1–3 แล้วนำผลมาบันทึกด้วยขั้น 4

## คำสั่งอื่น

- `--resume <slug>` / `--list`: `ls .learnmap/` → `python3 $M outline <dir>` → `open <dir>/index.html` → รอคำสั่งในแชท
- `--export <slug>` (**ทำเมื่อ user สั่งเท่านั้น** และรัน `unchecked` ก่อน): เขียนลง vault Alice `03 - Resources/` — node ที่ expanded แล้วเป็น atomic note ละไฟล์ (frontmatter `type: note`, `status: active`, `tags`, `date`) ลิงก์หากันด้วย `[[wikilink]]` ตาม tree + MOC 1 ไฟล์ชื่อ `<title> Learning Map MOC` ก่อนเขียนให้ค้นว่ามี note ซ้ำอยู่แล้วไหม ถ้ามีให้ลิงก์แทนการสร้างใหม่ เสร็จแล้ว append `log.md` (`## [YYYY-MM-DD] ingest | <title> learning map`)
- `render <dir>`: สร้าง index.html ใหม่หลังแก้ template

## จบ

เมื่อ user บอกว่าพอแล้ว ให้สรุปว่า map มีกี่ node, ขยายไปกี่อัน, fact check ผ่าน/มีจุดผิดกี่อัน (`unchecked` ต้องว่าง) และบอก path ของ map ไว้ resume ทีหลัง
