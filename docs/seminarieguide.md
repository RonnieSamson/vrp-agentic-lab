# Seminariemanual: Så fungerar projektet steg för steg

Det här dokumentet är skrivet som ett stöd för ett seminarium där ni ska förklara hur hela systemet fungerar – från inläsning av tickets till agentens beslut och den efterföljande valideringen.

Målet är att beskriva workflowet i logisk ordning så att det blir lätt att följa både tekniskt och muntligt.

---

## 1. Syftet med projektet

Projektet visar ett agentiskt arbetsflöde för triagering av supportärenden i en webbshop/plattform för dykutrustning och dykrelaterade tjänster.

Med **triagering** menas att man snabbt sorterar och bedömer ett ärende för att avgöra vad det handlar om, om något saknas och vart det ska skickas vidare.

Det är alltså **inte** bara en vanlig chatbot som svarar direkt. I stället arbetar systemet som en liten controller som:

- läser in ett ärende
- bedömer vad som saknas
- använder verktyg vid behov
- sparar vad som redan har hänt i en trajectory
- fattar ett slutgiltigt beslut
- låter en validator kontrollera om beslutet följer affärsreglerna

Det här gör projektet bra att presentera i ett seminarium eftersom det tydligt visar skillnaden mellan:

- LLM-svar i ett steg
- agentisk problemlösning i flera steg

---

## 2. Den övergripande idén

Systemet jobbar med supporttickets som kan handla om till exempel:

- returer
- fakturafrågor
- leveransproblem
- service av utrustning
- kursbokningar
- dykresor

Varje ticket skickas in till agenten. Agenten avgör sedan om den behöver:

1. läsa en policy
2. kontrollera att obligatorisk information finns
3. avsluta med ett slutligt svar

Det viktigaste är att agenten arbetar steg för steg och använder den information som redan finns i sin trajectory för att undvika onödiga upprepningar.

Med trajectory menas alltså den löpande historiken över vad agenten har gjort i just det här ärendet.

---

## 3. Projektets byggstenar

För att förstå helheten är det bra att dela upp systemet i fyra huvuddelar.

### 3.1 `data/`

Här finns all indata som systemet använder.

- `data/tickets.json` – exempel på tickets som ska triageras
- `data/policies/` – textfiler med policyinformation för vissa ärendetyper

### 3.2 `app/`

Här ligger själva logiken.

- `main.py` – startar programmet och kör igenom alla tickets
- `agent.py` – innehåller agentloopen och beslutslogiken
- `tools.py` – enkla verktyg som agenten får använda
- `validator.py` – kontrollerar att beslutet följer reglerna
- `models.py` – datamodeller för tickets och agentbeslut

### 3.3 `trajectory`

Trajectory är agentens historik eller spår av vad som har hänt under ärendets gång. Man kan tänka på det som en logg över agentens steg.

Den innehåller exempelvis:

- modellens beslut
- verktygsanrop
- verktygsresultat
- finala svar
- fel om något går fel

Det här är viktigt eftersom agenten använder trajectory för att förstå vad som redan har gjorts och för att undvika att upprepa samma steg.

### 3.4 LLM-modellen

Agenten använder `ChatOllama` med modellen `llama3.1:8b` och `temperature=0`.

Det betyder i praktiken att modellen ska svara så stabilt och konsekvent som möjligt.

---

## 4. Flödet från start till slut

Här är hela systemets arbetsgång i rätt ordning.

### Steg 1: Programmet startas

I `app/main.py` läses alla tickets in från `data/tickets.json`.

För varje ticket körs sedan:

1. `run_agent(ticket)`
2. utskrift av slutgiltigt svar
3. utskrift av trajectory
4. validering via `validate_decision(...)`

Det betyder att `main.py` fungerar som projektets orkestrerare.

---

### Steg 2: Ticket-data läses in

Varje ticket innehåller typiskt:

