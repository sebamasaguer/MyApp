import json
from datetime import date

_VERSES = [
    ("Jeremías 29:11", "Porque yo sé los planes que tengo para ustedes, planes de bienestar y no de calamidad, para darles un futuro y una esperanza."),
    ("Filipenses 4:13", "Todo lo puedo en Cristo que me fortalece."),
    ("Josué 1:9", "Sé fuerte y valiente. No temas ni te desanimes, porque el Señor tu Dios estará contigo dondequiera que vayas."),
    ("Salmos 118:24", "Este es el día que hizo el Señor; nos gozaremos y alegraremos en él."),
    ("Proverbios 3:5-6", "Confía en el Señor con todo tu corazón y no te apoyes en tu propio entendimiento. Reconócelo en todos tus caminos y él allanará tus sendas."),
    ("Mateo 6:34", "No se angustien por el mañana, el cual tendrá sus propios afanes. Cada día tiene ya sus problemas."),
    ("Isaías 40:31", "Los que confían en el Señor renovarán sus fuerzas; volarán como las águilas, correrán y no se fatigarán, caminarán y no se cansarán."),
    ("Salmos 23:1", "El Señor es mi pastor, nada me faltará."),
    ("Salmos 46:1", "Dios es nuestro amparo y fortaleza, nuestro pronto auxilio en las tribulaciones."),
    ("Salmos 27:1", "El Señor es mi luz y mi salvación; ¿a quién temeré? El Señor es la fortaleza de mi vida; ¿de quién he de atemorizarme?"),
    ("Salmos 37:4", "Deléitate en el Señor, y él te concederá las peticiones de tu corazón."),
    ("Salmos 55:22", "Encomienda al Señor tus cargas, y él te sustentará; no permitirá jamás que el justo caiga."),
    ("Salmos 121:1-2", "Alzo mis ojos a los montes; ¿de dónde vendrá mi socorro? Mi socorro viene del Señor, que hizo los cielos y la tierra."),
    ("Salmos 143:8", "Hazme oír por la mañana tu misericordia, porque en ti he confiado; hazme saber el camino por donde he de andar."),
    ("Salmos 5:3", "Oye, Señor, mi voz por la mañana; de mañana me presentaré delante de ti, y esperaré."),
    ("Salmos 90:14", "Sácianos por la mañana con tu misericordia, y cantaremos y nos alegraremos todos nuestros días."),
    ("Salmos 34:8", "Gustad y ved que el Señor es bueno; dichoso el que en él se refugia."),
    ("Salmos 138:8", "El Señor cumplirá su propósito en mí; tu misericordia, oh Señor, es para siempre."),
    ("Proverbios 16:3", "Encomienda al Señor tus obras, y tus pensamientos serán afirmados."),
    ("Proverbios 16:9", "El corazón del hombre traza su camino, pero el Señor dirige sus pasos."),
    ("Proverbios 18:10", "Torre fuerte es el nombre del Señor; a él correrá el justo y estará a salvo."),
    ("Eclesiastés 3:1", "Todo tiene su tiempo, y todo lo que se quiere debajo del cielo tiene su hora."),
    ("Isaías 41:10", "No temas, porque yo estoy contigo; no desmayes, porque yo soy tu Dios que te esfuerzo; siempre te ayudaré, siempre te sustentaré con la diestra de mi justicia."),
    ("Isaías 26:3", "Tú guardarás en completa paz a aquel cuyo pensamiento en ti persevera, porque en ti ha confiado."),
    ("Isaías 43:2", "Cuando pases por las aguas, yo estaré contigo; y si por los ríos, no te anegarán."),
    ("Lamentaciones 3:22-23", "Por la misericordia del Señor no hemos sido consumidos, porque nunca decayeron sus misericordias. Nuevas son cada mañana; grande es tu fidelidad."),
    ("Habacuc 3:19", "Jehová el Señor es mi fortaleza, el cual hace mis pies como de ciervas, y en mis alturas me hace andar."),
    ("Sofonías 3:17", "El Señor está en medio de ti, poderoso, él salvará; se gozará sobre ti con alegría."),
    ("Mateo 6:33", "Buscad primeramente el reino de Dios y su justicia, y todas estas cosas os serán añadidas."),
    ("Mateo 7:7", "Pedid, y se os dará; buscad, y hallaréis; llamad, y se os abrirá."),
    ("Marcos 11:24", "Todo lo que pidiereis orando, creed que lo recibiréis, y os vendrá."),
    ("Lucas 1:37", "Porque nada hay imposible para Dios."),
    ("Juan 14:27", "La paz os dejo, mi paz os doy; yo no os la doy como el mundo la da. No se turbe vuestro corazón, ni tenga miedo."),
    ("Juan 16:33", "En el mundo tendréis aflicción; pero confiad, yo he vencido al mundo."),
    ("Romanos 8:28", "Sabemos que a los que aman a Dios, todas las cosas les ayudan a bien."),
    ("Romanos 8:31", "Si Dios es por nosotros, ¿quién contra nosotros?"),
    ("Romanos 12:2", "No os conforméis a este siglo, sino transformaos por medio de la renovación de vuestro entendimiento."),
    ("Romanos 15:13", "El Dios de esperanza os llene de todo gozo y paz en el creer, para que abundéis en esperanza."),
    ("1 Corintios 10:13", "No os ha sobrevenido ninguna tentación que no sea humana; pero fiel es Dios, que no os dejará ser tentados más de lo que podéis resistir."),
    ("1 Corintios 16:13", "Velad, estad firmes en la fe; portaos varonilmente, y esforzaos."),
    ("2 Corintios 4:16", "Aunque el hombre exterior se va desgastando, el interior no obstante se renueva de día en día."),
    ("2 Corintios 5:17", "Si alguno está en Cristo, nueva criatura es; las cosas viejas pasaron; he aquí todas son hechas nuevas."),
    ("2 Corintios 12:9", "Bástate mi gracia, porque mi poder se perfecciona en la debilidad."),
    ("Gálatas 6:9", "No nos cansemos de hacer bien, porque a su tiempo segaremos, si no desmayamos."),
    ("Efesios 2:10", "Somos hechura suya, creados en Cristo Jesús para buenas obras."),
    ("Efesios 3:20", "Poderoso es Dios para hacer todas las cosas mucho más abundantemente de lo que pedimos o entendemos."),
    ("Filipenses 4:6", "Por nada estéis afanosos, sino sean conocidas vuestras peticiones delante de Dios en toda oración."),
    ("Filipenses 4:19", "Mi Dios suplirá todo lo que os falta conforme a sus riquezas en gloria en Cristo Jesús."),
    ("Colosenses 3:23", "Todo lo que hagáis, hacedlo de corazón, como para el Señor y no para los hombres."),
    ("1 Tesalonicenses 5:16-18", "Estad siempre gozosos. Orad sin cesar. Dad gracias en todo, porque esta es la voluntad de Dios para con vosotros en Cristo Jesús."),
    ("2 Timoteo 1:7", "No nos ha dado Dios espíritu de cobardía, sino de poder, de amor y de dominio propio."),
    ("Hebreos 11:1", "La fe es la certeza de lo que se espera, la convicción de lo que no se ve."),
    ("Hebreos 12:1", "Corramos con paciencia la carrera que tenemos por delante."),
    ("Hebreos 13:8", "Jesucristo es el mismo ayer, y hoy, y por los siglos."),
    ("Santiago 1:5", "Si alguno tiene falta de sabiduría, pídala a Dios, el cual da a todos abundantemente y sin reproche."),
    ("Santiago 1:17", "Toda buena dádiva y todo don perfecto desciende de lo alto, del Padre de las luces."),
    ("1 Pedro 5:7", "Echad toda vuestra ansiedad sobre él, porque él tiene cuidado de vosotros."),
    ("1 Juan 4:18", "En el amor no hay temor, sino que el perfecto amor echa fuera el temor."),
    ("Apocalipsis 21:5", "He aquí, yo hago nuevas todas las cosas."),
    ("Salmos 16:11", "Me mostrarás la senda de la vida; en tu presencia hay plenitud de gozo."),
]

