"""
Russian Roulette

Endpoints
---------
GET  /           — SPA with embedded HTML/CSS/JS
POST /api/spin   — Pull the trigger (returns JSON)
POST /api/reset  — Reset the game
GET  /health     — Health-check for Docker / CI / Ansible
"""

from __future__ import annotations

import logging
import os
import secrets
from typing import Any

from flask import Flask, jsonify, session

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    #Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    #Constants
    CHAMBERS = 6  # revolver ammo

    #Helpers
    def _init_session() -> None:
        """Ensure the session has the required game keys."""
        if "round" not in session:
            session["round"] = 0
            session["alive"] = True
            session["bullet"] = secrets.randbelow(CHAMBERS)
            session["current_chamber"] = 0

    #Routes
    @app.route("/")
    def index() -> str:
        """Serve the single-page application."""
        return HTML_PAGE

    @app.route("/api/spin", methods=["POST"])
    def spin() -> tuple[Any, int]:
        """Pull the trigger. Returns JSON with game state."""
        _init_session()

        if not session["alive"]:
            return jsonify(
                alive=False,
                chamber=session["current_chamber"],
                round=session["round"],
                message="Game over. Press 'New Game'.",
            ), 200

        session["round"] += 1
        chamber = session["current_chamber"]
        bullet = session["bullet"]

        if chamber == bullet:
            session["alive"] = False
            logger.info("BANG! Game over after %d rounds.", session["round"])
            return jsonify(
                alive=False,
                chamber=chamber + 1,
                round=session["round"],
                message="BANG! 💀 Game Over.",
            ), 200

        session["current_chamber"] = (chamber + 1) % CHAMBERS
        logger.info("Click. Round %d survived (chamber %d).", session["round"], chamber + 1)
        return jsonify(
            alive=True,
            chamber=chamber + 1,
            round=session["round"],
            message="Click... you survived. 🎯",
        ), 200

    @app.route("/api/reset", methods=["POST"])
    def reset() -> tuple[Any, int]:
        """Reset the game to a fresh state."""
        session.clear()
        _init_session()
        logger.info("Game reset.")
        return jsonify(
            alive=True,
            chamber=0,
            round=0,
            message="New game. Good luck...",
        ), 200

    @app.route("/health")
    def health() -> tuple[Any, int]:
        """Health-check endpoint for Docker / CI / monitoring."""
        return jsonify(status="ok"), 200

    return app


# Embedded SPA

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<meta name="description" content="Russian Roulette — a browser mini-game on Flask."/>
<title>Russian Roulette </title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"/>
<style>
/* Reset & Base  */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0a0f;--surface:#14141f;--surface2:#1e1e2e;
  --red:#e63946;--green:#06d6a0;--gold:#ffd60a;
  --text:#e0e0e8;--muted:#6c7086;
  --font:'Inter',system-ui,sans-serif;
}
html{font-size:16px}
body{
  font-family:var(--font);background:var(--bg);color:var(--text);
  min-height:100vh;display:flex;flex-direction:column;align-items:center;
  justify-content:center;overflow:hidden;
  background-image:
    radial-gradient(ellipse 80% 60% at 50% -20%,rgba(230,57,70,.12),transparent),
    radial-gradient(ellipse 60% 50% at 80% 110%,rgba(6,214,160,.08),transparent);
}

/* Card */
.card{
  background:var(--surface);border:1px solid rgba(255,255,255,.06);
  border-radius:24px;padding:3rem 2.5rem;max-width:420px;width:92%;
  text-align:center;position:relative;
  box-shadow:0 8px 40px rgba(0,0,0,.5);
}

