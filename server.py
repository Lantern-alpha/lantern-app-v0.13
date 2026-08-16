
import os, json, re, uuid, time, hashlib, random
from pathlib import Path
from urllib.parse import urlparse
import requests
from flask import Flask, request, jsonify, send_from_directory, Response
from openai import OpenAI

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/"public"
VAULT=json.loads((ROOT/"vault.json").read_text())
BODIES=json.loads((ROOT/"bodies.json").read_text())
app=Flask(__name__, static_folder=None)
client=OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) if os.environ.get("OPENAI_API_KEY") else None
MODEL=os.environ.get("OPENAI_LIGHT_MODEL","gpt-5-mini")
SUPABASE_URL=(os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
SUPABASE_SECRET_KEY=(os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
SUPABASE_PUBLISHABLE_KEY=(os.environ.get("SUPABASE_PUBLISHABLE_KEY") or "").strip()
TTS_MODEL=(os.environ.get("OPENAI_TTS_MODEL") or "gpt-4o-mini-tts").strip()
VOICE_FEMALE=(os.environ.get("LANTERN_VOICE_FEMALE") or "marin").strip()
VOICE_MALE=(os.environ.get("LANTERN_VOICE_MALE") or "cedar").strip()
SUPABASE_REST=f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""

def config_status():
    problems=[]
    try:
        u=urlparse(SUPABASE_URL)
        if u.scheme!="https" or not u.netloc.endswith(".supabase.co") or u.path not in ("","/"):
            problems.append("SUPABASE_URL must contain only the project URL, for example https://PROJECT.supabase.co")
    except Exception:
        problems.append("SUPABASE_URL is invalid.")
    if not SUPABASE_SECRET_KEY:
        problems.append("SUPABASE_SECRET_KEY is missing.")
    elif not (SUPABASE_SECRET_KEY.startswith("sb_secret_") or SUPABASE_SECRET_KEY.count(".")==2):
        problems.append("SUPABASE_SECRET_KEY does not look like a Supabase server secret.")
    if not SUPABASE_PUBLISHABLE_KEY:
        problems.append("SUPABASE_PUBLISHABLE_KEY is missing.")
    if not os.environ.get("OPENAI_API_KEY"):
        problems.append("OPENAI_API_KEY is missing.")
    return {"ok":not problems,"problems":problems}
""
PATHWAYS=["Prepare Me","Encourage Me","Comfort Me","Calm Me","Inspire Me","Teach Me","Connect Me","Surprise Me"]
ADMIN_TOKEN=(os.environ.get("LANTERN_ADMIN_TOKEN") or "").strip()

def is_admin_request():
    token=(request.headers.get("X-Lantern-Admin-Token") or "").strip()
    return bool(ADMIN_TOKEN and token and hashlib.sha256(token.encode()).digest()==hashlib.sha256(ADMIN_TOKEN.encode()).digest())


def sb_headers(prefer=None):
    status=config_status()
    if status["problems"]:
        raise RuntimeError("; ".join(status["problems"]))
    h={"apikey":SUPABASE_SECRET_KEY,"Content-Type":"application/json"}
    if not SUPABASE_SECRET_KEY.startswith("sb_secret_"):
        h["Authorization"]=f"Bearer {SUPABASE_SECRET_KEY}"
    if prefer:
        h["Prefer"]=prefer
    return h

def _sb_error(r, operation, table):
    # Never return request headers or secret-bearing URLs to the browser.
    detail=""
    try:
        payload=r.json()
        detail=payload.get("message") or payload.get("error") or payload.get("hint") or ""
    except Exception:
        detail=""
    base=f"Supabase {operation} failed for {table} (HTTP {r.status_code})"
    if r.status_code==404:
        base+= ". Confirm the Lantern schema has been run and the table is exposed to the Data API."
    elif r.status_code in (401,403):
        base+= ". Check the server-side Supabase secret key and API permissions."
    if detail:
        base+= f": {detail[:240]}"
    return RuntimeError(base)

def sb_get(table,params=None):
    try:
        r=requests.get(f"{SUPABASE_REST}/{table}",headers=sb_headers(),params=params or {},timeout=20)
    except requests.RequestException as e:
        raise RuntimeError(f"Could not reach Supabase while reading {table}.") from e
    if not r.ok: raise _sb_error(r,"read",table)
    return r.json()

def sb_post(table,payload,prefer="return=minimal"):
    try:
        r=requests.post(f"{SUPABASE_REST}/{table}",headers=sb_headers(prefer),json=payload,timeout=20)
    except requests.RequestException as e:
        raise RuntimeError(f"Could not reach Supabase while writing {table}.") from e
    if not r.ok: raise _sb_error(r,"write",table)
    return r.json() if "return=representation" in prefer else None

def sb_patch(table,payload,params,prefer="return=minimal"):
    try:
        r=requests.patch(f"{SUPABASE_REST}/{table}",headers=sb_headers(prefer),params=params,json=payload,timeout=20)
    except requests.RequestException as e:
        raise RuntimeError(f"Could not reach Supabase while updating {table}.") from e
    if not r.ok: raise _sb_error(r,"update",table)
    return r.json() if "return=representation" in prefer else None

def auth_headers(access_token=None):
    if not SUPABASE_PUBLISHABLE_KEY:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is missing.")
    h={"apikey":SUPABASE_PUBLISHABLE_KEY,"Content-Type":"application/json"}
    if access_token:h["Authorization"]=f"Bearer {access_token}"
    return h

def auth_post(path,payload,access_token=None):
    try:
        r=requests.post(f"{SUPABASE_URL}/auth/v1/{path}",headers=auth_headers(access_token),json=payload,timeout=25)
    except requests.RequestException as e:
        raise RuntimeError("Could not reach Supabase Auth.") from e
    if not r.ok:
        detail=""
        try:
            d=r.json();detail=d.get("msg") or d.get("message") or d.get("error_description") or d.get("error") or ""
        except Exception:pass
        raise RuntimeError((detail or f"Authentication failed (HTTP {r.status_code}).")[:300])
    return r.json() if r.content else {}

def auth_get_user(access_token):
    try:r=requests.get(f"{SUPABASE_URL}/auth/v1/user",headers=auth_headers(access_token),timeout=20)
    except requests.RequestException:return None
    return r.json() if r.ok else None

def bearer_token():
    h=(request.headers.get("Authorization") or "").strip()
    return h.split(" ",1)[1].strip() if h.lower().startswith("bearer ") else None

def authenticated_user():
    token=bearer_token();return auth_get_user(token) if token else None

def ensure_profile(uid,email=None,first_name=None,country=None,tier="free"):
    rows=sb_get("users",{"id":f"eq.{uid}","select":"id,email,first_name,country,tier"})
    if rows:
        clean={k:v for k,v in {"email":email,"first_name":first_name,"country":country}.items() if v not in (None,"")}
        if clean:sb_patch("users",clean,{"id":f"eq.{uid}"})
    else:
        sb_post("users",{"id":uid,"email":email,"first_name":first_name,"country":country,"tier":tier,"created":time.time()})
    if not sb_get("prefs",{"user_id":f"eq.{uid}","select":"user_id"}):sb_post("prefs",{"user_id":uid,"voice":"lantern"})

def migrate_guest_data(guest_id,auth_id):
    if not guest_id or guest_id==auth_id:return
    if not sb_get("users",{"id":f"eq.{guest_id}","select":"id"}):return
    for table in ("recent","reflections"):
        try:sb_patch(table,{"user_id":auth_id},{"user_id":f"eq.{guest_id}"})
        except Exception:pass
    try:
        gp=sb_get("prefs",{"user_id":f"eq.{guest_id}","select":"mode,voice,sound,faith,language,history"})
        if gp:sb_patch("prefs",gp[0],{"user_id":f"eq.{auth_id}"})
    except Exception:pass
    try:
        saved=sb_get("saved",{"user_id":f"eq.{guest_id}","select":"story_id,title,provenance,text,created"})
        for row in saved:
            if not sb_get("saved",{"user_id":f"eq.{auth_id}","story_id":f"eq.{row['story_id']}","select":"story_id"}):
                row["user_id"]=auth_id;sb_post("saved",row)
    except Exception:pass

def ensure_user(uid):
    rows=sb_get("users",{"id":f"eq.{uid}","select":"id"})
    if not rows:
        au=authenticated_user()
        if au and str(au.get("id"))==str(uid):
            meta=au.get("user_metadata") or {}
            sb_post("users",{"id":uid,"email":au.get("email"),"first_name":meta.get("first_name"),"country":meta.get("country"),"tier":"free","created":time.time()})
        else:sb_post("users",{"id":uid,"tier":"guest","created":time.time()})
    if not sb_get("prefs",{"user_id":f"eq.{uid}","select":"user_id"}):sb_post("prefs",{"user_id":uid,"voice":"lantern"})

def user_id():
    au=authenticated_user()
    if au and au.get("id"):return str(au["id"])
    return request.headers.get("X-Lantern-User") or "guest-"+request.remote_addr.replace(":","_")

def strip_json(t):
    t=re.sub(r"^```(?:json)?\s*|\s*```$","",t.strip())
    a,b=t.find("{"),t.rfind("}")
    return json.loads(t[a:b+1] if a>=0 and b>a else t)

def fallback_voice(moment,pathway):
    seed=((moment or "")+"|"+(pathway or "")).encode("utf-8")
    return "female" if hashlib.sha256(seed).digest()[0] % 2 == 0 else "male"

def fallback(moment,pathway):
    if pathway:return {"pathway":pathway,"mechanism":"explicit intent","gravity":"low","tone":"warm","distance":"distant","microcopy":"Finding something that fits this moment.","clarify":False,"clarification_question":None,"voice_choice":fallback_voice(moment,pathway),"audio_style":"Warm, restrained, natural storytelling with pathway-appropriate pacing.","ambience":"rain_glass" if pathway=="Calm Me" else "night_room" if pathway=="Comfort Me" else "journey" if pathway=="Prepare Me" else "open_air"}
    t=(moment or "").lower()
    rules=[("Prepare Me",r"interview|presentation|exam|meeting|tomorrow|speech|first day|audition"),
    ("Comfort Me",r"grief|died|death|loss|heartbroken|hard day|hurt|sad"),
    ("Calm Me",r"anxious|anxiety|panic|overthink|stressed|stress|nervous|can't sleep"),
    ("Encourage Me",r"failed|rejected|discouraged|keep going|tired of trying"),
    ("Inspire Me",r"inspire|stuck|creative|idea|possibility"),
    ("Teach Me",r"teach|learn|curious|interesting|weird|history|science"),
    ("Connect Me",r"alone|lonely|belong|home|friend|outsider|new city|miss someone")]
    for p,pat in rules:
        if re.search(pat,t):return {"pathway":p,"mechanism":"moment fit","gravity":"low","tone":"warm","distance":"distant","microcopy":"Finding something that fits this moment.","clarify":False,"clarification_question":None}
    return {"pathway":"Surprise Me","mechanism":"serendipity","gravity":"low","tone":"curious","distance":"distant","microcopy":"Some stories are worth finding by accident.","clarify":False,"clarification_question":None}

def analyze(moment,pathway):
    if not client:return fallback(moment,pathway)
    p=f"""You are LIGHT, Lantern's story-routing intelligence. Lantern is a story product, not a therapist, coach, friend or diagnostic system.
User moment: {moment!r}
Selected pathway: {pathway!r}
Explicit intent outranks inference. Use minimum necessary understanding. Return ONLY JSON:
{{"pathway": one of {PATHWAYS}, "mechanism":"short phrase","gravity":"low|medium|high","tone":"gentle|warm|playful|curious|energizing|reflective|grounded","distance":"close|parallel|distant","microcopy":"one short relevant line for the Finding Your Story screen","clarify":false,"clarification_question":null,"voice_choice":"female|male","audio_style":"one concise premium storyteller performance direction","ambience":"rain_glass|night_room|open_air|journey|quiet_fire"}}
Choose voice_choice from narrative texture, never from stereotypes about the user's identity or pathway. Both voices can serve every pathway.
Clarify only if a missing detail materially changes safe routing."""
    return strip_json(client.responses.create(model=MODEL,input=p).output_text)

def score(profile,item,recent):
    n=-100 if item["id"] in recent else 0
    n+=5 if item["pathway"]==profile["pathway"] else 0
    n+=2 if item.get("gravity")==profile.get("gravity") else 0
    n+=1 if profile.get("tone") in item.get("tone",[]) else 0
    n+=1 if profile.get("distance") in item.get("distance",[]) else 0
    return n

def retrieve(profile,recent):
    r=sorted(VAULT,key=lambda x:score(profile,x,recent),reverse=True)
    return (r[0],score(profile,r[0],recent)) if r else (None,-999)

def story_fingerprint(title,text):
    norm=re.sub(r"\s+"," ",((title or "")+" "+(text or "")).strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:20]

def generate(moment,profile):
    if not client:return None

    premise_prompt=f"""You are Lantern's story editor.
USER MOMENT (context only; never mirror it literally): {moment!r}
LIGHT PROFILE: {json.dumps(profile)}

Build an ACTUAL STORY a person would tell a friend, not a poem, literary vignette, meditation, parable, inspirational essay, or audiobook monologue.

Before prose, create a simple story engine:
- a relatable person with a concrete situation
- something they want / need / are trying to do
- a problem, surprise, mistake, obstacle, discovery or unresolved question
- 3-5 things that actually HAPPEN
- an earned turn or realization through events
- a restrained ending that leaves perspective/reassurance without stating a moral

STYLE:
- plain, conversational English
- actions, decisions, dialogue and consequences over description
- concrete details only when they matter
- no decorative prose
- no "pool of light", "steam curled", "muted silhouette", "faded photograph", "whispering wind", "golden glow", or similar literary filler
- no abstract opening about life/courage/fear
- preserve Story Distance: never reproduce the user's exact situation

The first 15 seconds must make a listener ask "what happened next?"

Return ONLY JSON:
{{
 "cold_open":"2-4 plain conversational sentences starting in the middle of something happening",
 "central_question":"the simple unanswered question pulling us forward",
 "character":"who we are following, in one sentence",
 "goal":"what they are trying to do",
 "complication":"what makes it difficult/interesting",
 "events":["event 1","event 2","event 3","event 4"],
 "turn":"earned turn/discovery",
 "afterglow":"what feeling remains, without moralizing",
 "voice_choice":"female|male",
 "sound_palette":"forward|warm|quiet|wonder|curious"
}}"""
    premise=strip_json(client.responses.create(model=MODEL,input=premise_prompt).output_text)
    if not premise or not premise.get("central_question") or not premise.get("cold_open"):return None

    story_prompt=f"""Write the Lantern story from this approved engine.

USER MOMENT (context only): {moment!r}
LIGHT PROFILE: {json.dumps(profile)}
STORY ENGINE: {json.dumps(premise)}

TARGET:
A compelling 5-7 minute spoken story, roughly 850-1100 words.

VOICE ON THE PAGE:
It should sound like a very good storyteller speaking naturally to another person.
NOT literary. NOT poetic. NOT overly descriptive. NOT an essay. NOT a motivational speech.

RULES:
- Start immediately with action/situation from the cold open.
- Use short-to-medium paragraphs.
- Dialogue is welcome when natural.
- Every 30-45 seconds, something should happen, change, be learned, be decided, go wrong, become harder, become clearer, or surprise us.
- Keep the central question alive until late in the story.
- Favor verbs and human behavior over adjectives.
- Do not describe ordinary light/weather/objects unless they affect what happens.
- No decorative metaphors or poetic sentence fragments.
- Do not write lines that sound designed to become Instagram quotes.
- Preserve Story Distance.
- No therapy framing, advice, affirmations, guaranteed outcomes, sermon, or explicit lesson.
- Do not end with "and that's when...", "the lesson was...", "you've got this", or a question to the listener.
- Ending should be simple, human, and earned.

VISUAL DIRECTION:
Return 5-7 VISUAL CATEGORIES only, for the interface to interpret internally.
Do not write captions for the user. Use simple categories like "start_line", "empty_chair", "train_window", "workbench", "road", "doorway", "crowd_from_distance", "hands_object", "open_space".
These are production metadata and must never appear as user-facing text.

Return ONLY JSON:
{{
 "title":"clear, intriguing, non-poetic title",
 "story":"...",
 "landing":"return_to_life|close_for_now",
 "voice_choice":"female|male",
 "audio_style":"natural spoken storytelling; rhythmic and conversational; vary pace with events; pause at turns; never audiobook or announcer delivery",
 "sound_palette":"forward|warm|quiet|wonder|curious",
 "visual_beats":[{{"at":0.0,"kind":"start_line"}}],
 "hook":"plain-language story hook"
}}"""
    g=strip_json(client.responses.create(model=MODEL,input=story_prompt).output_text)
    if g and not g.get("voice_choice"):g["voice_choice"]=premise.get("voice_choice","female")
    return g

def quality(moment,profile,story):
    if not client:return True
    prompt=f"""You are Lantern's ruthless story editor.

USER MOMENT: {moment!r}
PROFILE: {json.dumps(profile)}
STORY:
{story[:16000]}

Reject the story if it feels like:
- poetry, literary fiction, a meditation, a motivational essay, a parable, or a beautifully-worded monologue
- too descriptive relative to what actually happens
- generic inspirational AI writing
- literal mirroring of the user's problem
- a character simply feeling bad, thinking, then realizing something
- predictable adversity -> success -> moral
- setup that takes too long before anything happens
- decorative imagery ("pool of light", "steam curled", "muted silhouette", etc.)
- an audiobook passage rather than something a person would naturally tell another person
- advice, therapy, preaching, slogans, or explicit lessons

A PASSING story has:
1. a relatable human situation,
2. a clear question/problem,
3. events/actions/decisions,
4. forward motion,
5. at least one meaningful complication or surprise,
6. a simple earned ending,
7. plain conversational language.

Return ONLY JSON:
{{"pass":true|false,"relatable":1-10,"hook":1-10,"forward_motion":1-10,"plain_language":1-10,"stay_to_end":1-10,"reason":"brief"}}.
Pass only if every numeric score is >= 7."""
    q=strip_json(client.responses.create(model=MODEL,input=prompt).output_text)
    scores=[q.get(k,0) for k in ("relatable","hook","forward_motion","plain_language","stay_to_end")]
    return bool(q.get("pass")) and min(scores)>=7

def entitlement(uid):
    if is_admin_request():
        return {"state":"admin","tier":"admin","full_allowed":True,"full_remaining":"unlimited","curated_allowed":True,"curated_remaining":"unlimited"}
    ensure_user(uid)
    rows=sb_get("users",{"id":f"eq.{uid}","select":"tier,email"}); u=rows[0] if rows else {"tier":"guest","email":None}
    tier=u.get("tier") or "guest"; registered=bool(u.get("email")); now=time.time(); week=now-7*86400; month=now-30*86400
    def count(event,cutoff=None):
        p={"user_id":f"eq.{uid}","event":f"eq.{event}","select":"id"}
        if cutoff is not None: p["created"]=f"gte.{cutoff}"
        return len(sb_get("events",p))
    if not registered and tier!="paid":
        used=count("full_moment"); return {"state":"guest","tier":"guest","full_allowed":used<2,"full_remaining":max(0,2-used),"curated_allowed":True,"curated_remaining":"guest-preview"}
    if tier=="paid":
        used=count("full_moment",month); return {"state":"paid","tier":"paid","full_allowed":used<12,"full_remaining":max(0,12-used),"curated_allowed":True,"curated_remaining":"unlimited"}
    full=count("full_moment",month); curated=count("curated_story",week)
    return {"state":"free","tier":"free","full_allowed":full<1,"full_remaining":max(0,1-full),"curated_allowed":curated<1,"curated_remaining":max(0,1-curated)}

def consume(uid,kind,story_id):
    if is_admin_request():
        return
    event="full_moment" if kind=="full" else "curated_story"
    sb_post("events",{"user_id":uid,"event":event,"story_id":story_id,"created":time.time()})

@app.get("/")
def index():
    return send_from_directory(PUBLIC,"index.html")

@app.get("/<path:filename>")
def public_file(filename):
    p=PUBLIC/filename
    if p.exists() and p.is_file(): return send_from_directory(PUBLIC,filename)
    return jsonify({"error":"not_found"}),404
@app.post("/api/admin/verify")
def admin_verify():
    return jsonify({"ok":is_admin_request(),"admin":is_admin_request()})

@app.post("/api/admin/simulate-tier")
def admin_simulate_tier():
    if not is_admin_request(): return jsonify({"ok":False,"error":"admin_required"}),403
    d=request.get_json(force=True) or {}; tier=d.get("tier")
    if tier not in ("guest","free","paid"): return jsonify({"ok":False,"error":"invalid_tier"}),400
    uid=user_id(); ensure_user(uid)
    email=None if tier=="guest" else "alpha-admin@lantern.test"
    sb_patch("users",{"tier":tier,"email":email},{"id":f"eq.{uid}"})
    return jsonify({"ok":True,"simulated_tier":tier})

@app.get("/health")
def health():
    cfg=config_status()
    out={"ok":cfg["ok"],"ai":bool(client),"model":MODEL,"tts_model":TTS_MODEL,
         "supabase_configured":bool(SUPABASE_URL and SUPABASE_SECRET_KEY),
         "supabase_auth_configured":bool(SUPABASE_PUBLISHABLE_KEY),
         "config_ok":cfg["ok"]}
    if not cfg["ok"]:
        out["problems"]=cfg["problems"]
        return jsonify(out),503
    if request.args.get("deep")=="1":
        try:
            sb_get("users",{"select":"id","limit":"1"})
            out["supabase_connected"]=True
        except Exception as e:
            out["ok"]=False;out["supabase_connected"]=False;out["problem"]=str(e)
            return jsonify(out),503
    return jsonify(out)

@app.post("/api/auth/request-otp")
def request_otp():
    d=request.get_json(force=True) or {};email=(d.get("email") or "").strip().lower();first=(d.get("first_name") or "").strip();country=(d.get("country") or "").strip();mode=(d.get("mode") or "signup").strip()
    if not email or "@" not in email:return jsonify({"ok":False,"error":"Enter a valid email address."}),400
    if mode=="signup" and (not first or not country):return jsonify({"ok":False,"error":"First name and country are required."}),400
    payload={"email":email,"create_user":mode=="signup"}
    if mode=="signup":payload["data"]={"first_name":first,"country":country}
    try:auth_post("otp",payload);return jsonify({"ok":True,"email":email})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),400

@app.post("/api/auth/verify-otp")
def verify_otp():
    d=request.get_json(force=True) or {};email=(d.get("email") or "").strip().lower();token=(d.get("token") or "").strip();guest_id=(d.get("guest_id") or "").strip()
    if not email or not token:return jsonify({"ok":False,"error":"Email and verification code are required."}),400
    try:
        data=auth_post("verify",{"email":email,"token":token,"type":"email"});user=data.get("user") or {};session=data.get("session") or data;uid=str(user.get("id") or "")
        if not uid:raise RuntimeError("Supabase did not return a user.")
        meta=user.get("user_metadata") or {};ensure_profile(uid,email=user.get("email") or email,first_name=meta.get("first_name"),country=meta.get("country"),tier="free");migrate_guest_data(guest_id,uid)
        return jsonify({"ok":True,"user":{"id":uid,"email":user.get("email"),"first_name":meta.get("first_name"),"country":meta.get("country")},"access_token":session.get("access_token"),"refresh_token":session.get("refresh_token"),"expires_in":session.get("expires_in",3600)})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),400