- `id`
- `customer_name`
- `issue_type`
- `message`
- ibland `order_number`
- ibland `purchase_date`

Exempel på issue types i projektet:

- `return_request`
- `billing_issue`
- `shipping_issue`
- `service_request`
- `course_booking`
- `trip_booking`

Den här informationen blir grunden för hela triageringen.

---

### Steg 3: Agenten får en uppgift

När `run_agent(ticket)` anropas skapas en ny agentloop.

Agenten får:

- själva ticketen
- nuvarande stegnummer
- tidigare trajectory
- en maxgräns för hur många steg den får ta

Det betyder att agenten alltid arbetar i ett tydligt ramverk och inte kan fortsätta hur länge som helst.

---

### Steg 4: Systemprompt och state prompt byggs

Agenten konstruerar två delar av sin instruktion:

#### Systemprompt

Här står de övergripande reglerna för agenten:

- returnera endast JSON
- tillåtna actions är bara `tool` eller `final`
- tillåtna verktyg är bara `read_policy` och `check_required_fields`
- använd rätt policy-topic för rätt issue type
- undvik att upprepa samma onödiga verktygsanrop

#### State prompt

Här får modellen den aktuella situationen:

- vilket steg som körs
- hela ticketens innehåll
- vilken policy som hör till issue type
- hela trajectory hittills

Det här gör att modellen får både regler och kontext.

---

### Steg 5: Modellen returnerar ett JSON-beslut

Modellen ska svara i ett strikt JSON-format.

Ett beslut kan till exempel vara:

- att anropa `read_policy`
- att anropa `check_required_fields`
- att lämna ett slutgiltigt svar direkt

Om modellen skulle svara i fel format fångas detta upp av `parse_decision(...)`.

Då stoppas triageringen säkert med ett kontrollerat slut svar i stället för att krascha.

---

## 5. Hur agenten tänker i varje steg

Det här är kärnan i projektet och en bra del att förklara på seminariet.

### Steg 1: Kolla om tillräcklig information redan finns

Innan modellen ens får ta nästa beslut kontrollerar agenten om den redan har allt som behövs.

Funktionen `has_enough_information(...)` undersöker om:

- required fields är kontrollerade
- rätt policy har lästs, om det behövs

Om tillräcklig information finns, skapas direkt ett final answer.

---

### Steg 2: Om mer information behövs, fråga modellen om nästa åtgärd

Om agenten inte är färdig skickas kontexten till modellen.

Modellen väljer då mellan:

- `tool`
- `final`

Det här är själva agentbeteendet: den väljer nästa steg baserat på läget, inte bara på en enstaka prompt.

---

### Steg 3: Om modellen väljer ett verktyg, körs det lokalt

Två verktyg finns tillgängliga.

#### `read_policy(topic)`

Läser en policyfil från `data/policies/`.

Tillåtna topics är:

- `returns`
- `billing`
- `shipping`

Issue type mappas till rätt topic enligt:

- `return_request` → `returns`
- `billing_issue` → `billing`
- `shipping_issue` → `shipping`

#### `check_required_fields(ticket)`

Kontrollerar om obligatorisk information finns i ticketen.

Den letar bland annat efter:

- `id`
- `customer_name`
- `issue_type`
- `message`
- `order_number` för vissa ärendetyper

Om något saknas returneras exempelvis:

- `MISSING: order_number`

Om allt finns returneras:

- `OK: all required fields present`

---

### Steg 4: Resultatet läggs in i trajectory

När ett verktyg körs sparas resultatet i trajectory.

Det gör att agenten alltid kan se:

- vilket verktyg som redan har använts
- vilket svar det gav
- om samma verktyg redan har körts med samma input

Det här är viktigt för att undvika att agenten fastnar i samma loop.

---

### Steg 5: Dubblettskydd mot samma verktygsanrop

Funktionen `has_repeated_tool_call(...)` stoppar onödiga upprepningar.

Om modellen försöker använda exakt samma verktyg med samma input igen, blockeras detta.

