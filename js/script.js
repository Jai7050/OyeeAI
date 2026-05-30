const chat = document.getElementById("chat");
const input = document.getElementById("input");
const composerForm = document.getElementById("composerForm");
const voiceBtn = document.getElementById("voiceBtn");
const clearBtn = document.getElementById("clearBtn");
const locationBtn = document.getElementById("locationBtn");
const statusPill = document.getElementById("statusPill");
const micState = document.getElementById("micState");
const liveTime = document.getElementById("liveTime");
const voiceVisualizer = document.getElementById("voiceVisualizer");
const quickButtons = document.querySelectorAll(".quick-actions button");

let currentLocation = { lat: null, lon: null };
let recognition = null;
let speaking = false;

function updateClock() {
  const now = new Date();
  liveTime.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
updateClock();
setInterval(updateClock, 1000);

function setStatus(text, active = false) {
  statusPill.textContent = text;
  statusPill.classList.toggle("active", active);
}

function setWave(on) {
  voiceVisualizer.classList.toggle("active", on);
}

function appendMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;

  const roleEl = document.createElement("span");
  roleEl.className = "role";
  roleEl.textContent = role === "user" ? "You" : "OyeAI";

  const body = document.createElement("div");
  body.textContent = text;

  wrap.appendChild(roleEl);
  wrap.appendChild(body);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;

  // 🔥 SAVE HISTORY
  let history = JSON.parse(localStorage.getItem("oyeai_history")) || [];
  history.push({ role, text });
  localStorage.setItem("oyeai_history", JSON.stringify(history));
}

function speakText(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();

  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 1;
  utter.pitch = 1;
  utter.lang = "hi-IN";

  utter.onstart = () => {
    speaking = true;
    setStatus("Speaking", true);
    setWave(true);
  };
  utter.onend = () => {
    speaking = false;
    setStatus("Idle", false);
    setWave(false);
  };
  utter.onerror = () => {
    speaking = false;
    setStatus("Idle", false);
    setWave(false);
  };
  window.speechSynthesis.speak(utter);
}

async function sendMessage(message) {
  const text = (message ?? input.value).trim();
  if (!text) return;

  appendMessage("user", text);
  input.value = "";
  setStatus("Thinking", true);
  setWave(true);

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        lat: currentLocation.lat,
        lon: currentLocation.lon
      })
    });

    const data = await res.json();
    const reply = data.response || "No response received.";
    appendMessage("ai", reply);

    if (data.action === "open_url" && data.url) {
      window.open(data.url, "_blank");
    }

    if (data.speak !== false) {
      speakText(reply);
    } else {
      setStatus("Idle", false);
      setWave(false);
    }
  } catch (err) {
    appendMessage("ai", "Request failed. Check your internet or server.");
    setStatus("Idle", false);
    setWave(false);
    console.error(err);
  }
}

function initRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.disabled = true;
    voiceBtn.title = "Speech recognition is not supported in this browser.";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    micState.textContent = "On";
    setStatus("Listening", true);
    setWave(true);
  };

  recognition.onend = () => {
    micState.textContent = "Off";
    if (!speaking) {
      setStatus("Idle", false);
      setWave(false);
    }
  };

  recognition.onerror = () => {
    micState.textContent = "Off";
    setStatus("Idle", false);
    setWave(false);
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    input.value = transcript;
    sendMessage(transcript);
  };
}

composerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

voiceBtn.addEventListener("click", () => {
  if (recognition) recognition.start();
});

clearBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  setStatus("Idle", false);
  setWave(false);
});

quickButtons.forEach(btn => {
  btn.addEventListener("click", () => sendMessage(btn.dataset.msg));
});

locationBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    appendMessage("ai", "Location is not supported in this browser.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      currentLocation.lat = pos.coords.latitude;
      currentLocation.lon = pos.coords.longitude;
      appendMessage("ai", "Location added. You can now ask for weather.");
    },
    () => appendMessage("ai", "Location permission denied.")
  );
});

appendMessage("ai", "Hi, I am OyeAI. Try: open notepad, weather in Mumbai, time, or ask me anything.");
initRecognition();



