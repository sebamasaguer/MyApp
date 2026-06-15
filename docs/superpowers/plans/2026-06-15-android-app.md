# Daily Agent Android App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir una app Android en Flutter que reemplaza el bot de Telegram — dashboard de tareas diarias + chat con Claude + notificaciones programadas.

**Architecture:** App Flutter standalone sin backend. SQLite local para datos, llamadas HTTP directas a la API de Anthropic, WorkManager para scheduling de notificaciones diarias (08:00, 08:30, 23:00). API key guardada en flutter_secure_storage.

**Tech Stack:** Flutter 3.x, sqflite, http, flutter_local_notifications, workmanager, flutter_secure_storage, intl

**Proyecto nuevo en:** `/home/seba/Escritorio/hackathon/DailyAgentApp`

---

## Estructura de archivos

```
DailyAgentApp/
└── lib/
    ├── main.dart                        # Entry point, WorkManager callback
    ├── app.dart                         # MaterialApp, routing, theme
    ├── models/
    │   ├── task.dart                    # Modelo Task
    │   └── day_log.dart                 # Modelo DayLog
    ├── core/
    │   ├── database.dart                # SQLite: CRUD tasks + day_log
    │   ├── anthropic_client.dart        # HTTP calls a Claude API
    │   └── secure_storage.dart          # Guardar/leer API key
    ├── services/
    │   └── notification_service.dart    # WorkManager + flutter_local_notifications
    ├── screens/
    │   ├── welcome_screen.dart          # Primera vez: pide API key
    │   ├── main_shell.dart              # BottomNavigationBar shell
    │   ├── dashboard_screen.dart        # Resumen del día
    │   ├── tasks_screen.dart            # Lista completa de tareas
    │   ├── chat_screen.dart             # Chat con Claude (modo morning/night/free)
    │   └── settings_screen.dart         # API key, timezone, horarios
    └── widgets/
        ├── task_tile.dart               # Fila de tarea con checkbox
        ├── progress_header.dart         # Barra de progreso + saludo
        └── day_status_card.dart         # Tarjeta estado mañana/noche
```

---

## Task 1: Instalar Flutter y crear el proyecto

**Files:**
- Create: `/home/seba/Escritorio/hackathon/DailyAgentApp/` (proyecto Flutter)
- Create: `pubspec.yaml`

- [ ] **Step 1: Instalar Flutter via snap**

```bash
sudo snap install flutter --classic
flutter --version
```
Esperado: `Flutter 3.x.x`

- [ ] **Step 2: Aceptar licencias de Android SDK**

```bash
flutter doctor --android-licenses
```
Responder `y` a todo. Luego:
```bash
flutter doctor
```
Verificar que no haya errores críticos (puede haber warnings de Xcode/iOS — ignorarlos).

- [ ] **Step 3: Crear el proyecto Flutter**

```bash
cd /home/seba/Escritorio/hackathon
flutter create --org com.sebamasaguer --project-name daily_agent_app DailyAgentApp
cd DailyAgentApp
```

- [ ] **Step 4: Reemplazar pubspec.yaml con las dependencias del proyecto**

Reemplazar el contenido de `pubspec.yaml`:

```yaml
name: daily_agent_app
description: Agente diario personal con Claude AI
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  sqflite: ^2.3.3
  path: ^1.9.0
  http: ^1.2.1
  flutter_local_notifications: ^17.2.2
  workmanager: ^0.5.2
  flutter_secure_storage: ^9.2.2
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0

flutter:
  uses-material-design: true
```

- [ ] **Step 5: Instalar dependencias**

```bash
flutter pub get
```
Esperado: `Got dependencies!`

- [ ] **Step 6: Commit inicial**

```bash
git add -A
git commit -m "feat: crear proyecto Flutter DailyAgentApp"
```

---

## Task 2: Modelos de datos

**Files:**
- Create: `lib/models/task.dart`
- Create: `lib/models/day_log.dart`
- Test: `test/models/task_test.dart`
- Test: `test/models/day_log_test.dart`

- [ ] **Step 1: Escribir test de Task**

Crear `test/models/task_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:daily_agent_app/models/task.dart';

void main() {
  group('Task', () {
    test('fromMap crea Task desde mapa SQLite', () {
      final map = {
        'id': 1,
        'date': '2026-06-15',
        'text': 'Terminar el plan',
        'status': 'pending',
        'created_at': '2026-06-15 08:00:00',
      };
      final task = Task.fromMap(map);
      expect(task.id, 1);
      expect(task.date, '2026-06-15');
      expect(task.text, 'Terminar el plan');
      expect(task.status, 'pending');
    });

    test('toMap convierte Task a mapa SQLite', () {
      final task = Task(date: '2026-06-15', text: 'Estudiar Flutter', status: 'pending');
      final map = task.toMap();
      expect(map['date'], '2026-06-15');
      expect(map['text'], 'Estudiar Flutter');
      expect(map['status'], 'pending');
      expect(map.containsKey('id'), isFalse);
    });

    test('isPending retorna true si status es pending', () {
      final task = Task(date: '2026-06-15', text: 'x', status: 'pending');
      expect(task.isPending, isTrue);
    });

    test('isPending retorna false si status es done', () {
      final task = Task(date: '2026-06-15', text: 'x', status: 'done');
      expect(task.isPending, isFalse);
    });
  });
}
```

