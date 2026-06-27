import json
import random

_VERSES = [
    ("Jeremías 29:11", "Porque yo sé los planes que tengo para ustedes, planes de bienestar y no de calamidad, para darles un futuro y una esperanza."),
    ("Filipenses 4:13", "Todo lo puedo en Cristo que me fortalece."),
    ("Josué 1:9", "Sé fuerte y valiente. No temas ni te desanimes, porque el Señor tu Dios estará contigo dondequiera que vayas."),
    ("Salmos 118:24", "Este es el día que hizo el Señor; nos gozaremos y alegraremos en él."),
    ("Proverbios 3:5-6", "Confía en el Señor con todo tu corazón y no te apoyes en tu propio entendimiento. Reconócelo en todos tus caminos y él allanará tus sendas."),
    ("Mateo 6:34", "No se angustien por el mañana, el cual tendrá sus propios afanes. Cada día tiene ya sus problemas."),
    ("Isaías 40:31", "Los que confían en el Señor renovarán sus fuerzas; volarán como las águilas, correrán y no se fatigarán, caminarán y no se cansarán."),
    ("Salmos 23:1", "El Señor es mi pastor, nada me faltará."),
]

_CLOSING_VERSES = [
    ("Salmos 4:8", "En paz me acostaré y así también dormiré, porque solo tú, Señor, me haces vivir confiado."),
    ("Mateo 11:28", "Vengan a mí todos ustedes que están cansados y agobiados, y yo les daré descanso."),
    ("Salmos 127:2", "Dios concede el sueño a sus amados."),
]


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