h1{
  font-size:1.75rem;font-weight:800;margin-bottom:.25rem;
  background:linear-gradient(135deg,var(--gold),var(--red));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.subtitle{color:var(--muted);font-size:.85rem;margin-bottom:2rem}

/* Cylinder */
.cylinder-wrap{
  width:180px;height:180px;margin:0 auto 2rem;position:relative;
}
.cylinder{
  width:100%;height:100%;border-radius:50%;
  border:3px solid rgba(255,255,255,.08);
  position:relative;transition:transform .6s cubic-bezier(.4,2,.6,1);
  background:var(--surface2);
}
.cylinder.spin{animation:spinAnim .6s cubic-bezier(.4,2,.6,1)}
@keyframes spinAnim{
  0%{transform:rotate(0)}
  100%{transform:rotate(360deg)}
}
.chamber{
  position:absolute;width:28px;height:28px;border-radius:50%;
  background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.1);
  top:50%;left:50%;transition:background .3s,border-color .3s,box-shadow .3s;
}
.chamber:nth-child(1){transform:translate(-50%,-50%) rotate(0deg)   translateY(-60px)}
.chamber:nth-child(2){transform:translate(-50%,-50%) rotate(60deg)  translateY(-60px)}
.chamber:nth-child(3){transform:translate(-50%,-50%) rotate(120deg) translateY(-60px)}
.chamber:nth-child(4){transform:translate(-50%,-50%) rotate(180deg) translateY(-60px)}
.chamber:nth-child(5){transform:translate(-50%,-50%) rotate(240deg) translateY(-60px)}
.chamber:nth-child(6){transform:translate(-50%,-50%) rotate(300deg) translateY(-60px)}
.chamber.active{
  background:var(--gold);border-color:var(--gold);
  box-shadow:0 0 12px rgba(255,214,10,.5);
}
.chamber.dead{
  background:var(--red);border-color:var(--red);
  box-shadow:0 0 16px rgba(230,57,70,.6);
}

/* HUD */
.hud{display:flex;justify-content:center;gap:2rem;margin-bottom:1.5rem}
.hud-item{font-size:.8rem;color:var(--muted)}
.hud-item span{display:block;font-size:1.6rem;font-weight:800;color:var(--text)}

/* Message */
.message{
  min-height:2.2rem;font-size:1rem;font-weight:600;
  margin-bottom:1.5rem;transition:color .3s;
}
.message.alive{color:var(--green)}
.message.dead{color:var(--red)}