- [ ] **Step 2: Ejecutar test (debe fallar)**

```bash
flutter test test/models/task_test.dart
```
Esperado: error de compilación — `Task` no existe.

- [ ] **Step 3: Crear lib/models/task.dart**

```dart
class Task {
  final int? id;
  final String date;
  final String text;
  final String status;
  final String? createdAt;

  Task({
    this.id,
    required this.date,
    required this.text,
    this.status = 'pending',
    this.createdAt,
  });

  bool get isPending => status == 'pending';

  Task copyWith({String? status}) => Task(
        id: id,
        date: date,
        text: text,
        status: status ?? this.status,
        createdAt: createdAt,
      );

  Map<String, dynamic> toMap() {
    final map = <String, dynamic>{
      'date': date,
      'text': text,
      'status': status,
    };
    if (id != null) map['id'] = id;
    return map;
  }

  factory Task.fromMap(Map<String, dynamic> map) => Task(
        id: map['id'] as int?,
        date: map['date'] as String,
        text: map['text'] as String,
        status: map['status'] as String? ?? 'pending',
        createdAt: map['created_at'] as String?,
      );
}
```

- [ ] **Step 4: Ejecutar test (debe pasar)**

```bash
flutter test test/models/task_test.dart
```
Esperado: `All tests passed!`

- [ ] **Step 5: Escribir test de DayLog**

Crear `test/models/day_log_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:daily_agent_app/models/day_log.dart';

void main() {
  group('DayLog', () {
    test('fromMap crea DayLog desde mapa SQLite', () {
      final map = {
        'id': 1,
        'date': '2026-06-15',
        'morning_plan': 'Plan de hoy',
        'night_review': null,
        'state': 'morning_done',
        'created_at': '2026-06-15 08:00:00',
      };
      final log = DayLog.fromMap(map);
      expect(log.date, '2026-06-15');
      expect(log.state, 'morning_done');
      expect(log.morningPlan, 'Plan de hoy');
      expect(log.nightReview, isNull);
    });

    test('isMorningDone retorna true si state es morning_done', () {
      final log = DayLog(date: '2026-06-15', state: 'morning_done');
      expect(log.isMorningDone, isTrue);
    });

    test('isNightDone retorna true si state es night_done', () {
      final log = DayLog(date: '2026-06-15', state: 'night_done');
      expect(log.isNightDone, isTrue);
    });
  });
}
```

- [ ] **Step 6: Crear lib/models/day_log.dart**

```dart
class DayLog {
  final int? id;
  final String date;
  final String? morningPlan;
  final String? nightReview;
  final String state;
  final String? createdAt;

  DayLog({
    this.id,
    required this.date,
    this.morningPlan,
    this.nightReview,
    this.state = 'idle',
    this.createdAt,
  });

  bool get isMorningDone => state == 'morning_done';
  bool get isNightDone => state == 'night_done';

  DayLog copyWith({String? state, String? morningPlan, String? nightReview}) =>
      DayLog(
        id: id,
        date: date,
        morningPlan: morningPlan ?? this.morningPlan,
        nightReview: nightReview ?? this.nightReview,
        state: state ?? this.state,
        createdAt: createdAt,
      );

  Map<String, dynamic> toMap() => {
        'date': date,
        'morning_plan': morningPlan,
        'night_review': nightReview,
        'state': state,
      };

  factory DayLog.fromMap(Map<String, dynamic> map) => DayLog(
        id: map['id'] as int?,
        date: map['date'] as String,
        morningPlan: map['morning_plan'] as String?,
        nightReview: map['night_review'] as String?,
        state: map['state'] as String? ?? 'idle',
        createdAt: map['created_at'] as String?,
      );
}
```

- [ ] **Step 7: Ejecutar todos los tests de modelos**

```bash
flutter test test/models/
```
Esperado: `All tests passed!`

- [ ] **Step 8: Commit**

```bash
git add lib/models/ test/models/
git commit -m "feat: agregar modelos Task y DayLog"
```

---

## Task 3: Capa de base de datos (SQLite)

**Files:**
- Create: `lib/core/database.dart`
- Test: `test/core/database_test.dart`

- [ ] **Step 1: Escribir tests de DatabaseService**

