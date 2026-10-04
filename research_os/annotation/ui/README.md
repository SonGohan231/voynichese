Failed to connect to bus: Operation not permitted
# Blind annotation UI

Static, local-only editor for the frozen A/B packets. It deliberately has no network calls, automated overlays, predictions, hypothesis labels, or split information.

Run from the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory .
```

Open annotator A:

```text
http://127.0.0.1:8000/research_os/annotation/ui/?packet=../packets/annotator-a.packet.json
```

Use `annotator-b.packet.json` in an operationally separate browser profile/device for annotator B. Do not give either annotator access to repository history, `analysis_output`, the `AUTO_CANDIDATE` artifact, the other profile, or exported submissions.

The editor verifies the packet universe hash with Web Crypto, reads only original source paths, stores work in browser `localStorage`, and exports the frozen `blind_annotation.schema.json` shape. Export does not imply scientific validity; run `annotation_gate.py` on both completed files.

Design reference: `design/concept.png`.