@app.post("/api/auth/refresh")
def refresh_auth():
    d=request.get_json(force=True) or {};rt=(d.get("refresh_token") or "").strip()
    if not rt:return jsonify({"ok":False,"error":"No refresh token."}),400
    try:
        data=auth_post("token?grant_type=refresh_token",{"refresh_token":rt});return jsonify({"ok":True,"access_token":data.get("access_token"),"refresh_token":data.get("refresh_token") or rt,"expires_in":data.get("expires_in",3600),"user":data.get("user")})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),401

@app.post("/api/auth/signout")
def signout_auth():
    token=bearer_token()
    if token:
        try:auth_post("logout",{},access_token=token)
        except Exception:pass
    return jsonify({"ok":True})

@app.post("/api/audio/speech")
def audio_speech():
    d=request.get_json(force=True) or {};text=(d.get("text") or "").strip();requested=(d.get("voice") or "lantern").strip();profile=d.get("profile") or {}
    if not text:return jsonify({"ok":False,"error":"No narration text."}),400
    if len(text)>3900:return jsonify({"ok":False,"error":"Narration segment is too long."}),400
    choice=profile.get("voice_choice") if requested=="lantern" else requested;voice=VOICE_FEMALE if choice=="female" else VOICE_MALE
    style=profile.get("audio_style") or "Tell this like a gifted human storyteller speaking to one person. Warm, intimate, restrained. Vary cadence naturally. Slow down at emotional turns. Use real pauses after important images and before the final lines. Never sound like an announcer, audiobook robot, advertisement, meditation cliché, or motivational speaker."
    style += " Target an unhurried conversational pace around 0.88x. Let punctuation breathe; do not rush paragraph endings."
    payload={"model":TTS_MODEL,"voice":voice,"input":text,"response_format":"mp3","speed":0.88,"instructions":style}
    try:
        r=requests.post("https://api.openai.com/v1/audio/speech",headers={"Authorization":f"Bearer {os.environ.get('OPENAI_API_KEY')}","Content-Type":"application/json"},json=payload,timeout=90)
        if not r.ok:
            detail=""
            try:detail=(r.json().get("error") or {}).get("message") or ""
            except Exception:pass
            raise RuntimeError(detail or f"TTS failed (HTTP {r.status_code}).")
        return Response(r.content,mimetype="audio/mpeg",headers={"Cache-Control":"private, max-age=3600"})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),503

