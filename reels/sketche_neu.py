"""Einmalig: Comic-Sketch-Serie in reels/warteschlange.json eintragen (Sonder-Reels mit Uhrzeit).
Neue Sketche sind gesperrt ("freigegeben": false), bis der Inhaber sie gesehen und freigegeben hat.
Der WLAN-Sketch wurde vom Inhaber bereits abgenommen."""
import json
import os

Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warteschlange.json")
TAGS = "#jobwechsel #bewerbung #arbeitsleben #schwarzwald #personalvermittlung"


def L(wer, text, sprich=None, **kw):
    x = dict(wer=wer, text=text, sprich=sprich or text, augen="normal", ruhe="neutral",
             arm="tisch" if wer == "personaler" else "handy")
    x.update(kw)
    return x


def cap(suche, frage):
    return (f"{suche}\n\nKennst du das? Ein Zeichentrick-Sketch von Inpernell, deiner Personalvermittlung im Schwarzwald. "
            f"Direktvermittlung in Festanstellung, für dich kostenlos.\n\n{frage}\n\nTop Jobs aus der Region: Link in der Bio."
            f"\n\n{TAGS}")


SKETCHE = [
    dict(id="2026-11-25-sketch-genz-wlan", datum="2026-11-25", zeit="12:00", freigegeben=True,
         thema="Sketch: Gen Z sucht einen Job",
         caption=cap("Wie es sich anfühlt, als Gen Z einen Job zu suchen 😅",
                     "Was war die ehrlichste Antwort, die du je im Vorstellungsgespräch gegeben hast?"),
         fertig_video="reels/fertig/2026-11-25-sketch-genz-wlan.mp4",
         fertig_titelbild="reels/fertig/2026-11-25-sketch-genz-wlan.jpg"),
    dict(id="2026-11-28-sketch-bewerbung-1995", datum="2026-11-28", zeit="11:00", freigegeben=False,
         thema="Sketch: Bewerbung früher und heute",
         caption=cap("Bewerbung früher vs. heute: Wenn der Chef von damals erzählt 📮",
                     "Wie lange hast du schon mal auf eine Antwort auf deine Bewerbung gewartet?"),
         sketch=dict(titel="Wie es sich anfühlt, wenn der Chef von früher erzählt",
                     abspann="Bewerben geht heute schneller. Zum Beispiel per DM an uns.",
                     dialog=[
                         L("personaler", "Früher haben wir Bewerbungen noch per Post geschickt.",
                           "[nostalgic] Früher haben wir Bewerbungen noch per Post geschickt."),
                         L("genz", "Per was?", "[confused] Per was?", augen="gross", brauen="hoch", vor=0.5),
                         L("personaler", "Per Post. Mit Briefmarke und Foto vom Fotografen.",
                           "[proud] Per Post. Mit Briefmarke und Foto vom Fotografen.", ruhe="grinsen"),
                         L("genz", "Und wie lange hat die Antwort gedauert?",
                           "[skeptical] Und wie lange hat die Antwort gedauert?", augen="muede"),
                         L("personaler", "Sechs Wochen.", "[matter-of-fact] Sechs Wochen.", ruhe="grinsen", vor=0.5),
                         L("genz", "Ich hab schon gekündigt, weil nach vier Stunden keiner geantwortet hat.",
                           "[deadpan] Ich hab schon gekündigt, weil nach vier Stunden keiner geantwortet hat.",
                           augen="genervt", ruhe="schief", arm="achselzucken", fx="fragezeichen", sfx_vor="grillen",
                           vor=1.2, nach=1.3, sfx_nach="badumtss")])),
    dict(id="2026-12-02-sketch-staerken", datum="2026-12-02", zeit="12:00", freigegeben=False,
         thema="Sketch: Deine Stärken",
         caption=cap("Was sind deine Stärken? Die ehrlichste Antwort im Vorstellungsgespräch 💼",
                     "Welche Stärke schreibst du in jede Bewerbung?"),
         sketch=dict(titel="Wie es sich anfühlt, im Gespräch ehrlich zu sein",
                     abspann="Ehrlich hilft. Den passenden Job finden wir trotzdem.",
                     dialog=[
                         L("personaler", "Was sind deine Stärken?", "[professional] Was sind deine Stärken?"),
                         L("genz", "Ich bin sehr gut im Multitasking.", "[confident] Ich bin sehr gut im Multitasking.",
                           ruhe="grinsen"),
                         L("personaler", "Zum Beispiel?", "[curious] Zum Beispiel?", augen="gross", brauen="hoch"),
                         L("genz", "Ich kann gleichzeitig im Meeting sein und nicht zuhören.",
                           "[deadpan] Ich kann gleichzeitig im Meeting sein und nicht zuhören.", augen="muede", vor=0.6),
                         L("personaler", "Du passt perfekt ins Management.", "[impressed] Du passt perfekt ins Management.",
                           augen="gross", ruhe="grinsen", arm="tisch_hoch", brauen="hoch", fx="speedlines",
                           sfx_vor="grillen", vor=1.3, pointe=True, nach=1.3, sfx_nach="badumtss")])),
    dict(id="2026-12-05-sketch-faxgeraet", datum="2026-12-05", zeit="11:00", freigegeben=False,
         thema="Sketch: Arbeitgeber aus den 80ern",
         caption=cap("Wenn der Arbeitgeber noch in den 80ern lebt 📠",
                     "Was ist der älteste Benefit, den dir je ein Arbeitgeber angeboten hat?"),
         sketch=dict(titel="Wie es sich anfühlt, wenn der Arbeitgeber noch in den 80ern lebt",
                     abspann="Wir finden Arbeitgeber, die im Jahr 2026 angekommen sind.",
                     dialog=[
                         L("personaler", "Wir bieten Obstkorb, Kicker und ein Faxgerät.",
                           "[proud] Wir bieten Obstkorb, Kicker und ein Faxgerät.", ruhe="grinsen"),
                         L("genz", "Ein was?", "[confused] Ein was?", augen="gross", brauen="hoch", vor=0.5),
                         L("personaler", "Ein Faxgerät. Ganz neu. Mit Papierrolle.",
                           "[excited] Ein Faxgerät. Ganz neu. Mit Papierrolle.", ruhe="grinsen", arm="tisch_hoch"),
                         L("genz", "Und gibt es Homeoffice?", "[hopeful] Und gibt es Homeoffice?"),
                         L("personaler", "Klar. Du darfst das Faxgerät mit nach Hause nehmen.",
                           "[generous] Klar. Du darfst das Faxgerät mit nach Hause nehmen.", ruhe="grinsen",
                           arm="tisch_hoch", fx="speedlines", vor=0.6, pointe=True),
                         L("genz", "Ich glaube, ich muss los.", "[flat] Ich glaube, ich muss los.", augen="genervt",
                           ruhe="schief", arm="achselzucken", fx="fragezeichen", sfx_vor="grillen", vor=1.2, nach=1.3,
                           sfx_nach="badumtss")])),
    dict(id="2026-12-09-sketch-gehalt", datum="2026-12-09", zeit="12:00", freigegeben=False,
         thema="Sketch: Gehaltsvorstellung",
         caption=cap("Was stellst du dir beim Gehalt vor? Gen Z antwortet ehrlich 💶",
                     "Welche Zahl nennst du, wenn du nach deiner Gehaltsvorstellung gefragt wirst?"),
         sketch=dict(titel="Wie es sich anfühlt, nach dem Gehalt gefragt zu werden",
                     abspann="Was ist drin? Wir sagen es dir ehrlich. Kostenlos.",
                     dialog=[
                         L("personaler", "Was stellst du dir beim Gehalt vor?",
                           "[professional] Was stellst du dir beim Gehalt vor?"),
                         L("genz", "Mehr.", "[confident] Mehr.", ruhe="grinsen", vor=0.5),
                         L("personaler", "Mehr als was?", "[confused] Mehr als was?", augen="gross", brauen="skeptisch"),
                         L("genz", "Mehr als jetzt.", "[obvious] Mehr als jetzt.", augen="muede"),
                         L("personaler", "Und was verdienst du jetzt?", "[cautious] Und was verdienst du jetzt?",
                           brauen="sorge"),
                         L("genz", "Nichts. Deshalb ja.", "[deadpan] Nichts. Deshalb ja.", augen="genervt", ruhe="schief",
                           arm="achselzucken", fx="fragezeichen", sfx_vor="grillen", vor=1.2, nach=1.3,
                           sfx_nach="badumtss")])),
]

if __name__ == "__main__":
    q = json.load(open(Q, encoding="utf-8"))
    vorhanden = {r["id"] for r in q}
    for sk in SKETCHE:
        if sk["id"] not in vorhanden:
            q.append(sk)
    json.dump(q, open(Q, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(Q, "a").write("\n")
    print("eingetragen:", [s["id"] for s in SKETCHE if s["id"] not in vorhanden])
