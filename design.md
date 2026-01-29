# PONK Module 3 — Speech Acts / Argumentační celky

## MVP app design

Combining developed ponk-app3 shell (dir `ponk-app3`) with LLM annotation experiment (dir `experiment_01`).

- text received from PONK app in CONLLU format
- converted to raw text, prompt built from prompt_template & payload_template
- send to LLM (this needs to be UFAL-hosted LLM - see /home/polto/ufal/ponk_and_llms_source/experiment_06_aiufal)
- receive & process response -> converted back to CONLLU format with annotations
- send back to PONK app

## MVP Implementation Plan

| Step | Description | Status |
|------|-------------|--------|
| 1 | Wire up `llm_client.py` to call UFAL API (`https://ai.ufal.mff.cuni.cz/api/chat/completions`) | ✅ |
| 2 | Update env vars: `AIUFAL_API_KEY`, model: `LLM3-AMD-MI210.llama3.3:latest` | ✅ |
| 3 | Update prompt: no overlapping spans, wrapper object `{"annotations": [...]}` | ✅ |
| 4 | Add error handling & timeout config | ✅ |
| 5 | Test locally with sample CoNLL-U | ✅ |
| 6 | Deploy to ponk-app3 VM | ⏳ |

**Note:** UFAL LLM model names require server prefix (e.g., `LLM3-AMD-MI210.llama3.3:latest`). List available models: `curl -s -H "Authorization: Bearer $AIUFAL_API_KEY" https://ai.ufal.mff.cuni.cz/api/models`

## CoNLL-U Format & Annotation Strategy

### CoNLL-U Format Overview

CoNLL-U is a tab-separated format with 10 fields per token:
```
ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
```

Example:
```conllu
# sent_id = 1
# text = Nejvyšší správní soud rozhodl v senátě.
1	Nejvyšší	vysoký	ADJ	...	...	3	amod	_	_
2	správní	správní	ADJ	...	...	3	amod	_	_
3	soud	soud	NOUN	...	...	4	nsubj	_	_
4	rozhodl	rozhodnout	VERB	...	...	0	root	_	_
5	v	v	ADP	...	...	6	case	_	_
6	senátě	senát	NOUN	...	...	4	obl	_	SpaceAfter=No
7	.	.	PUNCT	...	...	4	punct	_	_
```

### PonkApp3 Annotation Format

**Pattern:** `PonkApp3:[SpeechActLabel]:[SpanID]=start|end`

Added to the **MISC** column (10th field):

```conllu
3	soud	soud	NOUN	...	...	4	nsubj	_	PonkApp3:01_Situace:a1b2c3=start
4	rozhodl	rozhodnout	VERB	...	...	0	root	_	PonkApp3:01_Situace:a1b2c3=end
```

**Speech Act Labels:**
- `01_Situace` - Situation
- `02_Kontext` - Context
- `03_Postup` - Procedure
- `04_Proces` - Process
- `05_Podmínky` - Conditions
- `06_Doporučení` - Recommendations
- `07_Odkazy` - Links
- `08_Prameny` - References
- `09_Nezařaditelné` - Not classified

### CoNLL-U ↔ Raw Text Conversion Strategy

**Pipeline:**
```
CoNLL-U → Extract Text → LLM Prompt → LLM Response (char offsets) → Map to Tokens → Annotated CoNLL-U
```

**1. CoNLL-U → Raw Text:**
- Extract text from `# text =` comments (sentence-level)
- Build character offset map: `[(token_id, sent_id, char_start, char_end), ...]`
- Preserve token-to-character mapping for reverse lookup

**2. LLM Response → Token Annotations:**
- LLM returns: `[{"start": 286, "end": 541, "label": "01_Situace"}, ...]`
- For each span:
  - Find first token overlapping `start` char → add `PonkApp3:{label}:{uuid}=start`
  - Find last token overlapping `end` char → add `PonkApp3:{label}:{uuid}=end`
  - Generate unique span ID (UUID)

**3. Edge Cases:**
- Multiple annotations on same token → separate with `|` in MISC
- Sentence boundaries → track cumulative character offsets across sentences
- `SpaceAfter=No` → handle punctuation spacing correctly

---

## Deployment Instructions

### Test deployment with uv