Crear `test/core/database_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:daily_agent_app/core/database.dart';
import 'package:daily_agent_app/models/task.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late DatabaseService db;

  setUp(() async {
    db = DatabaseService(dbPath: ':memory:');
    await db.init();
  });

  tearDown(() async {
    await db.close();
  });

  group('DatabaseService - tasks', () {
    test('addTasks inserta tareas y getTasks las devuelve', () async {
      await db.addTasks(['Tarea 1', 'Tarea 2'], '2026-06-15');
      final tasks = await db.getTasksForDate('2026-06-15');
      expect(tasks.length, 2);
      expect(tasks[0].text, 'Tarea 1');
      expect(tasks[1].text, 'Tarea 2');
    });

    test('getPendingTasks solo devuelve pendientes', () async {
      await db.addTasks(['Tarea 1', 'Tarea 2'], '2026-06-15');
      final all = await db.getTasksForDate('2026-06-15');
      await db.updateTaskStatus(all[0].id!, 'done');
      final pending = await db.getPendingTasksForDate('2026-06-15');
      expect(pending.length, 1);
      expect(pending[0].text, 'Tarea 2');
    });

    test('carryOverPending mueve pendientes de ayer a hoy', () async {
      await db.addTasks(['Pendiente ayer'], '2026-06-14');
      await db.carryOverPending(from: '2026-06-14', to: '2026-06-15');
      final today = await db.getTasksForDate('2026-06-15');
      expect(today.length, 1);
      expect(today[0].text, 'Pendiente ayer');
    });
  });

  group('DatabaseService - day_log', () {
    test('setState crea registro si no existe', () async {
      await db.setState('morning_done', '2026-06-15');
      final log = await db.getDayLog('2026-06-15');
      expect(log?.state, 'morning_done');
    });

    test('setState actualiza si ya existe', () async {
      await db.setState('morning_done', '2026-06-15');
      await db.setState('night_done', '2026-06-15');
      final log = await db.getDayLog('2026-06-15');
      expect(log?.state, 'night_done');
    });

    test('saveMorningPlan guarda el plan', () async {
      await db.saveMorningPlan('Plan del día', '2026-06-15');
      final log = await db.getDayLog('2026-06-15');
      expect(log?.morningPlan, 'Plan del día');
    });
  });
}
```

- [ ] **Step 2: Agregar sqflite_common_ffi al pubspec.yaml (solo dev)**

Agregar en `dev_dependencies` de `pubspec.yaml`:

```yaml
  sqflite_common_ffi: ^2.3.3
```

Luego: `flutter pub get`

- [ ] **Step 3: Ejecutar test (debe fallar)**

```bash
flutter test test/core/database_test.dart
```
Esperado: error — `DatabaseService` no existe.

- [ ] **Step 4: Crear lib/core/database.dart**

```dart
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../models/day_log.dart';
import '../models/task.dart';

class DatabaseService {
  static final DatabaseService _instance = DatabaseService._internal();
  factory DatabaseService({String? dbPath}) {
    if (dbPath != null) return DatabaseService._withPath(dbPath);
    return _instance;
  }

  DatabaseService._internal() : _dbPath = null;
  DatabaseService._withPath(String path) : _dbPath = path;

  final String? _dbPath;
  Database? _db;

  Future<void> init() async {
    if (_db != null) return;
    final path = _dbPath ??
        join(await getDatabasesPath(), 'daily_agent.db');
    _db = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        ''');
        await db.execute('''
          CREATE TABLE day_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            morning_plan TEXT,
            night_review TEXT,
            state TEXT DEFAULT 'idle',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        ''');
      },
    );
  }

  Future<void> close() async => await _db?.close();

  Database get _database {
    if (_db == null) throw StateError('DatabaseService no inicializado. Llama init() primero.');
    return _db!;
  }

  // --- Tasks ---

  Future<void> addTasks(List<String> texts, String date) async {
    final batch = _database.batch();
    for (final text in texts) {
      if (text.trim().isEmpty) continue;
      batch.insert('tasks', {'date': date, 'text': text.trim(), 'status': 'pending'});
    }
    await batch.commit(noResult: true);
  }

  Future<List<Task>> getTasksForDate(String date) async {
    final rows = await _database.query('tasks', where: 'date = ?', whereArgs: [date], orderBy: 'id');
    return rows.map(Task.fromMap).toList();
  }

  Future<List<Task>> getPendingTasksForDate(String date) async {
    final rows = await _database.query(
      'tasks',
      where: 'date = ? AND status = ?',
      whereArgs: [date, 'pending'],
      orderBy: 'id',
    );
    return rows.map(Task.fromMap).toList();
  }

  Future<void> updateTaskStatus(int id, String status) async {
    await _database.update('tasks', {'status': status}, where: 'id = ?', whereArgs: [id]);
  }

  Future<void> carryOverPending({required String from, required String to}) async {
    final pending = await getPendingTasksForDate(from);
    if (pending.isEmpty) return;
    await addTasks(pending.map((t) => t.text).toList(), to);
    await _database.update(
      'tasks',
      {'status': 'carried_over'},
      where: 'date = ? AND status = ?',
      whereArgs: [from, 'pending'],
    );
  }

  // --- DayLog ---

  Future<DayLog?> getDayLog(String date) async {
    final rows = await _database.query('day_log', where: 'date = ?', whereArgs: [date]);
    if (rows.isEmpty) return null;
    return DayLog.fromMap(rows.first);
  }

  Future<void> setState(String state, String date) async {
    await _database.insert(
      'day_log',
      {'date': date, 'state': state},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    await _database.update('day_log', {'state': state}, where: 'date = ?', whereArgs: [date]);
  }

  Future<void> saveMorningPlan(String plan, String date) async {
    await _database.insert(
      'day_log',
      {'date': date, 'morning_plan': plan, 'state': 'morning_done'},
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );
    await _database.update(
      'day_log',
      {'morning_plan': plan, 'state': 'morning_done'},
      where: 'date = ?',
      whereArgs: [date],
    );
  }

  Future<void> saveNightReview(String review, String date) async {
    await _database.insert(
      'day_log',
      {'date': date, 'night_review': review, 'state': 'night_done'},
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );
    await _database.update(
      'day_log',
      {'night_review': review, 'state': 'night_done'},
      where: 'date = ?',
      whereArgs: [date],
    );
  }
}
```

- [ ] **Step 5: Ejecutar tests**

