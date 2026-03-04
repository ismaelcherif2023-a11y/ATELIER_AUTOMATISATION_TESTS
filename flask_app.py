from flask import Flask
import requests
import json
import os
import time
from datetime import datetime

app = Flask(__name__)
METRICS_FILE = os.path.join(os.path.dirname(__file__), "metrics.json")
API_URL = "https://api.open-meteo.com/v1/forecast?latitude=50.63&longitude=3.06&current_weather=true"

def tester_api():
    resultat = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": None,
        "temps_reponse_ms": None,
        "succes": False,
        "message": ""
    }
    try:
        debut = time.time()
        response = requests.get(API_URL, timeout=10)
        fin = time.time()
        resultat["status_code"] = response.status_code
        resultat["temps_reponse_ms"] = round((fin - debut) * 1000, 2)
        resultat["succes"] = response.status_code == 200
        resultat["message"] = "OK" if resultat["succes"] else "Erreur HTTP"
    except Exception as e:
        resultat["status_code"] = "ERREUR"
        resultat["message"] = str(e)
    try:
        with open(METRICS_FILE, "r") as f:
            donnees = json.load(f)
    except:
        donnees = []
    donnees.append(resultat)
    donnees = donnees[-100:]
    with open(METRICS_FILE, "w") as f:
        json.dump(donnees, f, indent=2)
    return resultat

@app.route("/")
def dashboard():
    tester_api()
    try:
        with open(METRICS_FILE, "r") as f:
            donnees = json.load(f)
    except:
        donnees = []
    total = len(donnees)
    succes = sum(1 for d in donnees if d["succes"])
    echecs = total - succes
    taux_dispo = round((succes / total * 100), 2) if total > 0 else 0
    temps_list = [d["temps_reponse_ms"] for d in donnees if d["temps_reponse_ms"]]
    temps_moyen = round(sum(temps_list) / len(temps_list), 2) if temps_list else 0
    temps_max = max(temps_list) if temps_list else 0
    temps_min = min(temps_list) if temps_list else 0

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Monitor</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="30">
        <style>
            body {{ font-family: Arial; margin: 0; background: #1a1a2e; color: white; }}
            .header {{ background: #16213e; padding: 20px 40px; border-bottom: 3px solid #0f3460; }}
            h1 {{ margin: 0; color: #e94560; }}
            .sub {{ color: #aaa; margin-top: 5px; }}
            .container {{ padding: 30px 40px; }}
            .cards {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
            .card {{ background: #16213e; border-radius: 12px; padding: 25px;
                     text-align: center; border: 1px solid #0f3460; flex: 1; min-width: 130px; }}
            .card h2 {{ font-size: 2em; margin: 0; color: #e94560; }}
            .card p {{ margin: 5px 0 0; color: #aaa; font-size: 0.9em; }}
            .green h2 {{ color: #2ecc71; }}
            .blue h2 {{ color: #3498db; }}
            .orange h2 {{ color: #f39c12; }}
            table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 12px; }}
            th {{ background: #0f3460; padding: 12px; color: #e94560; text-align: center; }}
            td {{ padding: 10px; text-align: center; border-bottom: 1px solid #0f3460; }}
            .ok {{ background: #2ecc71; color: black; padding: 3px 10px; border-radius: 20px; font-size: 0.85em; }}
            .ko {{ background: #e74c3c; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.85em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 API Monitoring Dashboard</h1>
            <p class="sub">API testée : Open-Meteo (Météo Lille) — Rafraîchissement auto toutes les 30s</p>
        </div>
        <div class="container">
            <div class="cards">
                <div class="card green"><h2>{taux_dispo}%</h2><p>Disponibilité</p></div>
                <div class="card blue"><h2>{temps_moyen} ms</h2><p>Temps moyen</p></div>
                <div class="card orange"><h2>{temps_min} ms</h2><p>Temps min</p></div>
                <div class="card orange"><h2>{temps_max} ms</h2><p>Temps max</p></div>
                <div class="card"><h2>{total}</h2><p>Tests total</p></div>
                <div class="card"><h2>{succes}/{echecs}</h2><p>✅ OK / ❌ KO</p></div>
            </div>
            <table>
                <tr>
                    <th>#</th><th>Timestamp</th><th>Status</th>
                    <th>Temps (ms)</th><th>Message</th><th>Résultat</th>
                </tr>
                {"".join(f'''<tr>
                    <td>{total - i}</td>
                    <td>{d["timestamp"]}</td>
                    <td>{d["status_code"]}</td>
                    <td>{d["temps_reponse_ms"] if d["temps_reponse_ms"] else "—"}</td>
                    <td>{d.get("message", "")}</td>
                    <td><span class="{'ok' if d['succes'] else 'ko'}">
                        {'✅ OK' if d['succes'] else '❌ FAIL'}</span></td>
                </tr>''' for i, d in enumerate(reversed(donnees)))}
            </table>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)
