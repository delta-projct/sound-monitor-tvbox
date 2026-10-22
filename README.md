# sound-monitor-tvbox
Sistem pemantauan suara otomatis (headless) berbasis TV Box Armbian menggunakan Python, Flask, dan WebRTC VAD untuk mendeteksi suara secara real-time.

## Fitur utama
* Mendeteksi kebisingan dan tingkat suara menggunakan microfon USB.
* Berjalan otomatis di latar belakang sebagai *service* linux.
* Dilengkapi Web Server lokal (Flask) untuk memantau status suara.

  ## Teknologi yang digunakan
  * PYthon3
  * Flask (Web Server)
  * WebRTC VAD (Voive Activity Detection)
  * Armbian OS/Linux