```bash
flutter test test/core/database_test.dart
```
Esperado: `All tests passed!`

- [ ] **Step 6: Commit**

```bash
git add lib/core/database.dart test/core/ pubspec.yaml pubspec.lock
git commit -m "feat: agregar DatabaseService con SQLite"
```

---

## Task 4: Cliente Anthropic

**Files:**
- Create: `lib/core/anthropic_client.dart`
- Test: `test/core/anthropic_client_test.dart`

- [ ] **Step 1: Crear lib/core/anthropic_client.dart**

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

enum ChatMode { morning, night, free }

class ChatMessage {
  final String role; // 'user' o 'assistant'
  final String content;
  ChatMessage({required this.role, required this.content});
  Map<String, dynamic> toMap() => {'role': role, 'content': content};
}

class AnthropicClient {
  static const _baseUrl = 'https://api.anthropic.com/v1/messages';
  static const _model = 'claude-sonnet-4-6';

  final String apiKey;
  final http.Client _httpClient;

  AnthropicClient({required this.apiKey, http.Client? httpClient})
      : _httpClient = httpClient ?? http.Client();

  String _buildSystemPrompt(ChatMode mode, List<String> tasks, String date) {
    final taskList = tasks.isEmpty
        ? 'Ninguna tarea cargada aún.'
        : tasks.map((t) => '- $t').join('\n');

    final modeInstructions = switch (mode) {
      ChatMode.morning =>
        'Es la mañana. Saludá al usuario, preguntá cuáles son sus tareas del día de forma amigable y breve.',
      ChatMode.night =>
        'Es la noche. Hacé una revisión del día: preguntá qué logró, qué quedó pendiente, y cerrá con un mensaje motivador.',
      ChatMode.free =>
        'El usuario inició una conversación libre. Respondé de forma útil y amigable sobre su día y tareas.',
    };

    return '''Sos un asistente personal de productividad. Hoy es $date.

Tareas del día:
$taskList

$modeInstructions

Respondé siempre en español, de forma concisa (máximo 3 párrafos). No uses emojis en exceso.''';
  }

  Future<String> sendMessage({
    required List<ChatMessage> history,
    required ChatMode mode,
    required List<String> tasks,
    required String date,
  }) async {
    final response = await _httpClient.post(
      Uri.parse(_baseUrl),
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: jsonEncode({
        'model': _model,
        'max_tokens': 1024,
        'system': _buildSystemPrompt(mode, tasks, date),
        'messages': history.map((m) => m.toMap()).toList(),
      }),
    );

    if (response.statusCode != 200) {
      final body = jsonDecode(response.body);
      throw AnthropicException(
        statusCode: response.statusCode,
        message: body['error']?['message'] ?? 'Error desconocido',
      );
    }

    final body = jsonDecode(response.body);
    return body['content'][0]['text'] as String;
  }
}

class AnthropicException implements Exception {
  final int statusCode;
  final String message;
  AnthropicException({required this.statusCode, required this.message});

  @override
  String toString() => 'AnthropicException($statusCode): $message';
}
```

- [ ] **Step 2: Escribir tests con mock HTTP**

Crear `test/core/anthropic_client_test.dart`:

```dart
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:daily_agent_app/core/anthropic_client.dart';

void main() {
  group('AnthropicClient', () {
    test('sendMessage retorna texto de respuesta exitosa', () async {
      final mockClient = MockClient((request) async {
        expect(request.headers['x-api-key'], 'test-key');
        return http.Response(
          jsonEncode({
            'content': [{'text': 'Hola, ¿cómo vas con tus tareas?', 'type': 'text'}]
          }),
          200,
        );
      });

      final client = AnthropicClient(apiKey: 'test-key', httpClient: mockClient);
      final result = await client.sendMessage(
        history: [ChatMessage(role: 'user', content: 'Hola')],
        mode: ChatMode.morning,
        tasks: ['Estudiar Flutter'],
        date: '2026-06-15',
      );

      expect(result, 'Hola, ¿cómo vas con tus tareas?');
    });

    test('sendMessage lanza AnthropicException con 401', () async {
      final mockClient = MockClient((_) async => http.Response(
            jsonEncode({'error': {'message': 'Invalid API key'}}),
            401,
          ));

      final client = AnthropicClient(apiKey: 'bad-key', httpClient: mockClient);
      expect(
        () => client.sendMessage(
          history: [ChatMessage(role: 'user', content: 'Hola')],
          mode: ChatMode.free,
          tasks: [],
          date: '2026-06-15',
        ),
        throwsA(isA<AnthropicException>()),
      );
    });
  });
}
```

- [ ] **Step 3: Agregar http al dev para testing**

En `pubspec.yaml`, bajo `dev_dependencies`:
```yaml
  http: ^1.2.1