1. **Copy files to ponk-app3:**
   ```bash
   # From local machine, copy to jump host (exclude build artifacts)
   rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
     --exclude='*.log' --exclude='.env' \
     ponk-app3/ tpolak@ufallab.ms.mff.cuni.cz:~/ponk-app3-deploy/
   
   # SSH to jump host, then copy to ponk-app3
   ssh tpolak@ufallab.ms.mff.cuni.cz
   rsync -av ~/ponk-app3-deploy/ ponk-app3:~/ponk-app3/
   ```

2. **Install uv and deploy:**
   ```bash
   cd ~/ponk-app3
   
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env  # or restart shell
   
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate
   uv pip install .
   ```

3. **Set up systemd service:**
   See "Systemd Service Setup" section below for creating the service file.
   After setup:
   ```bash
   sudo systemctl start ponk-app3
   ```

4. **Verify:**
   - Visit https://quest.ms.mff.cuni.cz/ponk-app3/
   - Or from ponk-app3: `curl http://localhost:8000/api/health`

### Environment Variables

Set these on ponk-app3 before running the app:

```bash
# Required: UFAL LLM API key (get from UFAL admin or Zimbra Briefcase)
export AIUFAL_API_KEY="your-api-key-here"

# Optional: override defaults
export AIUFAL_ENDPOINT="https://ai.ufal.mff.cuni.cz/api/chat/completions"  # default
export AIUFAL_MODEL="LLM3-AMD-MI210.llama3.3:latest"                          # default
export AIUFAL_USE_MOCK="true"                                               # for testing without API
```

**Environment file for systemd:**

Create `~/ponk-app3/.env` with:
```bash
AIUFAL_API_KEY=your-api-key-here
# Optional overrides:
# AIUFAL_ENDPOINT=https://ai.ufal.mff.cuni.cz/api/chat/completions
# AIUFAL_MODEL=LLM3-AMD-MI210.llama3.3:latest
```

The systemd service (see below) reads this file via `EnvironmentFile=`, ensuring vars persist across VM restarts.

To list available models:
```bash
curl -s -H "Authorization: Bearer $AIUFAL_API_KEY" https://ai.ufal.mff.cuni.cz/api/models
```

### Updating the Deployed App

1. **Stop the running service:**
   ```bash
   ssh ponk-app3
   sudo systemctl stop ponk-app3
   ```

2. **Copy updated files to ponk-app3:**
   ```bash
   # From local machine, copy to jump host (exclude build artifacts)
   rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
     --exclude='*.log' --exclude='.env' \
     ponk-app3/ tpolak@ufallab.ms.mff.cuni.cz:~/ponk-app3-update/
   
   # SSH to jump host, then sync to ponk-app3
   ssh tpolak@ufallab.ms.mff.cuni.cz
   
   # Backup current version on ponk-app3 (optional)
   ssh ponk-app3 "cp -r ~/ponk-app3 ~/ponk-app3.bak.\$(date +%Y%m%d)"
   
   # Sync updated files to ponk-app3
   rsync -av ~/ponk-app3-update/ ponk-app3:~/ponk-app3/
   ```

3. **Update dependencies (only if pyproject.toml changed):**
   ```bash
   ssh ponk-app3
   cd ~/ponk-app3
   source .venv/bin/activate
   uv pip install .
   ```

4. **Restart the service:**
   ```bash
   sudo systemctl start ponk-app3
   
   # Verify
   systemctl status ponk-app3
   curl http://localhost:8000/api/health
   ```

4. **Check logs if issues:**
   ```bash
   sudo journalctl -u ponk-app3 -f
   ```

### Systemd Service Setup

Create `/etc/systemd/system/ponk-app3.service`:
```ini
[Unit]
Description=PONK App3 Speech Acts Service
After=network.target

[Service]
Type=simple
User=tpolak
WorkingDirectory=/home/tpolak/ponk-app3
EnvironmentFile=/home/tpolak/ponk-app3/.env
ExecStart=/home/tpolak/ponk-app3/.venv/bin/python app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ponk-app3
sudo systemctl start ponk-app3
```

Useful commands:
```bash
sudo systemctl status ponk-app3   # check status
sudo systemctl restart ponk-app3  # restart after updates
sudo journalctl -u ponk-app3 -f   # follow logs
```

---

## Local Testing

### Generating Test CoNLL-U Data

