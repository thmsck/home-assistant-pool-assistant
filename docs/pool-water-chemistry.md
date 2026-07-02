# Poolwasser-Chemie: Bewertungsgrundlage

Dieses Dokument beschreibt die chemischen Zusammenhänge, Grenzwerte und
Bewertungslogik für den Pool Assistant. Ziel ist nicht, starre Pooltabellen
abzubilden, sondern die Messwerte so zu erklären, dass die Sensorlogik fachlich
prüfbar bleibt.

Der Pool Assistant ist ein Assistenzsystem. Er ersetzt weder lokale
Vorschriften noch Herstellerangaben oder die eigenverantwortliche Bewertung der
Wasserqualität.

## Wissenschaftlicher Status

Dieses Dokument unterscheidet bewusst zwischen:

- wissenschaftlich gut belegten chemischen Zusammenhängen
- praxisorientierten Empfehlungen für private Außenpools
- projektspezifischen Bewertungsregeln des Pool Assistant

Die Bewertungsbereiche sind deshalb keine gesetzlichen oder allgemein
verbindlichen Grenzwerte. Sie sind Arbeitsbereiche für ein Assistenzsystem, das
private, stabilisierte Außenpools nachvollziehbar bewerten soll.

## Quellen und Einordnung

Die Grenzwerte in diesem Dokument sind eine pragmatische Mischung aus
öffentlichen Richtwerten, typischer privater Poolpflege und den Anforderungen
des chemischen Modells.

- CDC Healthy Swimming nennt für private Pools typischerweise `1-4 ppm`
  Chlor und `pH 7.0-7.8`.
- Der CDC Model Aquatic Health Code 2024 nennt für öffentliche Anlagen
  `pH 7.0-7.8`, Maßnahmen ab `0.4 mg/l` gebundenem Chlor und keine Badenden
  bei freiem Chlor über `10 mg/l`.
- Der USEPA Free Chlorine and Cyanuric Acid Simulator und O'Brien et al.
  beschreiben das Gleichgewichtsmodell für Chlor, Cyanursäure und HOCl.

Für den Pool Assistant sind diese Quellen keine 1:1-Betriebsanweisung. Die
Integration bewertet einen privaten, stabilisierten Außenpool und soll früh
warnen, bevor Messwerte klar außerhalb sinnvoller Zielbereiche liegen.

## Begriffe

| Begriff | Bedeutung |
| --- | --- |
| `pH` | Maß für sauer/basisch. Beeinflusst direkt das Verhältnis von HOCl zu OCl⁻. |
| `Freies Chlor` | Messwert für frei verfügbares Chlor, in der Praxis meist DPD-FC als mg/l Cl₂. Enthält bei CYA nicht nur HOCl/OCl⁻, sondern auch reversible Chlor-Cyanurat-Spezies. |
| `Totales Chlor` | Freies Chlor plus gebundenes Chlor, meist DPD-TC als mg/l Cl₂. |
| `Gebundenes Chlor` | `Totales Chlor - freies Chlor`. Näherung für Chloramine und andere gebundene Chlorverbindungen. |
| `CYA` | Cyanursäure/Stabilisator. Schützt Chlor vor UV, bindet aber den größten Teil des freien Chlors reversibel. |
| `HOCl` | Hypochlorige Säure. Wichtigste wirksame Desinfektionsform von Chlor. |
| `OCl⁻` | Hypochlorit-Ion. Ebenfalls freies Chlor, aber deutlich weniger desinfektionswirksam als HOCl. |
| `Alkalinität` | Säurebindungsvermögen des Wassers. Stabilisiert den pH, ist aber kein Desinfektionsparameter. |

## Zentrale Zusammenhänge

### pH ↔ HOCl/OCl⁻

Chlor liegt im Wasser hauptsächlich als HOCl und OCl⁻ vor. Der pH entscheidet,
wie viel davon als HOCl vorhanden ist.

- Niedriger pH verschiebt das Gleichgewicht Richtung HOCl.
- Höherer pH verschiebt das Gleichgewicht Richtung OCl⁻.
- HOCl ist die wesentlich wirksamere Desinfektionsform.
- Zu niedriger pH kann Material angreifen und Haut/Augen reizen.
- Zu hoher pH reduziert die Desinfektionswirkung und begünstigt Trübungen oder
  Kalkprobleme.