```
(ya está en dependencies — no duplicar, el test lo puede usar directamente)

- [ ] **Step 4: Ejecutar tests**

```bash
flutter test test/core/anthropic_client_test.dart
```
Esperado: `All tests passed!`

- [ ] **Step 5: Commit**

```bash
git add lib/core/anthropic_client.dart test/core/anthropic_client_test.dart
git commit -m "feat: agregar AnthropicClient con soporte de modos morning/night/free"
```

---

## Task 5: Secure Storage

**Files:**
- Create: `lib/core/secure_storage.dart`

- [ ] **Step 1: Crear lib/core/secure_storage.dart**

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  static const _keyApiKey = 'anthropic_api_key';
  static const _keyTimezone = 'timezone';

  final FlutterSecureStorage _storage;

  SecureStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<String?> getApiKey() => _storage.read(key: _keyApiKey);
  Future<void> saveApiKey(String key) => _storage.write(key: _keyApiKey, value: key);
  Future<bool> hasApiKey() async => (await getApiKey()) != null;

  Future<String> getTimezone() async =>
      (await _storage.read(key: _keyTimezone)) ?? 'America/Argentina/Salta';
  Future<void> saveTimezone(String tz) => _storage.write(key: _keyTimezone, value: tz);

  Future<void> deleteAll() => _storage.deleteAll();
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/core/secure_storage.dart
git commit -m "feat: agregar SecureStorage para API key"
```

---

## Task 6: Entry point y navegación

**Files:**
- Modify: `lib/main.dart`
- Create: `lib/app.dart`
- Create: `lib/screens/main_shell.dart`

- [ ] **Step 1: Reemplazar lib/main.dart**

```dart
import 'package:flutter/material.dart';
import 'package:workmanager/workmanager.dart';
import 'app.dart';
import 'core/database.dart';
import 'services/notification_service.dart';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((taskName, inputData) async {
    await DatabaseService().init();
    await NotificationService().handleScheduledTask(taskName);
    return Future.value(true);
  });
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await DatabaseService().init();
  await NotificationService().init();
  await Workmanager().initialize(callbackDispatcher, isInDebugMode: false);
  runApp(const DailyAgentApp());
}
```

- [ ] **Step 2: Crear lib/app.dart**

```dart
import 'package:flutter/material.dart';
import 'core/secure_storage.dart';
import 'screens/main_shell.dart';
import 'screens/welcome_screen.dart';

class DailyAgentApp extends StatelessWidget {
  const DailyAgentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Agente Diario',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6750A4)),
        useMaterial3: true,
      ),
      home: const _StartupRouter(),
    );
  }
}

class _StartupRouter extends StatefulWidget {
  const _StartupRouter();

  @override
  State<_StartupRouter> createState() => _StartupRouterState();
}

class _StartupRouterState extends State<_StartupRouter> {
  bool? _hasKey;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final has = await SecureStorage().hasApiKey();
    setState(() => _hasKey = has);
  }

  @override
  Widget build(BuildContext context) {
    if (_hasKey == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _hasKey! ? const MainShell() : const WelcomeScreen();
  }
}
```

- [ ] **Step 3: Crear lib/screens/main_shell.dart**

```dart
import 'package:flutter/material.dart';
import 'dashboard_screen.dart';
import 'tasks_screen.dart';
import 'settings_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  final _screens = const [
    DashboardScreen(),
    TasksScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Inicio'),
          NavigationDestination(icon: Icon(Icons.checklist_outlined), selectedIcon: Icon(Icons.checklist), label: 'Tareas'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Configuración'),
        ],
      ),
    );
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add lib/main.dart lib/app.dart lib/screens/main_shell.dart
git commit -m "feat: agregar entry point y navegación con BottomNavigationBar"
```

---

## Task 7: Pantalla de bienvenida

**Files:**
- Create: `lib/screens/welcome_screen.dart`

- [ ] **Step 1: Crear lib/screens/welcome_screen.dart**

```dart
import 'package:flutter/material.dart';
import '../core/secure_storage.dart';
import '../services/notification_service.dart';
import 'main_shell.dart';

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> {
  final _controller = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });

    final key = _controller.text.trim();
    await SecureStorage().saveApiKey(key);
    await NotificationService().scheduleAll();

    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const MainShell()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.psychology, size: 64, color: Color(0xFF6750A4)),
                const SizedBox(height: 16),
                Text('Agente Diario', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text('Para comenzar, ingresá tu clave de API de Anthropic.', style: Theme.of(context).textTheme.bodyLarge),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    labelText: 'API Key de Anthropic',
                    hintText: 'sk-ant-...',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.key),
                  ),
                  obscureText: true,
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Ingresá tu API key';
                    if (!v.trim().startsWith('sk-ant-')) return 'La key debe empezar con sk-ant-';
                    return null;
                  },
                ),
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _loading ? null : _save,
                    child: _loading ? const CircularProgressIndicator(color: Colors.white) : const Text('Comenzar'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/screens/welcome_screen.dart
git commit -m "feat: agregar WelcomeScreen para ingresar API key"
```

---

## Task 8: Widgets reutilizables

**Files:**
- Create: `lib/widgets/task_tile.dart`
- Create: `lib/widgets/progress_header.dart`
- Create: `lib/widgets/day_status_card.dart`

- [ ] **Step 1: Crear lib/widgets/task_tile.dart**

```dart
import 'package:flutter/material.dart';
import '../models/task.dart';

class TaskTile extends StatelessWidget {
  final Task task;
  final ValueChanged<bool?> onChanged;

  const TaskTile({super.key, required this.task, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final done = !task.isPending;
    return ListTile(
      leading: Checkbox(value: done, onChanged: onChanged),
      title: Text(
        task.text,
        style: TextStyle(
          decoration: done ? TextDecoration.lineThrough : null,
          color: done ? Colors.grey : null,
        ),
      ),
    );
  }
}
```