The app expects input in CoNLL-U format. You can generate CoNLL-U from Czech text using UDPipe:

```bash
# Using UDPipe REST API
echo "Pokud jste obdrželi výzvu k zaplacení pokuty." | \
  curl -F data=@- -F model=czech-pdt-ud-2.12-230717 \
  https://lindat.mff.cuni.cz/services/udpipe/api/process
```

Or use the Python UDPipe library, or manually create test data for simple cases.

### Testing with curl

**Basic test (short text):**

```bash
curl -X POST http://localhost:8000/api/annotate \
  -H "Content-Type: application/json" \
  -d '{
  "result": "# sent_id = 1\n# text = Pokud jste obdrželi výzvu k zaplacení pokuty za přestupek, měli byste nejprve ověřit, zda je výzva oprávněná.\n1\tPokud\tpokud\tSCONJ\t_\t_\t4\tmark\t_\t_\n2\tjste\tbýt\tAUX\t_\t_\t4\taux\t_\t_\n3\tobdrželi\tobdržet\tVERB\t_\t_\t4\tadvcl\t_\t_\n4\tvýzvu\tvýzva\tNOUN\t_\t_\t0\troot\t_\t_\n5\tk\tk\tADP\t_\t_\t6\tcase\t_\t_\n6\tzaplacení\tzaplacení\tNOUN\t_\t_\t4\tnmod\t_\t_\n7\tpokuty\tpokuta\tNOUN\t_\t_\t6\tnmod\t_\t_\n8\tza\tza\tADP\t_\t_\t9\tcase\t_\t_\n9\tpřestupek\tpřestupek\tNOUN\t_\t_\t7\tnmod\t_\tSpaceAfter=No\n10\t,\t,\tPUNCT\t_\t_\t4\tpunct\t_\t_\n11\tměli\tmít\tVERB\t_\t_\t4\tconj\t_\t_\n12\tbyste\tbýt\tAUX\t_\t_\t11\taux\t_\t_\n13\tnejprve\tnejprve\tADV\t_\t_\t14\tadvmod\t_\t_\n14\tověřit\tověřit\tVERB\t_\t_\t11\txcomp\t_\tSpaceAfter=No\n15\t,\t,\tPUNCT\t_\t_\t14\tpunct\t_\t_\n16\tzda\tzda\tSCONJ\t_\t_\t19\tmark\t_\t_\n17\tje\tbýt\tAUX\t_\t_\t19\tcop\t_\t_\n18\tvýzva\tvýzva\tNOUN\t_\t_\t19\tnsubj\t_\t_\n19\toprávněná\toprávněný\tADJ\t_\t_\t14\tccomp\t_\tSpaceAfter=No\n20\t.\t.\tPUNCT\t_\t_\t4\tpunct\t_\t_\n\n# sent_id = 2\n# text = Zkontrolujte datum, místo a popis přestupku.\n1\tZkontrolujte\tzkontrolovat\tVERB\t_\t_\t0\troot\t_\t_\n2\tdatum\tdatum\tNOUN\t_\t_\t1\tobj\t_\tSpaceAfter=No\n3\t,\t,\tPUNCT\t_\t_\t2\tpunct\t_\t_\n4\tmísto\tmísto\tNOUN\t_\t_\t2\tconj\t_\t_\n5\ta\ta\tCCONJ\t_\t_\t6\tcc\t_\t_\n6\tpopis\tpopis\tNOUN\t_\t_\t2\tconj\t_\t_\n7\tpřestupku\tpřestupek\tNOUN\t_\t_\t6\tnmod\t_\tSpaceAfter=No\n8\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n"
}'
```

**View formatted output:**

```bash
curl -s -X POST http://localhost:8000/api/annotate \
  -H "Content-Type: application/json" \
  -d '{"result": "# sent_id = 1\n# text = Test věta.\n1\tTest\ttest\tNOUN\t_\t_\t0\troot\t_\t_\n2\tvěta\tvěta\tNOUN\t_\t_\t1\tnmod\t_\tSpaceAfter=No\n3\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n"}' \
  | jq -r .result
```

The output will include `PonkApp3:` annotations in the MISC column (10th field) of annotated tokens.