@app.get("/api/audio/config")
def audio_config():
    return jsonify({"tts_model":TTS_MODEL,"voices":{"female":"Female","male":"Male","lantern":"Lantern's Choice"},"candidate_mapping":{"female":VOICE_FEMALE,"male":VOICE_MALE}})

@app.get("/api/me")
def me():
    uid=user_id()
    try:
        ensure_user(uid); ent=entitlement(uid)
        saved=sb_get("saved",{"user_id":f"eq.{uid}","select":"story_id,title,provenance,created","order":"created.desc"})
        recent=sb_get("recent",{"user_id":f"eq.{uid}","select":"story_id,title,provenance,created","order":"created.desc","limit":"20"})
        prefs=sb_get("prefs",{"user_id":f"eq.{uid}","select":"mode,voice,sound,faith,language,history"})
        p=prefs[0] if prefs else {"mode":"read","voice":"lantern","sound":True,"faith":"neutral","language":"English","history":True}
        profile_rows=sb_get("users",{"id":f"eq.{uid}","select":"email,first_name,country,tier"});profile=profile_rows[0] if profile_rows else {}
        return jsonify({"id":uid,"authenticated":bool(authenticated_user()),"profile":profile,"entitlement":ent,"saved":saved,"recent":recent,"prefs":p})
    except Exception as e:
        app.logger.exception("Lantern /api/me failed")
        return jsonify({"ok":False,"error":"Lantern could not load your account state.","detail":str(e)}),503