- [ ] **Step 2: Crear lib/widgets/progress_header.dart**

```dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class ProgressHeader extends StatelessWidget {
  final int completed;
  final int total;

  const ProgressHeader({super.key, required this.completed, required this.total});

  String get _greeting {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Buenos días';
    if (hour < 19) return 'Buenas tardes';
    return 'Buenas noches';
  }

  @override
  Widget build(BuildContext context) {
    final progress = total == 0 ? 0.0 : completed / total;
    final dateStr = DateFormat('EEEE, d \'de\' MMMM', 'es').format(DateTime.now());

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(_greeting, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(dateStr, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey)),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: LinearProgressIndicator(value: progress, minHeight: 8, borderRadius: BorderRadius.circular(4))),
            const SizedBox(width: 12),
            Text('$completed/$total', style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ],
    );
  }
}
```

- [ ] **Step 3: Crear lib/widgets/day_status_card.dart**

```dart
import 'package:flutter/material.dart';
import '../models/day_log.dart';

class DayStatusCard extends StatelessWidget {
  final DayLog? dayLog;

  const DayStatusCard({super.key, this.dayLog});

  @override
  Widget build(BuildContext context) {
    final morningDone = dayLog?.isMorningDone ?? false;
    final nightDone = dayLog?.isNightDone ?? false;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Estado del día', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            _StatusRow(label: 'Planificación matutina', done: morningDone),
            const SizedBox(height: 8),
            _StatusRow(label: 'Revisión nocturna', done: nightDone),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String label;
  final bool done;

  const _StatusRow({required this.label, required this.done});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? Colors.green : Colors.grey, size: 20),
        const SizedBox(width: 8),
        Text(label),
      ],
    );
  }
}
```

- [ ] **Step 4: Agregar soporte de locale español en main.dart**

En `pubspec.yaml`, bajo `flutter:`:
```yaml
  generate: true
```

Y agregar al bloque `dependencies`:
```yaml
  flutter_localizations:
    sdk: flutter
```

En `lib/app.dart`, agregar en `MaterialApp`:
```dart
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/date_symbol_data_local.dart';
// en main() antes de runApp:
await initializeDateFormatting('es', null);

// en MaterialApp:
localizationsDelegates: const [
  GlobalMaterialLocalizations.delegate,
  GlobalWidgetsLocalizations.delegate,
  GlobalCupertinoLocalizations.delegate,
],
supportedLocales: const [Locale('es')],
locale: const Locale('es'),
```

```bash
flutter pub get
```

- [ ] **Step 5: Commit**

```bash
git add lib/widgets/ lib/app.dart pubspec.yaml pubspec.lock
git commit -m "feat: agregar widgets TaskTile, ProgressHeader, DayStatusCard"
```

---

## Task 9: Dashboard Screen

**Files:**
- Create: `lib/screens/dashboard_screen.dart`

- [ ] **Step 1: Crear lib/screens/dashboard_screen.dart**

```dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/database.dart';
import '../models/day_log.dart';
import '../models/task.dart';
import '../widgets/day_status_card.dart';
import '../widgets/progress_header.dart';
import '../widgets/task_tile.dart';
import 'chat_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> with WidgetsBindingObserver {
  final _db = DatabaseService();
  List<Task> _tasks = [];
  DayLog? _dayLog;
  bool _loading = true;

  String get _today => DateFormat('yyyy-MM-dd').format(DateTime.now());

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _load();
  }

  Future<void> _load() async {
    final tasks = await _db.getTasksForDate(_today);
    final log = await _db.getDayLog(_today);
    if (mounted) setState(() { _tasks = tasks; _dayLog = log; _loading = false; });
  }

  Future<void> _toggleTask(Task task) async {
    final newStatus = task.isPending ? 'done' : 'pending';
    await _db.updateTaskStatus(task.id!, newStatus);
    _load();
  }

  void _openChat(ChatMode mode) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ChatScreen(mode: mode, today: _today)),
    );
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final pending = _tasks.where((t) => t.isPending).toList();
    final completed = _tasks.where((t) => !t.isPending).length;

    return Scaffold(
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    ProgressHeader(completed: completed, total: _tasks.length),
                    const SizedBox(height: 16),
                    DayStatusCard(dayLog: _dayLog),
                    const SizedBox(height: 16),
                    if (pending.isEmpty)
                      const Card(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: Text('No hay tareas pendientes para hoy.', textAlign: TextAlign.center),
                        ),
                      )
                    else
                      Card(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Padding(
                              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                              child: Text('Pendientes', style: Theme.of(context).textTheme.titleMedium),
                            ),
                            ...pending.map((t) => TaskTile(task: t, onChanged: (_) => _toggleTask(t))),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openChat(ChatMode.free),
        icon: const Icon(Icons.chat),
        label: const Text('Hablar con Claude'),
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/screens/dashboard_screen.dart
git commit -m "feat: agregar DashboardScreen con tareas pendientes y acceso al chat"
```

---

## Task 10: Tasks Screen

**Files:**
- Create: `lib/screens/tasks_screen.dart`

- [ ] **Step 1: Crear lib/screens/tasks_screen.dart**

```dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/database.dart';
import '../models/task.dart';
import '../widgets/task_tile.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final _db = DatabaseService();
  final _controller = TextEditingController();
  List<Task> _tasks = [];

  String get _today => DateFormat('yyyy-MM-dd').format(DateTime.now());

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final tasks = await _db.getTasksForDate(_today);
    if (mounted) setState(() => _tasks = tasks);
  }

  Future<void> _addTask() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    await _db.addTasks([text], _today);
    _controller.clear();
    _load();
  }

  Future<void> _toggleTask(Task task) async {
    await _db.updateTaskStatus(task.id!, task.isPending ? 'done' : 'pending');
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tareas de hoy')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Agregar tarea...',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    onSubmitted: (_) => _addTask(),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(onPressed: _addTask, child: const Text('Agregar')),
              ],
            ),
          ),
          Expanded(
            child: _tasks.isEmpty
                ? const Center(child: Text('No hay tareas para hoy.'))
                : ListView(
                    children: _tasks
                        .map((t) => TaskTile(task: t, onChanged: (_) => _toggleTask(t)))
                        .toList(),
                  ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/screens/tasks_screen.dart
git commit -m "feat: agregar TasksScreen con lista y campo para agregar tareas"
```

---

## Task 11: Chat Screen

**Files:**
- Create: `lib/screens/chat_screen.dart`

- [ ] **Step 1: Crear lib/screens/chat_screen.dart**

```dart
import 'package:flutter/material.dart';
import '../core/anthropic_client.dart';
import '../core/database.dart';
import '../core/secure_storage.dart';

class ChatScreen extends StatefulWidget {
  final ChatMode mode;
  final String today;

  const ChatScreen({super.key, required this.mode, required this.today});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _db = DatabaseService();
  final _storage = SecureStorage();
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatMessage> _history = [];
  List<String> _taskTexts = [];
  bool _loading = false;
  AnthropicClient? _client;

  String get _modeLabel => switch (widget.mode) {
        ChatMode.morning => 'Planificación matutina',
        ChatMode.night => 'Revisión nocturna',
        ChatMode.free => 'Chat con Claude',
      };

  @override
  void initState() {
    super.initState();
    _init();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _init() async {
    final apiKey = await _storage.getApiKey();
    final tasks = await _db.getTasksForDate(widget.today);
    _taskTexts = tasks.map((t) => '${t.isPending ? "[ ]" : "[x]"} ${t.text}').toList();
    _client = AnthropicClient(apiKey: apiKey!);

    if (widget.mode != ChatMode.free) {
      await _sendOpener();
    }
  }

  Future<void> _sendOpener() async {
    await _sendToApi('Iniciá la conversación.');
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _loading) return;
    _controller.clear();
    await _sendToApi(text);
  }

  Future<void> _sendToApi(String userText) async {
    setState(() {
      _history.add(ChatMessage(role: 'user', content: userText));
      _loading = true;
    });
    _scrollToBottom();

    try {
      final reply = await _client!.sendMessage(
        history: _history,
        mode: widget.mode,
        tasks: _taskTexts,
        date: widget.today,
      );

      if (reply.toLowerCase().contains('tarea') && widget.mode == ChatMode.morning) {
        final lines = reply.split('\n').where((l) => l.trim().startsWith('-')).map((l) => l.replaceFirst('-', '').trim()).where((l) => l.isNotEmpty).toList();
        if (lines.isNotEmpty) {
          await _db.addTasks(lines, widget.today);
          await _db.saveMorningPlan(reply, widget.today);
        }
      }
      if (widget.mode == ChatMode.night) {
        await _db.saveNightReview(reply, widget.today);
      }

      setState(() {
        _history.add(ChatMessage(role: 'assistant', content: reply));
        _loading = false;
      });
    } on AnthropicException catch (e) {
      setState(() {
        _history.add(ChatMessage(role: 'assistant', content: 'Error: ${e.message}'));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_modeLabel)),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(12),
              itemCount: _history.where((m) => m.role != 'user' || m.content != 'Iniciá la conversación.').length,
              itemBuilder: (context, index) {
                final visible = _history.where((m) => m.role != 'user' || m.content != 'Iniciá la conversación.').toList();
                final msg = visible[index];
                final isUser = msg.role == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
                    decoration: BoxDecoration(
                      color: isUser ? Theme.of(context).colorScheme.primary : Theme.of(context).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      msg.content,
                      style: TextStyle(color: isUser ? Colors.white : null),
                    ),
                  ),
                );
              },
            ),
          ),
          if (_loading) const LinearProgressIndicator(),
          Padding(
            padding: EdgeInsets.only(left: 12, right: 12, bottom: MediaQuery.of(context).viewInsets.bottom + 12, top: 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(hintText: 'Escribí un mensaje...', border: OutlineInputBorder(), isDense: true),
                    onSubmitted: (_) => _sendMessage(),
                    textInputAction: TextInputAction.send,
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(onPressed: _loading ? null : _sendMessage, child: const Icon(Icons.send)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/screens/chat_screen.dart
git commit -m "feat: agregar ChatScreen con burbujas de chat y modos morning/night/free"
```

---

## Task 12: Settings Screen

**Files:**
- Create: `lib/screens/settings_screen.dart`

- [ ] **Step 1: Crear lib/screens/settings_screen.dart**

