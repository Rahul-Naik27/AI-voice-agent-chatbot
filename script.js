const recordBtn = document.getElementById("recordBtn");
const micLabel = recordBtn.querySelector(".mic__label");
const statusEl = document.getElementById("status");
const chatEl = document.getElementById("chat");
const player = document.getElementById("player");

let state = "idle";
let mediaRecorder;
let chunks = [];
let stream;

const sessionId = Date.now().toString();

function setState(next) {
  state = next;
  statusEl.textContent = next;

  if (next === "recording") {
    micLabel.textContent = "Stop";
    recordBtn.classList.add("recording");
  } else if (next === "uploading") {
    micLabel.textContent = "Uploading...";
    recordBtn.classList.remove("recording");
  } else if (next === "speaking") {
    micLabel.textContent = "Speaking...";
    recordBtn.classList.remove("recording");
  } else {
    micLabel.textContent = "Start";
    recordBtn.classList.remove("recording");
  }
}

function addMsg(text, who = "agent") {
  const div = document.createElement("div");
  div.className = "msg msg--" + who;
  chatEl.appendChild(div);

  if (who === "user" || who === "system") {
    div.textContent = text;
  } else {
    let i = 0;
    function typeChar() {
      if (i < text.length) {
        div.textContent += text.charAt(i);
        i++;
        if (i % 2 === 0) chatEl.scrollTop = chatEl.scrollHeight;
        setTimeout(typeChar, 25);
      }
    }
    typeChar();
  }

  const atBottom = chatEl.scrollHeight - chatEl.scrollTop <= chatEl.clientHeight + 5;
  if (atBottom) chatEl.scrollTop = chatEl.scrollHeight;
}

async function startRecording() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];

    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      uploadAudio(new Blob(chunks, { type: "audio/webm" }));
    };

    mediaRecorder.start();
    setState("recording");
  } catch (err) {
    console.error(err);
    addMsg("⚠️ Mic permission denied", "system");
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    setState("uploading");
  }
}

async function uploadAudio(blob) {
  try {
    // ✅ Create typing indicator dynamically at the bottom
    const typingDiv = document.createElement("div");
    typingDiv.className = "msg msg--system";
    typingDiv.textContent = "🤖 Typing...";
    chatEl.appendChild(typingDiv);
    chatEl.scrollTop = chatEl.scrollHeight;

    const form = new FormData();
    form.append("file", blob, "input.webm");

    const res = await fetch(`/agent/chat/${sessionId}`, { method: "POST", body: form });
    const data = await res.json();

    // ✅ Remove typing indicator before showing AI response
    typingDiv.remove();

    if (data.transcript) addMsg("🗣  " + data.transcript, "user");
    if (data.response_text) addMsg("🤖  " + data.response_text, "agent");

    if (data.audio_url) {
      player.src = data.audio_url;
      setState("speaking");
      await player.play();
      player.onended = () => setState("idle");
    } else setState("idle");
  } catch (err) {
    console.error(err);
    addMsg("⚠️ Error getting response", "system");
    setState("idle");
  }
}

recordBtn.addEventListener("click", () => {
  if (state === "idle") startRecording();
  else if (state === "recording") stopRecording();
});
