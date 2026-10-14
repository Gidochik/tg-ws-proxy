name: Build Custom TG WS Proxy APK
on: [push, workflow_dispatch]

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - name: Clone original Flowseal/tg-ws-proxy
        run: |
          git clone https://github.com/Flowseal/tg-ws-proxy.git flowseal_core

      - name: Create buildozer.spec
        run: |
          cat << 'EOF' > buildozer.spec
          [app]
          title = TG WS Proxy
          package.name = tgwsproxy
          package.domain = org.flowseal.custom
          source.dir = .
          source.include_exts = py,json,pem,crt,txt
          version = 1.11.2
          requirements = python3,kivy==2.3.0,cryptography,websockets,aiohttp,certifi,h2
          orientation = portrait
          fullscreen = 0
          android.permissions = INTERNET,ACCESS_NETWORK_STATE
          android.api = 33
          android.minapi = 24
          android.archs = arm64-v8a
          EOF

      - name: Build APK with Buildozer
        uses: ArtemSBulgakov/buildozer-action@v1
        with:
          workdir: .
          buildozer_version: master

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: TG-WS-Proxy-Custom-APK
          path: bin/*.apk