Ohne CYA kann pH allein einen großen Teil der Chlorwirkung erklären. Mit CYA
reicht das nicht mehr aus, weil zusätzlich sehr viel Chlor reversibel an
Cyanurat gebunden ist.

### CYA ↔ freies Chlor ↔ HOCl

Cyanursäure schützt Chlor im Außenpool vor UV-Abbau. Gleichzeitig bindet CYA
einen großen Anteil des freien Chlors. Der PoolLab-Wert `freies Chlor` kann
dann hoch wirken, obwohl nur ein kleiner Anteil als HOCl aktiv vorliegt.

Beispielprinzip:

- `3.0 mg/l` freies Chlor ohne CYA kann viel aktives HOCl bedeuten.
- `3.0 mg/l` freies Chlor mit hohem CYA kann sehr wenig aktives HOCl bedeuten.

Deshalb bewertet der Pool Assistant nicht nur `freies Chlor`, sondern berechnet
HOCl aus pH, freiem Chlor, CYA und Temperatur.

### Freies Chlor ↔ totales Chlor ↔ gebundenes Chlor

Gebundenes Chlor wird im Projekt als Differenz berechnet:

```text
gebundenes Chlor = totales Chlor - freies Chlor
```

Diese Differenz ist keine perfekte chemische Speziesanalyse, aber praktisch
wichtig:

- Niedriges gebundenes Chlor spricht für wenig Chloramine/Belastung.
- Erhöhtes gebundenes Chlor spricht für verbrauchtes Chlor, organische Last,
  Chloramine oder Mess-/Zeitpunktprobleme.
- Wenn `totales Chlor < freies Chlor`, ist der Messsatz chemisch unplausibel.
  Dann sollten Messwerte oder Messzeitpunkte geprüft werden.

Gebundenes Chlor sollte nicht direkt als Algenrisiko interpretiert werden. Es
ist eher ein Hygiene-/Belastungsindikator. Algenrisiko sollte primär aus HOCl,
CYA, pH und Messqualität abgeleitet werden.

### Alkalinität ↔ pH-Stabilität

Alkalinität ist der Puffer des Wassers.

- Zu niedrige Alkalinität: pH kann stark schwanken, Dosierung wird instabil.
- Zu hohe Alkalinität: pH steigt oft wieder an, pH-Senkung wird träge, Kalk- und
  Trübungsneigung steigt.
- Eine gute Alkalinität macht pH-Regelung einfacher, ersetzt aber keine
  ausreichende Desinfektion.

Alkalinität sollte deshalb im Pool Assistant bewertet werden, aber geringer
gewichtet sein als HOCl und Messqualität.

## Empfohlene Bewertungsbereiche

Diese Bereiche sind Arbeitswerte für den Pool Assistant. Sie sind bewusst
konservativ genug, um Handlungshinweise zu erzeugen, ohne jeden kleinen
Messfehler sofort kritisch zu bewerten.

### pH

| Bereich | Bewertung | Bedeutung |
| --- | --- | --- |
| `< 6.8` | kritisch | Material-/Komfortproblem, Messung prüfen, pH anheben. |
| `6.8-7.0` | niedrig | Chlorwirkung hoch, aber pH außerhalb Zielbereich. |
| `7.0-7.2` | nutzbar | Unterer Rand, beobachten. |
| `7.2-7.4` | optimal | Gute Desinfektionswirkung und guter Komfort. |
| `7.4-7.6` | gut | Meist unproblematisch. |
| `7.6-7.8` | erhöht | Chlorwirkung sinkt, beobachten oder pH senken. |
| `7.8-8.0` | deutlich erhöht | Desinfektionswirkung reduziert, pH senken. |
| `> 8.0` | kritisch | Chlorwirkung deutlich reduziert, Kalk-/Trübungsrisiko. |

### Cyanursäure

| Bereich | Bewertung | Bedeutung |
| --- | --- | --- |
| `0-10 mg/l` | niedrig | Wenig UV-Schutz, Chlor wird im Außenpool schnell abgebaut. |
| `10-20 mg/l` | brauchbar | Etwas Stabilisierung, aber noch wenig Reserve. |
| `20-50 mg/l` | Zielbereich | Guter Kompromiss aus UV-Schutz und Chlorwirkung. |
| `50-70 mg/l` | erhöht | Noch handhabbar, aber höherer Chlorbedarf. |
| `70-90 mg/l` | hoch | Chlor zunehmend stark gebunden, Wasserwechsel prüfen. |
| `90-120 mg/l` | sehr hoch | Organisches Chlor vermeiden, Verdünnung planen. |
| `> 120 mg/l` | kritisch | Desinfektionsbewertung stark belastet, Wasserwechsel wahrscheinlich sinnvoll. |