@app.post("/api/light")
def light():
    uid=user_id(); ensure_user(uid); data=request.get_json(force=True) or {}
    private=bool(data.get("just_this_moment"))
    ent=entitlement(uid)
    kind=data.get("experience_kind","full")
    allowed=ent["full_allowed"] if kind=="full" else ent["curated_allowed"]
    if not allowed:
        return jsonify({"status":"limit","kind":kind,"entitlement":ent})
    moment=(data.get("moment") or "").strip(); pathway=data.get("pathway"); recent=data.get("recent") or []
    profile=analyze(moment,pathway)
    if profile.get("clarify"):return jsonify({"status":"clarify","profile":profile,"question":profile.get("clarification_question")})
    cand,sc=retrieve(profile,recent)
    story=None; source=None
    if cand and sc>=6 and cand["id"] in BODIES:
        story={"id":cand["id"],"title":cand["title"],"provenance":cand["provenance"],"text":BODIES[cand["id"]],"landing":"return_to_life"};story["fingerprint"]=story_fingerprint(story["title"],story["text"]);source="retrieve"
    else:
        g=generate(moment or f"Selected pathway: {profile['pathway']}",profile)
        if g and quality(moment,profile,g["story"]):
            fp=story_fingerprint(g["title"],g["story"]); rt={str(x).lower() for x in (data.get("recent_titles") or [])}; rf=set(data.get("recent_fingerprints") or [])
            if fp in rf or str(g["title"]).lower() in rt:
                g2=generate(moment or f"Selected pathway: {profile['pathway']}",profile)
                if g2 and quality(moment,profile,g2["story"]): g=g2; fp=story_fingerprint(g["title"],g["story"])
            story={"id":"gen-"+uuid.uuid4().hex[:12],"title":g["title"],"provenance":"AN ORIGINAL LANTERN STORY","text":g["story"],"landing":g.get("landing","return_to_life"),"fingerprint":fp};source="generate"
            for k in ("voice_choice","audio_style","sound_palette","hook","visual_beats"):
                if g.get(k):profile[k]=g[k]
    if not story:
        cand,_=retrieve({"pathway":"Surprise Me","gravity":"low","tone":"curious","distance":"distant"},recent)
        if cand: story={"id":cand["id"],"title":cand["title"],"provenance":cand["provenance"],"text":BODIES[cand["id"]],"landing":"return_to_life"};story["fingerprint"]=story_fingerprint(story["title"],story["text"]);source="recovery"
    if not story:return jsonify({"status":"no_match","message":"I don't want to give this moment the wrong story.","cta":"Choose something for me"})
    now=time.time()
    consume(uid,kind,story["id"])
    if not private:
        sb_post("recent",{"user_id":uid,"story_id":story["id"],"title":story["title"],"provenance":story["provenance"],"text":story["text"],"created":now})
    return jsonify({"status":"story","source":source,"profile":profile,"story":story,
                    "entitlement":entitlement(uid)})