_CLOSING_VERSES = [
    ("Salmos 4:8", "En paz me acostaré y así también dormiré, porque solo tú, Señor, me haces vivir confiado."),
    ("Mateo 11:28", "Vengan a mí todos ustedes que están cansados y agobiados, y yo les daré descanso."),
    ("Salmos 127:2", "Dios concede el sueño a sus amados."),
    ("Salmos 3:5", "Yo me acosté y dormí, y desperté, porque el Señor me sustentaba."),
    ("Salmos 91:1", "El que habita al abrigo del Altísimo morará bajo la sombra del Omnipotente."),
    ("Salmos 91:11", "Pues a sus ángeles mandará acerca de ti, que te guarden en todos tus caminos."),
    ("Salmos 121:3-4", "No dará tu pie al resbaladero, ni se dormirá el que te guarda. He aquí, no se adormecerá ni dormirá el que guarda a Israel."),
    ("Salmos 139:23-24", "Examíname, oh Dios, y conoce mi corazón; pruébame y conoce mis pensamientos."),
    ("Salmos 30:5", "Por la noche durará el lloro, y a la mañana vendrá la alegría."),
    ("Salmos 63:6", "Cuando me acuerdo de ti en mi lecho, medito en ti en las vigilias de la noche."),
    ("Salmos 141:2", "Suba mi oración delante de ti como el incienso, el don de mis manos como la ofrenda de la tarde."),
    ("Proverbios 3:24", "Cuando te acuestes, no tendrás temor; te acostarás, y tu sueño será grato."),
    ("Isaías 30:15", "En quietud y en confianza será vuestra fortaleza."),
    ("Isaías 32:18", "Mi pueblo habitará en morada de paz, en habitaciones seguras, en descanso tranquilo."),
    ("Jeremías 31:25", "Porque satisfaré al alma cansada, y saciaré a toda alma entristecida."),
    ("Lamentaciones 3:25", "Bueno es el Señor a los que en él esperan, al alma que le busca."),
    ("Filipenses 4:7", "La paz de Dios, que sobrepasa todo entendimiento, guardará vuestros corazones y vuestros pensamientos en Cristo Jesús."),
    ("2 Tesalonicenses 3:16", "El Señor de paz os dé siempre paz en toda manera."),
    ("Hebreos 4:9-10", "Queda un reposo para el pueblo de Dios; porque el que ha entrado en su reposo, también ha reposado de sus obras."),
    ("Colosenses 3:15", "Y la paz de Dios gobierne en vuestros corazones."),
    ("Salmos 116:7", "Vuelve, oh alma mía, a tu reposo, porque el Señor te ha hecho bien."),
    ("Salmos 62:1", "En Dios solamente está acallada mi alma; de él viene mi salvación."),
    ("Salmos 94:19", "En la multitud de mis pensamientos dentro de mí, tus consuelos alegraban mi alma."),
    ("Salmos 103:2-3", "Bendice, alma mía, al Señor, y no olvides ninguno de sus beneficios."),
    ("1 Crónicas 16:34", "Aclamad al Señor, porque él es bueno; porque su misericordia es eterna."),
    ("Salmos 92:1-2", "Bueno es alabarte, oh Señor, y cantar salmos a tu nombre, oh Altísimo; anunciar por la mañana tu misericordia, y tu fidelidad cada noche."),
    ("Salmos 145:18", "Cercano está el Señor a todos los que le invocan, a todos los que le invocan de veras."),
    ("Nahúm 1:7", "Bueno es el Señor para refugio en el día de la angustia; y conoce a los que en él confían."),
    ("Romanos 8:38-39", "Nada nos podrá separar del amor de Dios, que es en Cristo Jesús Señor nuestro."),
    ("Apocalipsis 21:4", "Enjugará Dios toda lágrima de los ojos de ellos; y ya no habrá muerte, ni habrá más llanto."),
]


