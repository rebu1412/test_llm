const sendButton = document.getElementById("send");
const questionInput = document.getElementById("question");

const leftName = document.getElementById("left-name");
const leftModel = document.getElementById("left-model");
const leftEndpoint = document.getElementById("left-endpoint");

const rightName = document.getElementById("right-name");
const rightModel = document.getElementById("right-model");
const rightEndpoint = document.getElementById("right-endpoint");

const leftAnswer = document.getElementById("left-answer");
const rightAnswer = document.getElementById("right-answer");

const leftBotName = document.getElementById("left-bot-name");
const leftModelName = document.getElementById("left-model-name");
const leftLatency = document.getElementById("left-latency");

const rightBotName = document.getElementById("right-bot-name");
const rightModelName = document.getElementById("right-model-name");
const rightLatency = document.getElementById("right-latency");

function setLoading() {
  leftAnswer.textContent = "Loading...";
  rightAnswer.textContent = "Loading...";
  leftLatency.textContent = "⏱";
  rightLatency.textContent = "⏱";
}

function setResult(result, side) {
  const targetAnswer = side === "left" ? leftAnswer : rightAnswer;
  const targetBotName = side === "left" ? leftBotName : rightBotName;
  const targetModelName = side === "left" ? leftModelName : rightModelName;
  const targetLatency = side === "left" ? leftLatency : rightLatency;

  targetBotName.textContent = result.bot_name;
  targetModelName.textContent = result.model;
  targetLatency.textContent = `⏱ ${Math.round(result.latency_ms)} ms`;

  if (result.error) {
    targetAnswer.textContent = `Error: ${result.error}`;
    targetAnswer.classList.add("error");
  } else {
    targetAnswer.textContent = result.answer.trim();
    targetAnswer.classList.remove("error");
  }
}

async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    return;
  }

  sendButton.disabled = true;
  questionInput.disabled = true;
  setLoading();

  const payload = {
    question,
    left_bot: {
      type: "vllm",
      name: leftName.value.trim(),
      endpoint: leftEndpoint.value.trim(),
      model: leftModel.value.trim(),
    },
    right_bot: {
      type: "qwen_api",
      name: rightName.value.trim(),
      endpoint: rightEndpoint.value.trim() || null,
      model: rightModel.value.trim(),
    },
  };

  try {
    const response = await fetch("http://127.0.0.1:3636/chat/compare", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "Request failed");
    }

    const data = await response.json();
    data.results.forEach((result) => setResult(result, result.side));
  } catch (error) {
    leftAnswer.textContent = "Error fetching response.";
    rightAnswer.textContent = "Error fetching response.";
    leftAnswer.classList.add("error");
    rightAnswer.classList.add("error");
    leftLatency.textContent = "⏱";
    rightLatency.textContent = "⏱";
  } finally {
    sendButton.disabled = false;
    questionInput.disabled = false;
  }
}

sendButton.addEventListener("click", sendQuestion);
questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendQuestion();
  }
});