Det gör systemet mer robust och visar tydligt att agenten minns vad som redan har gjorts.

---

### Steg 6: Saknad information avslutar ärendet tidigt

Det här är en viktig förbättring i projektet.

Om `check_required_fields(...)` ger ett svar som börjar med `MISSING:` så avslutas ärendet direkt med ett tydligt svar:

> Ärendet kan inte triageras: följande information saknas: ...

Det innebär att agenten inte försöker fortsätta när den saknar avgörande information.

Det här är bra att lyfta på seminariet eftersom det visar hur systemet hanterar robusthet och felkontroll.

---

### Steg 7: När allt som behövs finns, skapas ett slutgiltigt svar

När agenten har tillräcklig information anropas `build_final_answer(...)`.

Där skapas ett enkelt men tydligt svar, till exempel:

- att ärendet ska skickas till returns support
- att det ska skickas till billing support
- att det ska skickas till shipping support
- att det ska skickas till service support
- att det ska skickas till course administration
- att det ska skickas till trip booking support

Det slutliga svaret innehåller också att required fields har kontrollerats, och ibland att policy har granskats.

---

## 6. Varför vissa ärendetyper inte läser någon policy

Inte alla issue types har en egen policyfil.

För närvarande finns dedikerade policyfiler för:

- returns
- billing
- shipping

För dessa är det logiskt att agenten ibland behöver läsa policyn innan den kan avsluta.

För andra typer, som:

- `service_request`
- `course_booking`
- `trip_booking`

finns ingen särskild policyfil ännu.

Därför räcker det oftast att kontrollera required fields och sedan returnera ett slutligt beslut.

---

## 7. Exempel på hur ett ärende behandlas

### Exempel: en retur

Anta att ticketen har issue type `return_request`.

Då ser flödet ofta ut så här:

1. Agenten ser att det är ett returärende
2. Den kontrollerar obligatoriska fält
3. Den läser eventuell returpolicy
4. Den verifierar att all information finns
5. Den returnerar ett slutligt svar om att ärendet ska till returns support

### Exempel: ett ärende med saknat ordernummer

Om ett billing- eller returnärende saknar ordernummer:

1. `check_required_fields(...)` upptäcker felet
2. Agenten ser `MISSING: order_number`
3. Agenten avslutar med att information saknas
4. Ärendet triageras inte vidare, alltså att det inte sorteras eller skickas vidare till nästa steg förrän viktig information har kompletterats

Det här är ett tydligt exempel på hur agenten gör en säker stoppning i stället för att gissa.

---

## 8. Validering efter agentens beslut

När agenten är klar kör `main.py` också en separat kontroll med `validate_decision(...)`.

Valideraren är inte samma sak som agenten. Den fungerar som en efterkontroll som tittar på affärsregler.

### Exempel på regler som valideras

#### Returärenden

- får inte ligga utanför 30-dagarsfönstret
- måste ha ordernummer
- använd personlig utrustning som verkar använd/testad flaggas för manuell granskning

#### Billing-ärenden

- måste ha ordernummer

### Varför är valideringen viktig?

För att visa att systemet inte bara gör ett agentiskt beslut, utan också kan kontrolleras mot regler efteråt.

Detta skapar en tydlig separation mellan:

- agentens triagering
- regelbaserad kontroll

---

## 9. Vad som skrivs ut i konsolen

När programmet körs skrivs följande ut för varje ticket:

- Ticket ID
- Final Answer
- Trajectory i JSON-format
- eventuella valideringsfel

Det gör det enkelt att följa varje ärende från start till slut.

För ett seminarium är detta mycket bra eftersom ni kan visa:

- hur agenten tänkte
- vilka verktyg som användes
- vilket slutresultat som skapades
- om validatorn godkände beslutet

---

## 10. Bra berättelse att använda på seminariet

Om ni ska presentera projektet muntligt kan ni förklara det ungefär så här:

> Vi byggde ett agentiskt workflow för triagering av supportärenden i en dykshop. Systemet läser in en ticket, låter en LLM-agent välja nästa steg, använder lokala verktyg när information saknas, sparar allt i en trajectory och avslutar med ett tydligt svar. Efteråt körs en separat validator som kontrollerar att beslutet följer affärsreglerna.

Den här berättelsen visar tydligt:

- varför projektet är agentiskt
- hur verktyg används
- hur minne/trajectory fungerar
- hur robusthet säkerställs
- varför validering behövs

---

## 11. Kort sammanfattning

Om ni bara vill säga det allra viktigaste kan ni sammanfatta projektet så här:

1. Ticket laddas in
2. Agenten får kontext och regler
3. Modellen väljer nästa steg
4. Verktyg körs vid behov
5. Trajectory sparar allt som händer
6. Agenten avslutar när den har tillräckligt med information
7. Validatorn kontrollerar beslutet mot affärsregler

Det är hela systemets logik i rätt ordning.

---

## 12. Slutsats

Det här projektet visar ett tydligt exempel på hur en liten agent kan byggas upp från enkla komponenter:

- data
- verktyg
- promptstyrning
- trajectory
- finala beslut
- validering

Det gör projektet lätt att förstå, lätt att demonstrera och bra att använda i ett seminarium där ni vill förklara hur ett agentiskt workflow fungerar i praktiken.

---

## 13. Kort presentationsversion enligt uppgiftens krav

Om ni vill presentera projektet kortare på seminariet kan ni följa den här ordningen:

### 1. Task definition

- **Goal:** triagera supportärenden i en dykshop
- **Inputs:** ticket-data som id, ärendetyp, meddelande och ibland ordernummer eller köpdatum
- **Actions:** läsa policy, kontrollera obligatoriska fält och ge ett slutligt beslut
- **Rules:** använd bara tillåtna verktyg, undvik upprepningar och stoppa om viktig information saknas

### 2. Workflow architecture

- **Planner/controller:** `run_agent(...)` i `app/agent.py`
- **Tools:** `read_policy(...)` och `check_required_fields(...)`
- **State:** trajectory som sparar tidigare beslut och verktygsresultat
- **Validation:** `validate_decision(...)` som kontrollerar affärsregler efteråt

### 3. Hur tool use fungerar

- Agenten väljer om den ska använda ett verktyg eller ge ett final answer
- Verktygen körs lokalt i Python
- Resultaten sparas i trajectory
- Det behövs för att agenten ska kunna läsa policy och kontrollera saknad information innan den beslutar

### 4. Vad visar att workflowet fungerar bra

- Det kan köra ett ärende end-to-end
- Det producerar tydliga final answers
- Det hanterar saknad information utan att fortsätta på felaktiga grunder
- Validatorn hittar regler som ska flaggas, till exempel saknat ordernummer eller retur efter för lång tid
- Trajectory visar exakt vilka steg som togs

### 5. Begränsningar, failure modes och mitigations

- **Begränsning:** bara vissa issue types har dedikerad policy
- **Failure mode:** modellen kan ge fel JSON eller fel verktygsanrop
- **Mitigation:** `parse_decision(...)` stoppar ogiltig output och `has_repeated_tool_call(...)` blockerar upprepningar
- **Failure mode:** viktig information saknas i ticketen
- **Mitigation:** agenten avslutar tidigt med ett tydligt meddelande om saknad information

### 6. Kort muntlig sammanfattning

> Systemet tar emot en supportticket, låter en agent välja nästa steg, använder lokala verktyg för policy och fältkontroll, sparar allt i en trajectory och avslutar med ett beslut. Efteråt valideras beslutet mot affärsregler. Det visar ett komplett agentiskt workflow från input till kontrollerad output.

Den här korta versionen följer uppgiftens krav och passar bra om ni vill presentera projektet på 2–4 minuter.