Wichtig: Hoher CYA ist nicht durch pH-Minus oder mehr Filterlaufzeit lösbar.
Praktisch sinkt CYA nur durch Verdünnung/Wasserwechsel oder Wasserverlust mit
Frischwasserzugabe.

### HOCl

Die HOCl-Bewertung orientiert sich an Arbeitsbereichen des Projekts. Sie
basieren auf veröffentlichten Gleichgewichtsmodellen und dem Abgleich mit
PoolLab-App-Ausgaben. Sie sind keine gesetzlichen oder allgemein verbindlichen
Grenzwerte.

| Bereich | Bewertung | Bedeutung |
| --- | --- | --- |
| `< 0.016 mg/l` | rot/kritisch | Desinfektionsleistung wahrscheinlich zu gering. |
| `0.016-0.05 mg/l` | gelb/begrenzt | Tötet einige Algen/Bakterien, aber nicht Zielbereich. |
| `> 0.05 mg/l` | grün/wirksam | Gute aktive Chlorverfügbarkeit. |

HOCl ist der wichtigste Wert für die Desinfektionsbewertung. Ein hoher Wert an
freiem Chlor ist nur dann positiv, wenn daraus auch ausreichend HOCl entsteht.

### Freies Chlor

Freies Chlor ist weiterhin wichtig, aber ohne CYA-Kontext nicht ausreichend.

| Bereich | Bewertung | Bedeutung |
| --- | --- | --- |
| `< 1.0 mg/l` | niedrig | Häufig zu wenig Reserve, besonders bei Badebetrieb/Sonne. |
| `1.0-4.0 mg/l` | typischer Bereich | Öffentlicher CDC-Orientierungswert für private Pools. |
| `4.0-8.0 mg/l` | erhöht | Kann bei CYA nötig sein, sollte über HOCl bewertet werden. |
| `8.0-10.0 mg/l` | hoch | Nicht weiter chloren, Ursache/Zielwert prüfen. |
| `> 10.0 mg/l` | kritisch | Bei öffentlichen Anlagen keine Badenden; im privaten Pool ebenfalls sehr vorsichtig bewerten. |

Für stabilisierte Außenpools ist ein starres Ziel wie `1-3 mg/l` fachlich
schwach, wenn CYA stark schwankt. Besser ist:

```text
freies Chlor so wählen, dass HOCl im Zielbereich liegt
```

und zusätzlich einen plausiblen Sicherheitsrahmen für freies Chlor beachten.

### Totales und gebundenes Chlor

| Gebundenes Chlor | Bewertung | Bedeutung |
| --- | --- | --- |
| `0.0-0.2 mg/l` | gut | Unauffällig. |
| `0.2-0.4 mg/l` | leicht erhöht | Beobachten, Filterlauf/Badebelastung prüfen. |
| `0.4-0.6 mg/l` | erhöht | Maßnahmen sinnvoll; MAHC nennt Maßnahmen ab `0.4 mg/l`. |
| `> 0.6 mg/l` | hoch | Zeitnah handeln: Messung bestätigen, oxidieren, Filter betreiben, ggf. Wasser tauschen. |

Wenn gebundenes Chlor hoch ist, sollte der Poolstatus schlechter werden. Das
sollte aber nicht automatisch `Algenrisiko hoch` bedeuten, wenn HOCl ausreichend
ist.

### Alkalinität

| Bereich | Bewertung | Bedeutung |
| --- | --- | --- |
| `< 30 mg/l` | kritisch niedrig | pH sehr instabil. |
| `30-50 mg/l` | niedrig | pH-Schwankungen wahrscheinlich. |
| `50-70 mg/l` | leicht niedrig | Beobachten, je nach pH-Verhalten korrigieren. |
| `70-120 mg/l` | Zielbereich | Gute pH-Pufferung. |
| `120-150 mg/l` | erhöht | pH kann träge oder steigend sein. |
| `150-180 mg/l` | hoch | pH-Korrektur erschwert, Kalkrisiko steigt. |
| `> 180 mg/l` | sehr hoch | Wasserbalance prüfen, Korrektur planen. |

## Bewertungslogik im Pool Assistant

Die Bewertung sollte in getrennten Teilurteilen erfolgen:

1. Messqualität
2. Desinfektionsleistung
3. Algenrisiko
4. Wasserbalance
5. Belastung/Chloramine
6. Gesamtstatus

### Messqualität

Ein chemisches Modell ist nur sinnvoll, wenn die Eingangswerte aus derselben
Messreihe stammen.

Empfohlene Regeln:

- `current`: relevante Werte sind aktuell und synchron genug.
- `unsynced`: Werte stammen aus zu unterschiedlichen Messzeitpunkten.
- `stale`: mindestens ein wichtiger Messwert ist zu alt.
- Unplausibel: `totales Chlor < freies Chlor`.

Bei `unsynced`, `stale` oder unplausiblen Chlorwerten sollte keine konkrete
Dosierempfehlung gegeben werden. Stattdessen sollte zuerst eine neue Messreihe
angefordert werden.

### Desinfektionsstatus

Der Desinfektionsstatus sollte primär aus HOCl kommen:

| HOCl | Status |
| --- | --- |
| `< 0.016 mg/l` | `critical` |
| `0.016-0.05 mg/l` | `limited` |
| `> 0.05 mg/l` | `effective` |

Freies Chlor sollte als Kontroll- und Reservewert angezeigt werden, aber nicht
allein den Status bestimmen.

### Chemisches Algenrisiko

Der Pool Assistant bewertet derzeit kein vollständiges biologisches
Algenrisiko, sondern ausschließlich das chemische Algenrisiko. Algenwachstum
wird zusätzlich durch Faktoren beeinflusst, die aktuell noch nicht im Modell
enthalten sind.

Aktuell berücksichtigt werden:

- HOCl
- pH
- Cyanursäure
- Messqualität

Derzeit nicht berücksichtigt werden beispielsweise:

- Wassertemperatur als Wachstumsfaktor
- UV-Belastung
- Filterlaufzeit
- Umwälzrate
- organische Belastung
- Badebetrieb

Gebundenes Chlor sollte hier nicht primär gewertet werden. Es beschreibt eher
Belastung/Chloramine als fehlende Algenprävention.

Empfohlene Logik:

| Bedingung | Risiko |
| --- | --- |
| `stale`, `HOCl < 0.010`, `CYA > 120`, `pH > 8.0`, unplausible Chlormessung | `critical` |
| `unsynced`, `HOCl < 0.016`, `CYA > 90`, `pH > 7.8` | `high` |
| `HOCl < 0.05`, `CYA > 70`, `pH > 7.6` | `medium` |
| sonst | `low` |

### Belastungsstatus / gebundenes Chlor

Gebundenes Chlor sollte separat bewertet werden:

| Bedingung | Status |
| --- | --- |
| `totales Chlor < freies Chlor` | Messwerte prüfen |
| `gebundenes Chlor <= 0.2` | unauffällig |
| `0.2-0.4` | leicht erhöht |
| `0.4-0.6` | erhöht |
| `> 0.6` | hoch |

Dieser Status darf den Gesamtstatus verschlechtern, sollte aber nicht allein
das Algenrisiko erhöhen.

### Poolchemie-Index

Der Index sollte kein Gesundheitsversprechen sein. Er ist ein technischer
Qualitätsindex der Wasserchemie.

Empfohlene Gewichtung:

| Teilscore | Gewicht |
| --- | --- |
| HOCl/Desinfektion | `35 %` |
| pH | `20 %` |
| CYA | `15 %` |
| Messqualität | `10 %` |
| Alkalinität | `10 %`, wenn vorhanden |
| Gebundenes Chlor/Plausibilität | `10 %`, wenn vorhanden |

Wenn ein optionaler Wert fehlt, sollte sein Gewicht entfernt und nicht als `0`
gewertet werden.

### Gesamtstatus

Der Poolstatus ist die menschliche Kurzfassung. Er sollte die wichtigsten
Blocker priorisieren:

1. Messwerte veraltet
2. Messwerte nicht synchron
3. Messwerte unplausibel
4. Kritische Desinfektion oder kritisches Algenrisiko
5. Hohe Chloramine/gebundenes Chlor
6. Erhöhte, aber nicht kritische Werte
7. Alles im Zielbereich

Vorschlag:

| Status | Bedeutung |
| --- | --- |
| `Messwerte veraltet` | Erst neu messen, keine Dosierempfehlung. |
| `Messwerte nicht synchron` | Werte stammen nicht aus derselben Messreihe. |
| `Messwerte prüfen` | Chlorwerte sind chemisch unplausibel. |
| `Kritisch` | Desinfektion/Algenrisiko oder Wasserchemie kritisch. |
| `Handlungsbedarf` | Zeitnah korrigieren, aber nicht akut kritisch. |
| `Beobachten` | Nutzbar, aber Entwicklung prüfen. |
| `Gut` | Im Zielbereich mit kleinen Abweichungen. |
| `Perfekt` | Alle Kernwerte im Zielbereich. |

## Handlungsempfehlungen nach Ursache

Der Sensor `Handlungsempfehlung` fasst die wichtigsten Ursachen in eine
priorisierte Aktionsliste zusammen. Messqualität blockiert dabei konkrete
Dosierhinweise: Bei veralteten, unsynchronen oder unplausiblen Messwerten wird
zuerst eine neue Messreihe empfohlen.

Erst wenn die Messwerte plausibel sind, werden konkrete chemische Ursachen
ausgegeben, z. B. zu wenig HOCl, erhöhter pH, hoher CYA, erhöhte Alkalinität
oder erhöhtes gebundenes Chlor.

### HOCl zu niedrig

- Neue Messung prüfen, wenn Werte alt oder unsynchron sind.
- pH prüfen und ggf. zuerst senken, wenn pH erhöht ist.
- Freies Chlor erhöhen, wenn pH und CYA plausibel sind.
- Bei hohem CYA nicht nur Chlor nachkippen, sondern CYA reduzieren.

### CYA zu hoch

- Kein weiteres organisches/stabilisiertes Chlor verwenden.
- Auf anorganisches Chlor wechseln, wenn Chlor dosiert werden muss.
- Wasser teilweise tauschen oder durch Rückspülen/Frischwasser verdünnen.
- Zielbereich wieder Richtung `20-50 mg/l` bringen.

### pH zu hoch

- pH-Minus/Säure nach Herstellerangabe dosieren.
- Nach Umwälzung erneut messen.
- TA prüfen, wenn pH immer wieder ansteigt.

### pH zu niedrig

- Keine weitere Säure dosieren.
- pH anheben.
- TA prüfen, wenn pH instabil ist.

### Gebundenes Chlor zu hoch

- Freies und totales Chlor in derselben Messreihe bestätigen.
- Badebelastung, organische Belastung und Filterzustand prüfen.
- Oxidieren/Schockchlorung nach Produktangabe erwägen.
- Filter lange laufen lassen, ggf. rückspülen oder Wasser teilweise tauschen.

### Alkalinität außerhalb Zielbereich

- Bei niedriger TA: pH-Stabilität beobachten und TA anheben, wenn pH springt.
- Bei hoher TA: pH-Korrekturen werden träger; langsame Senkung über pH-Steuerung
  und Wasserwechsel prüfen.

## Designregel für die Implementierung

Gebundenes Chlor wird nicht direkt in das chemische Algenrisiko eingerechnet.
Fachlich beschreibt es eher Belastung, Chloramine oder Messprobleme als
fehlende Algenprävention.

Die Implementierung folgt deshalb dieser Trennung:

- Algenrisiko nur aus HOCl, CYA, pH und Messqualität ableiten.
- Gebundenes Chlor separat als Belastungs-/Chloraminstatus führen.
- Gesamtstatus darf bei hohem gebundenem Chlor trotzdem `Handlungsbedarf`
  werden.

Damit bleibt die Aussage präziser:

```text
Nicht:  Algenrisiko hoch, weil gebundenes Chlor hoch ist.
Sondern: Desinfektion wirksam, aber gebundenes Chlor hoch → Handlungsbedarf.
```

## Referenzen

- CDC: Guidelines for Keeping Your Pool Safe and Healthy  
  https://www.cdc.gov/healthy-swimming/safety/what-you-can-do-to-stay-healthy-in-swimming-pools.html
- CDC: 2024 Model Aquatic Health Code, Code Language, 5th Edition  
  https://www.cdc.gov/model-aquatic-health-code/media/pdfs/2024/11/5th-Ed-MAHC-Code-508.pdf
- USEPA: Free Chlorine and Cyanuric Acid Simulator manual  
  https://usepaord.shinyapps.io/cyanuric/_w_ab89cb9537e14344abd0296f1c027566/manual.pdf
- O'Brien et al.: Equilibria in aqueous solutions of chlorinated isocyanurate  
  https://labcom.cloud/resources/obrien.pdf
