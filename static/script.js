const form = document.getElementById("upload-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const results = document.getElementById("results");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById("audio-input");
  if (!fileInput.files.length) return;

  const formData = new FormData();
  formData.append("audio", fileInput.files[0]);

  submitBtn.disabled = true;
  results.classList.add("hidden");
  statusEl.classList.remove("hidden", "error");
  statusEl.textContent = "Processing audio... this can take a minute for longer lectures.";

  try {
    const res = await fetch("/api/process", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Something went wrong");
    }

    renderResults(data);
    statusEl.classList.add("hidden");
  } catch (err) {
    statusEl.textContent = "Error: " + err.message;
    statusEl.classList.add("error");
  } finally {
    submitBtn.disabled = false;
  }
});

function renderResults(data) {
  document.getElementById("result-title").textContent = data.title || "Lecture Summary";
  document.getElementById("result-summary").textContent = data.summary || "";

  const keyPointsEl = document.getElementById("result-key-points");
  keyPointsEl.innerHTML = "";
  (data.key_points || []).forEach((point) => {
    const li = document.createElement("li");
    li.textContent = point;
    keyPointsEl.appendChild(li);
  });

  const questionsEl = document.getElementById("result-questions");
  questionsEl.innerHTML = "";
  (data.questions || []).forEach((q) => {
    const li = document.createElement("li");

    const questionText = document.createElement("div");
    questionText.textContent = q.question;
    li.appendChild(questionText);

    const revealBtn = document.createElement("button");
    revealBtn.textContent = "Show answer";
    revealBtn.className = "reveal-btn";

    const answerEl = document.createElement("div");
    answerEl.textContent = q.answer;
    answerEl.className = "answer";

    revealBtn.addEventListener("click", () => {
      answerEl.classList.toggle("shown");
      revealBtn.textContent = answerEl.classList.contains("shown") ? "Hide answer" : "Show answer";
    });

    li.appendChild(revealBtn);
    li.appendChild(answerEl);
    questionsEl.appendChild(li);
  });

  results.classList.remove("hidden");
}
