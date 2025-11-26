\# Installation



\## Voraussetzungen



\- Windows 10/11 (empfohlen), Linux/macOS mit manuellen Anpassungen

\- Python 3.11 x64

\- Git

\- NVIDIA-GPU mit CUDA ≥ 12.0 für GPU-Beschleunigung (optional, empfohlen)



\## Automatische Installation (empfohlen, Windows)



git clone https://github.com/Lautloserspieler/JarvisCore.git

cd JarvisCore

py -3.11 bootstrap.py --run



text



Der Bootstrap-Skript:



\- erstellt eine virtuelle Umgebung,

\- installiert alle Abhängigkeiten,

\- prüft CUDA-Status,

\- startet JarvisCore.



\## Manuelle Installation



git clone https://github.com/Lautloserspieler/JarvisCore.git

cd JarvisCore



python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python main.py



text



Für Linux/macOS entsprechend `source venv/bin/activate` nutzen.