```dart
import 'package:flutter/material.dart';
import '../core/secure_storage.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _storage = SecureStorage();
  final _keyController = TextEditingController();
  bool _saved = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _keyController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final key = await _storage.getApiKey();
    if (key != null) _keyController.text = key;
    setState(() => _loading = false);
  }

  Future<void> _save() async {
    final key = _keyController.text.trim();
    if (key.isEmpty) return;
    await _storage.saveApiKey(key);
    setState(() => _saved = true);
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) setState(() => _saved = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Configuración')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('API Key de Anthropic', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _keyController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.key),
                    hintText: 'sk-ant-...',
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: _save,
                  child: Text(_saved ? 'Guardado ✓' : 'Guardar'),
                ),
                const Divider(height: 32),
                ListTile(
                  leading: const Icon(Icons.schedule),
                  title: const Text('Notificaciones'),
                  subtitle: const Text('08:00 · 08:30 · 23:00'),
                  trailing: const Icon(Icons.info_outline),
                  onTap: () => showDialog(
                    context: context,
                    builder: (_) => AlertDialog(
                      title: const Text('Horarios fijos'),
                      content: const Text('Las notificaciones se envían a las 08:00, 08:30 y 23:00 todos los días. Para cambiar los horarios, reiniciá la app después de modificarlos en el código.'),
                      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/screens/settings_screen.dart
git commit -m "feat: agregar SettingsScreen para API key"
```

---

## Task 13: Notification Service

**Files:**
- Create: `lib/services/notification_service.dart`
- Modify: `android/app/src/main/AndroidManifest.xml`

- [ ] **Step 1: Crear lib/services/notification_service.dart**

```dart
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:workmanager/workmanager.dart';

const _kMorningTask = 'morning_notification';
const _kReminderTask = 'reminder_notification';
const _kNightTask = 'night_notification';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final _plugin = FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _plugin.initialize(
      const InitializationSettings(android: android),
    );
    await _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
  }

  Future<void> show({required int id, required String title, required String body}) async {
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'daily_agent_channel',
        'Agente Diario',
        channelDescription: 'Notificaciones del agente diario',
        importance: Importance.high,
        priority: Priority.high,
      ),
    );
    await _plugin.show(id, title, body, details);
  }

  Future<void> scheduleAll() async {
    await Workmanager().cancelAll();

    // 08:00 — planificación
    await Workmanager().registerPeriodicTask(
      _kMorningTask,
      _kMorningTask,
      frequency: const Duration(hours: 24),
      initialDelay: _delayUntil(8, 0),
      constraints: Constraints(networkType: NetworkType.not_required),
    );

    // 08:30 — recordatorio
    await Workmanager().registerPeriodicTask(
      _kReminderTask,
      _kReminderTask,
      frequency: const Duration(hours: 24),
      initialDelay: _delayUntil(8, 30),
      constraints: Constraints(networkType: NetworkType.not_required),
    );

    // 23:00 — revisión nocturna
    await Workmanager().registerPeriodicTask(
      _kNightTask,
      _kNightTask,
      frequency: const Duration(hours: 24),
      initialDelay: _delayUntil(23, 0),
      constraints: Constraints(networkType: NetworkType.not_required),
    );
  }

  Duration _delayUntil(int hour, int minute) {
    final now = DateTime.now();
    var target = DateTime(now.year, now.month, now.day, hour, minute);
    if (target.isBefore(now)) target = target.add(const Duration(days: 1));
    return target.difference(now);
  }

  Future<void> handleScheduledTask(String taskName) async {
    switch (taskName) {
      case _kMorningTask:
        await show(id: 1, title: 'Buenos días ☀️', body: '¿Cuáles son tus tareas de hoy?');
      case _kReminderTask:
        await show(id: 2, title: 'Recordatorio', body: 'Todavía no cargaste tus tareas del día.');
      case _kNightTask:
        await show(id: 3, title: 'Revisión nocturna 🌙', body: '¿Cómo te fue hoy?');
    }
  }
}
```

- [ ] **Step 2: Agregar permisos en AndroidManifest.xml**

Abrir `android/app/src/main/AndroidManifest.xml` y agregar dentro de `<manifest>` (antes de `<application>`):

```xml
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
<uses-permission android:name="android.permission.VIBRATE"/>
<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
<uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM"/>
```

Y dentro de `<application>`:

```xml
<receiver
    android:name="com.dexterous.flutterlocalnotifications.ScheduledNotificationBootReceiver"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED"/>
    </intent-filter>
</receiver>
```

- [ ] **Step 3: Commit**

```bash
git add lib/services/notification_service.dart android/app/src/main/AndroidManifest.xml
git commit -m "feat: agregar NotificationService con WorkManager para notificaciones diarias"
```

---

## Task 14: Compilar APK y probar

- [ ] **Step 1: Verificar que compila sin errores**

```bash
flutter analyze
```
Esperado: sin errores (puede haber warnings menores).

- [ ] **Step 2: Ejecutar todos los tests**

```bash
flutter test
```
Esperado: `All tests passed!`

- [ ] **Step 3: Compilar APK de release**

```bash
flutter build apk --release
```
Esperado:
```
Built build/app/outputs/flutter-apk/app-release.apk (XX.X MB)
```

- [ ] **Step 4: Instalar en dispositivo Android (con USB debugging activo)**

```bash
flutter install
```
O copiar el APK desde `build/app/outputs/flutter-apk/app-release.apk` al teléfono.

- [ ] **Step 5: Commit final**

```bash
git add -A
git commit -m "feat: app Android completa lista para distribución"
```