def _pick_verse(pool: list[tuple[str, str]], on_date: date | None = None) -> tuple[str, str]:
    d = on_date or date.today()
    index = d.timetuple().tm_yday % len(pool)
    return pool[index]


class ClaudeClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def _use_claude(self) -> bool:
        return bool(self.api_key)

    def _ask(self, prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def get_morning_message(self, pending_from_yesterday: list[str]) -> str:
        if self._use_claude():
            try:
                return self._morning_claude(pending_from_yesterday)
            except Exception:
                pass
        return self._morning_fallback(pending_from_yesterday)

    def _morning_claude(self, pending_from_yesterday: list[str]) -> str:
        pending_section = ""
        if pending_from_yesterday:
            items = "\n".join(f"- {t}" for t in pending_from_yesterday)
            pending_section = f"\n\nLos siguientes ítems quedaron pendientes de ayer y ya están en la lista de hoy:\n{items}"

        prompt = f"""Eres un asistente espiritual y de productividad personal que acompaña al usuario cada mañana.
Generá un mensaje de buenos días en español con estas secciones, sin títulos ni markdown, solo texto fluido:

1. Un saludo cálido y espiritual para comenzar el día.
2. Un versículo bíblico relevante (cita el libro, capítulo y versículo).
3. Una reflexión breve (2-3 oraciones) sobre ese versículo aplicado a la vida diaria.
4. Una frase motivadora corta al final.
{pending_section}

Terminá preguntando: "¿Qué querés hacer hoy? Escribime tus tareas, una por línea o separadas por coma."

Tono: espiritual, cálido, esperanzador. Sin emojis excesivos."""
        return self._ask(prompt)

    def _morning_fallback(self, pending_from_yesterday: list[str]) -> str:
        ref, verse = random.choice(_VERSES)
        pending_section = ""
        if pending_from_yesterday:
            items = "\n".join(f"- {t}" for t in pending_from_yesterday)
            pending_section = f"\n\nDe ayer quedaron estos pendientes ya cargados en tu lista de hoy:\n{items}\n"

        return (
            f"Buenos días. Que este nuevo día sea una oportunidad para crecer y servir.\n\n"
            f"{ref}\n\"{verse}\"\n\n"
            f"Cada mañana es un regalo. Enfocá tu energía en lo que depende de vos, "
            f"y encomendá lo demás a Dios.\n\n"
            f"Que tengas un día bendecido y productivo."
            f"{pending_section}\n\n"
            f"¿Qué querés hacer hoy? Escribime tus tareas, una por línea o separadas por coma."
        )

    def get_followup_message(self, has_tasks: bool) -> str:
        if self._use_claude():
            try:
                if has_tasks:
                    prompt = "Generá un mensaje breve de aliento en español para alguien que ya registró sus tareas del día. Recordale que puede escribirte cuando necesite ayuda o agregar más tareas. Tono espiritual y cálido. Una o dos oraciones."
                else:
                    prompt = "Generá un mensaje breve en español recordándole al usuario que aún no escribió sus tareas para hoy. Incluí una frase bíblica corta de aliento. Tono gentil. Dos o tres oraciones máximo."
                return self._ask(prompt)
            except Exception:
                pass

        if has_tasks:
            return "Ya tenés tu día organizado. Adelante, Dios te acompaña en cada paso. Escribime si necesitás agregar algo."
        return "Todavía no registraste tus tareas de hoy. \"Encomienda al Señor tus obras y tus planes se cumplirán.\" (Proverbios 16:3) ¿Qué querés hacer hoy?"

    def parse_tasks_from_text(self, user_text: str) -> list[str]:
        if self._use_claude():
            try:
                prompt = f"""El usuario describió sus tareas para hoy. Extraé una lista limpia de tareas individuales.
Devolvé SOLO un JSON array de strings, sin explicación. Ejemplo: ["Tarea 1", "Tarea 2"]

Texto del usuario: {user_text}"""
                raw = self._ask(prompt)
                start = raw.find("[")
                end = raw.rfind("]") + 1
                return json.loads(raw[start:end])
            except Exception:
                pass

        lines = [l.strip("- •*").strip() for l in user_text.replace(",", "\n").splitlines()]
        return [l for l in lines if l]

    def get_night_message(self, tasks: list[dict]) -> str:
        if self._use_claude():
            try:
                return self._night_claude(tasks)
            except Exception:
                pass
        return self._night_fallback(tasks)

    def _night_claude(self, tasks: list[dict]) -> str:
        task_section = "\n".join(
            f"- {'✓' if t['status'] == 'done' else '○'} {t['text']}"
            for t in tasks
        ) if tasks else "No había tareas registradas para hoy."

        prompt = f"""Eres un asistente espiritual nocturno. Es de noche y es momento de revisar el día.

Tareas del día:
{task_section}

Generá un mensaje en español que:
1. Celebre el esfuerzo del día con un versículo bíblico de gratitud o descanso.
2. Muestre la lista de tareas del día.
3. Pregunte: "¿Qué pudiste hacer hoy? Contame qué tareas completaste y cuáles quedaron pendientes."

Tono: tranquilo, reflexivo, espiritual. Sin emojis excesivos."""
        return self._ask(prompt)

    def _night_fallback(self, tasks: list[dict]) -> str:
        ref, verse = random.choice(_CLOSING_VERSES)
        task_section = "\n".join(
            f"{'✓' if t['status'] == 'done' else '○'} {t['text']}"
            for t in tasks
        ) if tasks else "No había tareas registradas para hoy."

        return (
            f"Buenas noches. Es momento de descansar y revisar el día.\n\n"
            f"{ref}\n\"{verse}\"\n\n"
            f"Estas fueron tus tareas de hoy:\n{task_section}\n\n"
            f"¿Qué pudiste hacer hoy? Contame qué tareas completaste y cuáles quedaron pendientes."
        )

    def parse_night_review(self, user_text: str, tasks: list[dict]) -> dict:
        if self._use_claude():
            try:
                task_list = "\n".join(f"{t['id']}. {t['text']}" for t in tasks)
                prompt = f"""El usuario revisó su día. Determiná qué tareas completó y cuáles quedaron pendientes.

Tareas registradas:
{task_list}

Lo que dijo el usuario: {user_text}

Devolvé SOLO un JSON con este formato exacto:
{{"done": [id1, id2], "pending": [id3, id4]}}

Donde done y pending son listas de IDs numéricos de las tareas."""
                raw = self._ask(prompt)
                start = raw.find("{")
                end = raw.rfind("}") + 1
                return json.loads(raw[start:end])
            except Exception:
                pass

        text_lower = user_text.lower()
        negative_words = {"no", "faltó", "falto", "quedó", "quedo", "pendiente", "sin", "imposible"}
        all_done_phrases = ("todas", "todo", "sí", "si", "listo", "listas", "completé", "complete",
                            "realicé", "realice", "hice", "hizo", "cumplí", "cumpli", "terminé",
                            "termine", "finalicé", "finalice")
        has_all_done = any(p in text_lower.split() for p in all_done_phrases)
        has_negative = any(neg in text_lower for neg in negative_words)

        if has_all_done and not has_negative:
            return {"done": [t["id"] for t in tasks], "pending": []}

        done_ids, pending_ids = [], []
        for t in tasks:
            words = [w for w in t["text"].lower().split() if len(w) > 3]
            if any(w in text_lower for w in words):
                done_ids.append(t["id"])
            else:
                pending_ids.append(t["id"])
        return {"done": done_ids, "pending": pending_ids}

    def get_closing_message(self, done_count: int, pending_count: int) -> str:
        if self._use_claude():
            try:
                prompt = f"""El usuario terminó su revisión nocturna. Completó {done_count} tarea(s) y dejó {pending_count} pendiente(s).

Generá un mensaje de cierre del día en español con:
1. Una palabra de gratitud y aliento basada en el esfuerzo realizado.
2. Un versículo bíblico relacionado con el descanso o la perseverancia.
3. Una frase de buenas noches.

Tono: cálido, espiritual, tranquilizador. Máximo 5 oraciones."""
                return self._ask(prompt)
            except Exception:
                pass

        ref, verse = random.choice(_CLOSING_VERSES)
        if done_count == 0:
            balance = "Cada día es un nuevo comienzo. Mañana tenés otra oportunidad."
        elif pending_count == 0:
            balance = f"¡Completaste todo lo que te propusiste! Qué orgullo."
        else:
            balance = f"Completaste {done_count} tarea(s). Los {pending_count} pendiente(s) los veremos mañana."

        return (
            f"{balance}\n\n"
            f"{ref}\n\"{verse}\"\n\n"
            f"Descansá bien. Mañana a las 8 seguimos. Buenas noches."
        )