/* Buttons */
.actions{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap}
.btn{
  font-family:var(--font);font-weight:600;font-size:.95rem;
  border:none;border-radius:14px;padding:.85rem 2rem;cursor:pointer;
  transition:transform .15s,box-shadow .2s,opacity .2s;
}
.btn:active{transform:scale(.96)}
.btn-trigger{
  background:linear-gradient(135deg,var(--red),#b91c1c);color:#fff;
  box-shadow:0 4px 20px rgba(230,57,70,.35);
}
.btn-trigger:hover{box-shadow:0 6px 28px rgba(230,57,70,.5)}
.btn-trigger:disabled{opacity:.4;cursor:not-allowed}
.btn-reset{
  background:var(--surface2);color:var(--text);
  border:1px solid rgba(255,255,255,.1);
}
.btn-reset:hover{background:rgba(255,255,255,.08)}

/* Footer */
.footer{
  margin-top:1.5rem;font-size:.7rem;color:var(--muted);opacity:.6;
}

/* Shake animation */
.shake{animation:shakeAnim .5s}
@keyframes shakeAnim{
  0%,100%{transform:translateX(0)}
  20%{transform:translateX(-12px)}
  40%{transform:translateX(12px)}
  60%{transform:translateX(-8px)}
  80%{transform:translateX(8px)}
}

/* Responsive */
@media(max-width:480px){
  .card{padding:2rem 1.5rem;border-radius:18px}
  h1{font-size:1.4rem}
  .cylinder-wrap{width:150px;height:150px}
  .chamber{width:22px;height:22px}
  .chamber:nth-child(1){transform:translate(-50%,-50%) rotate(0deg)   translateY(-48px)}
  .chamber:nth-child(2){transform:translate(-50%,-50%) rotate(60deg)  translateY(-48px)}
  .chamber:nth-child(3){transform:translate(-50%,-50%) rotate(120deg) translateY(-48px)}
  .chamber:nth-child(4){transform:translate(-50%,-50%) rotate(180deg) translateY(-48px)}
  .chamber:nth-child(5){transform:translate(-50%,-50%) rotate(240deg) translateY(-48px)}
  .chamber:nth-child(6){transform:translate(-50%,-50%) rotate(300deg) translateY(-48px)}
}
</style>
</head>
<body>

<div class="card" id="card">
  <h1>Russian Roulette</h1>
  <p class="subtitle">6 chambers. 1 bullet. Good luck.</p>

  <div class="cylinder-wrap">
    <div class="cylinder" id="cylinder">
      <div class="chamber" id="ch1"></div>
      <div class="chamber" id="ch2"></div>
      <div class="chamber" id="ch3"></div>
      <div class="chamber" id="ch4"></div>
      <div class="chamber" id="ch5"></div>
      <div class="chamber" id="ch6"></div>
    </div>
  </div>

  <div class="hud">
    <div class="hud-item">Round<span id="roundNum">0</span></div>
    <div class="hud-item">Chamber<span id="chamberNum">-</span></div>
  </div>

  <div class="message" id="msg">Press "Pull the trigger" to start</div>

  <div class="actions">
    <button class="btn btn-trigger" id="triggerBtn">Pull the trigger</button>
    <button class="btn btn-reset"   id="resetBtn">New game</button>
  </div>

  <p class="footer">Flask &bull; Docker &bull; CI/CD &bull; Ansible</p>
</div>

<script>
(function(){
  "use strict";

  const triggerBtn  = document.getElementById("triggerBtn");
  const resetBtn    = document.getElementById("resetBtn");
  const msgEl       = document.getElementById("msg");
  const roundEl     = document.getElementById("roundNum");
  const chamberEl   = document.getElementById("chamberNum");
  const cylinderEl  = document.getElementById("cylinder");
  const cardEl      = document.getElementById("card");
  const chambers    = Array.from(document.querySelectorAll(".chamber"));

  let busy = false;

  function clearChambers(){
    chambers.forEach(function(c){ c.classList.remove("active","dead"); });
  }

  function highlightChamber(idx, dead){
    clearChambers();
    if(idx >= 1 && idx <= 6){
      const c = chambers[idx - 1];
      c.classList.add(dead ? "dead" : "active");
    }
  }

  async function pull(){
    if(busy) return;
    busy = true;
    triggerBtn.disabled = true;

    cylinderEl.classList.remove("spin");
    void cylinderEl.offsetWidth;
    cylinderEl.classList.add("spin");

    try{
      const res  = await fetch("/api/spin", { method:"POST" });
      const data = await res.json();

      roundEl.textContent   = data.round;
      chamberEl.textContent = data.chamber;
      msgEl.textContent     = data.message;

      if(data.alive){
        msgEl.className = "message alive";
        highlightChamber(data.chamber, false);
        triggerBtn.disabled = false;
      } else {
        msgEl.className = "message dead";
        highlightChamber(data.chamber, true);
        cardEl.classList.add("shake");
        setTimeout(function(){ cardEl.classList.remove("shake"); }, 500);
      }
    } catch(err){
      msgEl.textContent = "Network error — please try again.";
      msgEl.className   = "message dead";
      triggerBtn.disabled = false;
    }
    busy = false;
  }

  async function reset(){
    if(busy) return;
    busy = true;
    try{
      const res  = await fetch("/api/reset", { method:"POST" });
      const data = await res.json();
      roundEl.textContent   = data.round;
      chamberEl.textContent = "-";
      msgEl.textContent     = data.message;
      msgEl.className       = "message";
      clearChambers();
      triggerBtn.disabled = false;
    } catch(err){
      msgEl.textContent = "Network error.";
      msgEl.className   = "message dead";
    }
    busy = false;
  }

  triggerBtn.addEventListener("click", pull);
  resetBtn.addEventListener("click", reset);
})();
</script>
</body>
</html>
"""


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