@app.get("/api/story-of-day")
def story_of_day():
    uid=user_id();ensure_user(uid); ent=entitlement(uid)
    day=int(time.time()//86400); item=VAULT[day%len(VAULT)]
    return jsonify({"entitlement":ent,"preview":{"id":item["id"],"title":item["title"],"provenance":item["provenance"],"pathway":item["pathway"]}})

@app.post("/api/save")
def save():
    uid=user_id();ensure_user(uid); d=request.get_json(force=True); s=d["story"]
    existing=sb_get("saved",{"user_id":f"eq.{uid}","story_id":f"eq.{s['id']}","select":"story_id"})
    payload={"user_id":uid,"story_id":s["id"],"title":s["title"],"provenance":s["provenance"],"text":s["text"],"created":time.time()}
    sb_patch("saved",payload,{"user_id":f"eq.{uid}","story_id":f"eq.{s['id']}"}) if existing else sb_post("saved",payload)
    return jsonify({"ok":True})

@app.post("/api/reflection")
def reflection():
    uid=user_id();ensure_user(uid); d=request.get_json(force=True)
    sb_post("reflections",{"user_id":uid,"story_id":d.get("story_id"),"text":d.get("text",""),"created":time.time()}); return jsonify({"ok":True})

@app.post("/api/resonance")
def resonance():
    uid=user_id();ensure_user(uid); d=request.get_json(force=True)
    sb_post("events",{"user_id":uid,"event":"resonance","story_id":d.get("story_id"),"rating":d.get("rating"),"created":time.time()}); return jsonify({"ok":True})

@app.post("/api/preferences")
def preferences():
    uid=user_id();ensure_user(uid); d=request.get_json(force=True)
    sb_patch("prefs",{"mode":d.get("mode","read"),"voice":d.get("voice","lantern"),"sound":bool(d.get("sound",True)),"faith":d.get("faith","neutral"),"language":d.get("language","English"),"history":bool(d.get("history",True))},{"user_id":f"eq.{uid}"}); return jsonify({"ok":True})

@app.post("/api/alpha/register")
def alpha_register():
    return jsonify({"ok":False,"error":"Legacy Alpha registration is disabled. Use verified email OTP."}),410

@app.post("/api/alpha/tier")
def alpha_tier():
    if not is_admin_request():return jsonify({"ok":False,"error":"admin_required"}),403
    uid=user_id();ensure_user(uid);d=request.get_json(force=True);tier="paid" if d.get("tier")=="paid" else "free";sb_patch("users",{"tier":tier},{"id":f"eq.{uid}"});return jsonify({"ok":True,"tier":tier})

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")),debug=False)