**Example annotated output:**
```
1  Test  ...  PonkApp3:01_Situace:abc123=start
2  věta  ...  _
3  .     ...  PonkApp3:01_Situace:abc123=end
```

### Health Check

```bash
curl http://localhost:8000/api/health
# {"status": "ok"}
```

---

## VM Access Summary

| Property | Value |
|----------|-------|
| VM name | `ponk-app3` |
| Internal IP | `10.10.51.187` |
| SSH access | `ssh tpolak@ponk-app3` (from quest or ufallab) |
| Public URL | https://quest.ms.mff.cuni.cz/ponk-app3/ |
| App port | 8000 |
| User | `tpolak` (sudo) |

---

## Email communication with IT and JM (newest first)

### Subject: Service integration feedback | 2026-01-28 | JM → TP

Tak až na to kódování už to snad funguje: https://quest.ms.mff.cuni.cz/ponk/devel/

Předpokládám správně, že kategorie se v textu nikdy nepřekrývají, tzn. každá část textu bude ohodnocena jen jednou hodnotou?

### Subject: Encoding issue | 2026-01-26 | JM → TP

Pracuju na tom, ale mám problém s kódováním češtiny. Podíval byste se prosím na kódování ve vracených datech?

Test:
```bash
curl -X POST https://quest.ms.mff.cuni.cz/ponk-app3/api/annotate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

vrací špatné kódování. Ale nevylučuju úplně, že je chyba někde u mne.

### Subject: ponk-app3 service ready for testing | 2026-01-26 | TP → JM

Mám hotovou první verzi služby ponk-app3 pro speech acts. Běží teď na VM a je dostupná přes quest proxy. Chtěl bych poprosit o zpětnou vazbu k formátu anotací, zda se to hodí do PONKu.

**URL služby:**
- https://quest.ms.mff.cuni.cz/ponk-app3/
- Endpoint: `POST /api/annotate`

**Formát:**
- Request: `{"result": "<conllu_text>"}`
- Response: `{"result": "<annotated_conllu>", "colours": {...}}`

**Anotace v MISC poli:**
```
PonkApp3:[SpeechActLabel]:[SpanID]=start|end
```

Například:
```
2  správní  ...  PonkApp3:03_Postup:30d15740=start
5  .        ...  PonkApp3:03_Postup:30d15740=end
```

**Speech act kategorie:**
01_Situace, 02_Kontext, 03_Postup, 04_Proces, 05_Podmínky, 06_Doporučení, 07_Odkazy, 08_Prameny, 09_Nezařaditelné

Zatím služba používá mock anotace (pro testování), ale struktura a formát jsou finální. Můžete prosím zkusit, jestli formát sedí s PONKem? Hlavně jestli se anotace správně zobrazují a jestli je v pořádku formát v MISC poli.

**Pro ověření:**
```bash
curl https://quest.ms.mff.cuni.cz/ponk-app3/api/health
```

Test s `test_request.json`:
```bash
curl -X POST https://quest.ms.mff.cuni.cz/ponk-app3/api/annotate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### Subject: ponk-app3 IP address | 2026-01-26 | IT → TP

IP adresa VM je dostupná ze stroje quest.ms.mff.cuni.cz nebo ufallab.ms.mff.cuni.cz.

Dá se použít jméno ponk-app3, které se překládá podle /etc/hosts na 10.10.51.187.

Příklad z questu:
```
# ping ponk-app3
PING ponk-app3 (10.10.51.187) 56(84) bytes of data.
64 bytes from ponk-app3 (10.10.51.187): icmp_seq=1 ttl=64 time=0.387 ms
```

Doplnil jsem podobný záznam i na ufallabu.

### Subject: ponk-app3 IP address | 2026-01-26 | TP → IT

Jaká je prosím IP adresa ponk-app3 pro SSH přístup?

### Subject: ponk-app3 VM ready | 2026-01-16 | IT → TP

Virtualka ponk-app3 je pripravena. Je to klon ponk-app2 ve kterem jsem pouze odebral uzivatele krome J.Mirovskeho.

Na virtualce je pripraven ucet tpolak s inicialnim UFALim well known heslem (dostupne v Zimbra Briefcase - data_for_UFAL_community). Ucet ma nastavene pravo sudo.

Port 8000 pripravene virtualky je dostupny pres quest proxy na URL: https://quest.ms.mff.cuni.cz/ponk-app3/

