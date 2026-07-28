# ALIBEL - Prototipo MVP

Este es el repositorio del MVP funcional de ALIBEL para detección de anomalías y verificación de emergencias usando el acelerómetro y giroscopio del teléfono.

## Estructura
- `/backend`: API en FastAPI, Modelo IsolationForest, Dashboard en tiempo real.
- `/app`: Aplicación móvil mínima en Flutter.
- `/scripts`: Scripts de simulación y entrenamiento del modelo.

## 1. Ejecutar el Servidor (Backend)
En una terminal en la carpeta principal del proyecto (`ALIBEL`):
1. Activa el entorno virtual:
   ```powershell
   .\venv\Scripts\activate
   ```
2. Ejecuta el servidor FastAPI con Uvicorn:
   ```powershell
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Abre el Dashboard en tu navegador: [http://localhost:8000](http://localhost:8000)

## 2. Simulador (Opcional - para probar sin teléfono)
Abre otra terminal, activa el entorno virtual y ejecuta:
```powershell
.\venv\Scripts\activate
python scripts\simulate_device.py
```
Verás cómo se envían datos normales y anómalos, y el Dashboard reaccionará en tiempo real.

## 3. Instalación de Flutter y Pruebas en Android / iPhone

### Instalación de Flutter (Windows)
1. Descarga el SDK de Flutter desde [la página oficial](https://docs.flutter.dev/get-started/install/windows).
2. Extrae el archivo `.zip` en `C:\src\flutter`.
3. Añade `C:\src\flutter\bin` a la variable de entorno `PATH` de tu sistema operativo.
4. Abre una nueva terminal y ejecuta `flutter doctor` para comprobar que todo está bien.

### Pruebas en Android
1. Instala **Android Studio**.
2. Abre Android Studio y descarga un emulador desde el *Device Manager* o conecta tu teléfono Android mediante un cable USB (con "Depuración USB" activada en Opciones de Desarrollador).
3. En la terminal de VSCode (o PowerShell), ve a la carpeta de la app:
   ```powershell
   cd app
   flutter pub get
   flutter run
   ```

### Pruebas en iPhone
> **Nota:** Para compilar una app de Flutter hacia iOS, **se requiere obligatoriamente una computadora Mac (macOS)** con Xcode instalado. Si estás en Windows, no puedes compilar para iPhone directamente usando cables.
> **Alternativas para probar en iPhone si solo tienes Windows:**
> - Usar servicios de CI/CD como **Codemagic** o **GitHub Actions** para compilar el `.ipa` en la nube.
> - Si consigues una Mac, simplemente abres la carpeta, instalas Xcode, conectas el iPhone y corres `flutter run`.

## Conexión de la App al Servidor Local
Para que el teléfono físico se comunique con el servidor en tu computadora, ambos deben estar conectados al mismo WiFi.
1. Averigua la IP local de tu computadora (por ejemplo, `192.168.1.15`) ejecutando `ipconfig` en Windows.
2. En `app/lib/main.dart`, cambia `final String serverIp = '10.0.2.2:8000';` por tu IP real: `final String serverIp = '192.168.1.15:8000';`.
3. Vuelve a ejecutar la app.