UFAL LLM servery jsou dostupne na stejne siti. Pokud by aplikace generovala vetsi objem dotazu nez cca 100 dotazu/h bylo by dobre se domluvit jake endpointy bude vyuzivat.

### Subject: PONK module integration | 2026-01-16 | JM → TP

S ostatními moduly (lingv. pravidla, lex. překvapení) to řešíme tak, že každý běží na své vlastní virtuálce a já s nimi komunikuju přes API. Pro Vás by asi bylo nejsnazší si některou z nich vzít, udělat kopii a tu upravit pro sebe. Kopii virtuálky a Vaše přístupové údaje k ní by dělali naši ajťáci. Záleží ovšem na hw požadavcích.

V API volání posílám data ve formátu CoNLL-U, přičemž odpověď očekávám opět v CoNLL-U s tím, že mi informace, které mám zobrazit, přidáte buď do nějakých komentářů před větami či (možná raději) do sloupce misc u jednotlivých tokenů. Konkrétní podobu bychom doladili, ale možná to může být něco jako SpeechAct=1 nebo SA=9, kdyžtak navrhněte Vy, jak byste to viděl.

Barevnou paletu mi můžete poslat v rámci JSONu, který mi budete vracet, nebo můžeme dát nějakou natvrdo. Návratový JSON tedy může mít položku "result", kde bude upravené CoNLL-U, a položku colours, kde bude definice barev pro jednotlivé hodnoty.

### Subject: PONK module integration | 2026-01-16 | TP → JM

Pracuji na dalším modulu pro PONK - "speech acts", kde budou jednotlivé části vstupního textu klasifikované (1-situace, 2-kontext, 3-postup, 4-proces, 5-podminky, 6-doporuceni, 7-odkazy, 8-prameny, 9-nezaraditelne). Modul by měl být přidaný do stávající aplikace, backend bude Python s API napojením na nějaký model hostovaný na UFALu. Asi by to mělo vypadat podobně jako "překvapení", t.j. barevná paleta vyznačující klasifikaci jednotlivých částí textu.

Chtěl bych poprosit o informace:
- Jak vypadá deployment PONKu a jaké jsou požadavky na integraci dalšího modulu? Je to "frontend - API - backend" nebo je to pohromadě?
- Pokud pohromadě - je nějaký github repozitář, do kterého mám přidat svůj kód?
- Pokud zvlášť - kam můžu udělat "deployment" svého modulu? Jaká je specifikace API komunikace? (t.j. jak vypadá REQUEST a jak má vypadat RESPONSE)

---

## Original requirement (2026-01-08)

- KUKy dataset with annotations https://ufal.mff.cuni.cz/grants/ponk/kuky , https://lindat.mff.cuni.cz/repository/items/1b92d326-7d0e-45ea-b9b8-e434bd16fee8
- LLM to generate rules from annotations
- the aim is to recognize argumentation structure
- readability attributes

- 
- domluvit s Jirkou Mirovskym pridani modulu 3 do ponk frontendu quest.ms.mff.cuni.cz/ponk/
- tento module barevne vyznaci vyznamove celky vstupniho dokumentu podle anotaci v KUKY 1.0

- backend bude prompt, ktery s vyuzitim ufal LLM analyzuje uzivatelem zadany dokument and identifikuje argumentacni casti dokumentu (vrati json podobne struktury jako KUKY 1.0) a frontend to pak zobrazi

- uzivatel muzu uploadnout jakykoliv dokument, t.j. je dulezite, udelat nejaky preprocessing dokumentu, aby byl vhodny pro LLM: pro jednoduchost, rozdelit jenom na odstavce (a i to jenom dlouhe texty)

### Backend

- raw text rozdelit na rozumne velke casti
- vlozit do promptu (staticky, predpripraveny)
- poslat na ufal GPT API
- zpracovat vystup (json)
- zobrazit vystup v frontendu
- vzit zatim jenom normativni kategorie 01-09 (popsane v https://ufal.mff.cuni.cz/grants/ponk/kuky 4.2.1)

01_Situace
02_Kontext
03_Postup
04_Proces
05_Podmínky
06_ Doporučení
07_Odkazy
08_Prameny
09_Nezařaditelné


671918e2c6537d54ff0626db

672b4359c6537d54ff062852